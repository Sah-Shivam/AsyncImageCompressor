import requests

def send_webhook(url, request_id, images, output_csv=None):
    data = {
        "requestId": request_id,
        "status": "COMPLETED",
        "compressedImages": images
    }
    
    if output_csv:
        data["outputCsv"] = output_csv
        
    try:
        response = requests.post(url, json=data)
        print(f"Webhook sent to {url}. Response: {response.status_code}")
        return response.status_code
    except Exception as e:
        print(f"Error sending webhook: {str(e)}")
        return None