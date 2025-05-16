# Receipt Scanner

A fully functional receipt scanner application that can scan any type of receipt, extract data, and store it in both a database and CSV format for machine learning model training. Now available as both a desktop application and a RESTful API.

## Features

- Scan receipts using OCR (Optical Character Recognition)
- Extract key information from receipts (date, merchant, items, prices, total, etc.)
- Store extracted data in a SQLite database
- Export data to CSV files for machine learning model training
- Simple and intuitive user interface
- RESTful API for integration with other applications

## Requirements

- Python 3.8+
- Tesseract OCR engine
- Required Python packages (see requirements.txt)

## Installation

1. Install Tesseract OCR:
   - Windows: Download and install from https://github.com/UB-Mannheim/tesseract/wiki
   - Make sure to add Tesseract to your PATH

2. Install required Python packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Desktop Application
Run the desktop application:
```
python app.py
```

### API Server
Run the API server:
```
python api.py
```

The API will be available at `http://localhost:5000`

### API Client
You can use the provided API client to interact with the API:
```
python api_client.py [path_to_receipt_image]
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check endpoint |
| `/api/scan` | POST | Scan a receipt image and extract text |
| `/api/extract` | POST | Extract structured data from receipt text |
| `/api/receipts` | GET | Get all receipts or search for receipts |
| `/api/receipts` | POST | Save a receipt to the database |
| `/api/receipts/{id}` | GET | Get a receipt by ID |
| `/api/receipts/{id}` | DELETE | Delete a receipt by ID |
| `/api/export` | GET | Export receipt data to CSV |

## Project Structure

- `app.py`: Main desktop application entry point
- `api.py`: RESTful API server
- `api_client.py`: API client for interacting with the API
- `scanner.py`: Receipt scanning and OCR functionality
- `extractor.py`: Data extraction from OCR text
- `database.py`: Database operations
- `exporter.py`: CSV export functionality
- `ui.py`: User interface components for desktop application
- `data/`: Directory for storing scanned receipts and exported data
  - `receipts/`: Scanned receipt images
  - `uploads/`: Temporary storage for API uploads
  - `exports/`: Exported CSV files
