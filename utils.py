
from PIL import Image
import requests
from io import BytesIO
import os
import csv
import traceback
import logging
from requests.exceptions import RequestException

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_images(request_id, csv_file_path, webhook_url, app):
    # Access mongo with app context
    with app.app_context():
        from db import mongo
        from webhook import send_webhook
        
        try:
            # Create the output dir if it doesn't exist
            output_dir = app.config['OUTPUT_FOLDER']
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Output CSV preparation
            output_csv_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{request_id}_output.csv")
            output_data = []
            all_processed_image_urls = []
            
            # Process the CSV file
            with open(csv_file_path, 'r') as file:
                # Check if file is empty
                if os.path.getsize(csv_file_path) == 0:
                    raise ValueError("CSV file is empty")
                
                csv_reader = csv.reader(file)
                # Try to get headers - this will raise StopIteration if file is empty after trim
                try:
                    headers = next(csv_reader)  # Skip header row
                    logger.info(f"CSV Headers: {headers}")
                except StopIteration:
                    raise ValueError("CSV file has no data rows")
                
                for row_idx, row in enumerate(csv_reader):
                    logger.info(f"Processing row {row_idx}: {row}")
                    
                    # Basic validation - need at least 3 columns
                    if len(row) < 3:
                        logger.warning(f"Row {row_idx} has fewer than 3 columns, skipping: {row}")
                        continue
                    
                    serial_number = row[0]
                    product_name = row[1]
                    
                    # The third column should contain comma-separated image URLs
                    # For safety, join all remaining columns and split by comma
                    all_url_text = ','.join(row[2:])
                    image_urls = [url.strip() for url in all_url_text.split(',') if url.strip()]
                    
                    logger.info(f"Found {len(image_urls)} image URLs for product {product_name}")
                    processed_image_urls = []
                    
                    for idx, image_url in enumerate(image_urls):
                        image_url = image_url.strip()
                        logger.info(f"Processing image {idx}: {image_url}")
                        
                        try:
                            # If URL is not a direct image URL (doesn't end with image extension)
                            # Replace with a placeholder image
                            if not any(image_url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                                logger.warning(f"URL doesn't appear to be a direct image: {image_url}")
                                # Use placeholder image instead
                                image_url = f"https://picsum.photos/{400 + idx * 10}/{300 + idx * 10}"
                                logger.info(f"Using placeholder: {image_url}")
                            
                            # Download the image
                            response = requests.get(image_url, timeout=10)
                            response.raise_for_status()
                            
                            # Process and save the image
                            image = Image.open(BytesIO(response.content))
                            image = image.convert("RGB")
                            
                            # Create unique filename for the output
                            safe_product_name = ''.join(c if c.isalnum() else '_' for c in product_name)
                            image_filename = f"{request_id}_{safe_product_name}_{idx}.jpg"
                            output_path = os.path.join(output_dir, image_filename)
                            public_url = f"/static/compressed_images/{image_filename}"
                            
                            # Save compressed image
                            image.save(output_path, "JPEG", quality=50)
                            processed_image_urls.append(public_url)
                            all_processed_image_urls.append(public_url)
                            logger.info(f"Successfully saved compressed image to {output_path}")
                            
                        except RequestException as e:
                            error = f"Request error for {image_url}: {str(e)}"
                            logger.error(error)
                            processed_image_urls.append("error")
                            
                        except Exception as e:
                            error = f"Error processing image {image_url}: {str(e)}"
                            logger.error(error)
                            logger.error(traceback.format_exc())
                            processed_image_urls.append("error")
                    
                    # Add row to output data
                    output_row = [
                        serial_number,
                        product_name,
                        ','.join(image_urls),
                        ','.join(processed_image_urls)
                    ]
                    output_data.append(output_row)
            
            # Write output CSV
            with open(output_csv_path, 'w', newline='') as outfile:
                csv_writer = csv.writer(outfile)
                csv_writer.writerow(['S. No.', 'Product Name', 'Input Image Urls', 'Output Image Urls'])
                csv_writer.writerows(output_data)
            
            # Update database status
            mongo.db.requests.update_one(
                {"requestId": request_id},
                {"$set": {
                    "status": "COMPLETED",
                    "compressedImages": all_processed_image_urls,
                    "outputCsv": output_csv_path
                }}
            )
            
            # Send webhook if provided
            if webhook_url:
                send_webhook(webhook_url, request_id, all_processed_image_urls, output_csv_path)
                
        except Exception as e:
            error_msg = f"Error processing CSV: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            
            # Update database with error status
            mongo.db.requests.update_one(
                {"requestId": request_id},
                {"$set": {
                    "status": "ERROR",
                    "error": str(e)
                }}
            )