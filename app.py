from flask import Flask, request, jsonify, send_from_directory
import os
import uuid
import logging
from werkzeug.utils import secure_filename
import threading

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'static/compressed_images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MONGO_URI'] = "mongodb://localhost:27017/image_compression_db"

# Create necessary directories
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)
        # logger.info(f"Created directory: {folder}")

logger.info("Flask app initialized")

# Import after Flask app is created to avoid circular imports
from db import mongo
from utils import process_images
from webhook import send_webhook

# Initialize MongoDB
mongo.init_app(app)
logger.info("MongoDB initialized")

@app.route('/upload', methods=['POST'])
def upload_csv():
    logger.info("Upload endpoint hit!")
    # logger.info(f"Files in request: {request.files}")
    
    if 'file' not in request.files:
        # logger.warning("No file part in request")
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    webhook_url = request.form.get('webhookUrl')
    # logger.info(f"Webhook URL: {webhook_url}")

    if file.filename == '':
        # logger.warning("Empty filename")
        return jsonify({"error": "No file selected"}), 400

    # Allow both CSV and any file (for testing)
    if file:
        filename = secure_filename(file.filename)
        request_id = str(uuid.uuid4())
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        # logger.info(f"File saved to {file_path}")
        
        # Store initial status in database
        mongo.db.requests.insert_one({
            "requestId": request_id,
            "status": "PROCESSING",
            "compressedImages": []
        })
        # logger.info(f"Created request with ID: {request_id}")
        
        # Start image processing in a separate thread
        thread = threading.Thread(
            target=process_images,
            args=(request_id, file_path, webhook_url, app)
        )
        thread.daemon = True
        thread.start()
        # logger.info(f"Started processing thread for request: {request_id}")

        return jsonify({
            "requestId": request_id,
            "message": "File Uploaded Successfully, Processing Started"
        })
    
    # logger.warning("Unknown error in file upload")
    return jsonify({"error": "Invalid file format or upload failed"}), 400

@app.route('/status/<request_id>', methods=['GET'])
def check_status(request_id):
    # logger.info(f"Status endpoint hit for {request_id}")
    data = mongo.db.requests.find_one({"requestId": request_id})
    if data:
        # logger.info(f"Found request: {data['status']}")
        return jsonify({
            "requestId": data['requestId'],
            "status": data['status'],
            "compressedImages": data.get('compressedImages', []),
            "error": data.get('error', None)
        })
    # logger.warning(f"Request ID not found: {request_id}")
    return jsonify({"error": "Invalid Request ID"}), 404

@app.route('/static/compressed_images/<filename>')
def serve_image(filename):
    """Serve compressed images directly"""
    return send_from_directory(OUTPUT_FOLDER, filename)

@app.route('/webhook', methods=['POST'])
def webhook():
    logger.info("Webhook endpoint hit!")
    data = request.json
    # logger.info(f"Webhook data: {data}")
    return jsonify({"message": "Webhook Received"}), 200


if __name__ == '__main__':
    logger.info("Starting Flask server...")
    # Print all registered routes
    for rule in app.url_map.iter_rules():
        logger.info(f"{rule.endpoint}: {rule.methods} {rule}")
    app.run(debug=True, port=5000)