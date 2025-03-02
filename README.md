# 📸 Async Image Compression System

## 🔥 Project Overview
The **Async Image Compression System** is a backend service that automates bulk image compression from CSV files. It processes image URLs asynchronously, compresses them by 50%, stores the results in MongoDB 🗂️, and notifies clients via webhook 🚀.

## 📌 Features
- ✅ Asynchronous Image Processing with Celery
- 🔐 MongoDB NoSQL Database
- 🌐 Webhook Notifications
- 📄 CSV Upload with Validation
- 🔥 Cloud Storage Integration

## 🏗️ System Architecture
### System Flow
1. 📄 CSV Upload via `/upload`
2. 🔍 CSV Validation
3. 🎯 Request ID Generation
4. 🔄 Async Image Compression
5. 📤 Cloud Storage Upload
6. 🗂️ MongoDB Data Storage
7. 🚨 Webhook Callback
8. 🔎 Status Tracking via `/status/{request_id}`

## 🔑 API Endpoints

### 1. Upload CSV API
- **Endpoint:** `/upload`
- **Method:** `POST`
- **Description:** Accepts CSV file and validates input.
- **Response:**
```json
{
  "request_id": "unique_id",
  "message": "File Accepted, Processing Started"
}
```

### 2. Check Status API
- **Endpoint:** `/status/{request_id}`
- **Method:** `GET`
- **Description:** Track image processing status.
- **Response:**
```json
{
  "request_id": "unique_id",
  "status": "Completed",
  "output_csv_url": "https://cloud-storage-url/output.csv"
}
```

## 🗂️ Database Schema
### MongoDB Collections
#### `requests`
| Field        | Type    | Description         |
|-------------|--------|------------------|
| request_id   | String | Unique request ID |
| status       | String | Pending, Completed, Failed |
| input_csv_url | String | Uploaded CSV URL |
| output_csv_url | String | Processed CSV URL |
| webhook_url   | String | Client Webhook Endpoint |

#### `images`
| Field         | Type    | Description       |
|--------------|--------|---------------|
| request_id   | String | Foreign Key to `requests` |
| product_name | String | Product Name |
| input_image_urls | List   | Original Image URLs |
| output_image_urls | List   | Compressed Image URLs |

## 🎯 Technologies Used
- 🐍 Python 3.13.1
- 🚀 Flask
- 🗂️ MongoDB
- 🔄 Celery
- ☁️ Cloudinary
- 🌐 Webhooks
- 🔥 Postman
- 🖼️ Draw.io

## ⚙️ How to Run
1. Clone the Repository
```bash
git clone https://github.com/YourUsername/AsyncImageCompressor.git
cd AsyncImageCompressor
```
2. Install Dependencies
```bash
pip install -r requirements.txt
```
3. Run the Application
```bash
python app.py
```

## 📩 Webhook Callback
- The system automatically triggers the webhook URL after image compression is completed.

## 🎯 Conclusion
The **Async Image Compression System** provides an efficient solution to handle bulk image compression from CSV files. It ensures high performance ⚡, scalability 🔥, and reliability 🔑 through asynchronous workers and webhook notifications.

---

🚀 Developed with ❤️ by **Shiva**

