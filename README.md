# Receipt Scanner

A fully functional receipt scanner application that can scan any type of receipt, extract data, and store it in both a database and CSV format for machine learning model training.

## Features

- Scan receipts using OCR (Optical Character Recognition)
- Extract key information from receipts (date, merchant, items, prices, total, etc.)
- Store extracted data in a SQLite database
- Export data to CSV files for machine learning model training
- Simple and intuitive user interface

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

Run the application:
```
python app.py
```

## Project Structure

- `app.py`: Main application entry point
- `scanner.py`: Receipt scanning and OCR functionality
- `extractor.py`: Data extraction from OCR text
- `database.py`: Database operations
- `exporter.py`: CSV export functionality
- `ui.py`: User interface components
- `models/`: Database models
- `data/`: Directory for storing scanned receipts and exported data
- `utils/`: Utility functions
