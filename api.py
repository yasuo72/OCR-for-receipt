"""
API for the Receipt Scanner application.
"""
import os
import base64
import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

from scanner import ReceiptScanner
from extractor import ReceiptExtractor
from database_pg import ReceiptDatabase
from exporter import ReceiptExporter

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure upload folder
UPLOAD_FOLDER = 'data/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Initialize components
tesseract_path = None
if os.name == 'nt':  # Windows
    # Common installation paths for Tesseract on Windows
    possible_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    ]
    for path in possible_paths:
        if os.path.exists(path):
            tesseract_path = path
            break

# Optional database: only connect if DATABASE_URL is provided in the environment


scanner = ReceiptScanner(tesseract_path)
extractor = ReceiptExtractor()

class _NoDatabase:
    def __getattr__(self, name):
        def _unavailable(*args, **kwargs):
            raise RuntimeError("Database is not configured")
        return _unavailable

try:
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        database = ReceiptDatabase(db_url)
    else:
        print("[OCR] Warning: DATABASE_URL not set – database functions disabled")
        database = _NoDatabase()
except Exception as e:
    print(f"[OCR] Warning: could not connect to database: {e} – database functions disabled")
    database = _NoDatabase()
exporter = ReceiptExporter()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/scan', methods=['POST'])
def scan_receipt():
    """
    Scan a receipt image and extract text using OCR.
    
    Accepts either a file upload or a base64 encoded image.
    """
    try:
        image_path = None
        
        # Check if the request has a file
        if 'file' in request.files:
            file = request.files['file']
            if file.filename:
                filename = secure_filename(file.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(image_path)
        
        # Check if the request has base64 encoded image
        elif 'image_base64' in request.form:
            image_data = request.form['image_base64']
            # Remove data URL prefix if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            # Decode base64 image
            image_bytes = base64.b64decode(image_data)
            
            # Save to a temporary file
            timestamp = int(datetime.now().timestamp())
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], f'receipt_{timestamp}.jpg')
            with open(image_path, 'wb') as f:
                f.write(image_bytes)
        
        else:
            return jsonify({
                'error': 'No image provided. Please upload a file or provide a base64 encoded image.'
            }), 400
        
        # Scan the image
        text = scanner.scan_image(image_path)
        
        # Return the extracted text
        return jsonify({
            'success': True,
            'text': text,
            'image_path': image_path
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/extract', methods=['POST'])
def extract_data():
    """
    Extract structured data from receipt text.
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                'error': 'No text provided. Please provide OCR text in the request body.'
            }), 400
        
        # Extract data from text
        receipt_data = extractor.extract_data(data['text'])
        
        # Return the extracted data
        return jsonify({
            'success': True,
            'data': receipt_data
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/receipts', methods=['POST'])
def save_receipt():
    """
    Save a receipt to the database.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No data provided.'
            }), 400
        
        # Required fields
        required_fields = ['merchant', 'date', 'total']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Prepare receipt data
        receipt_data = {
            'merchant': data['merchant'],
            'date': data['date'],
            'total': float(data['total']) if data['total'] else None,
            'tax': float(data['tax']) if 'tax' in data and data['tax'] else None,
            'receipt_path': data.get('receipt_path', None),
            'raw_text': data.get('raw_text', '')
        }
        
        # Prepare items data
        items_data = []
        for item in data.get('items', []):
            items_data.append({
                'name': item.get('name', ''),
                'quantity': float(item.get('quantity', 1)),
                'price': float(item.get('price', 0))
            })
        
        # Save to database
        receipt_id = database.add_receipt(receipt_data, items_data)
        
        # Return the receipt ID
        return jsonify({
            'success': True,
            'receipt_id': receipt_id
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/receipts', methods=['GET'])
def get_receipts():
    """
    Get all receipts or search for receipts.
    """
    try:
        # Check for search query
        query = request.args.get('query', '')
        
        if query:
            # Search for receipts
            receipts = database.search_receipts(query)
        else:
            # Get all receipts
            receipts = database.get_all_receipts()
        
        # Return the receipts
        return jsonify({
            'success': True,
            'receipts': receipts
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/receipts/<int:receipt_id>', methods=['GET'])
def get_receipt(receipt_id):
    """
    Get a receipt by ID.
    """
    try:
        # Get receipt from database
        receipt = database.get_receipt(receipt_id)
        
        if not receipt:
            return jsonify({
                'error': f'Receipt with ID {receipt_id} not found.'
            }), 404
        
        # Return the receipt
        return jsonify({
            'success': True,
            'receipt': receipt
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/receipts/<int:receipt_id>', methods=['DELETE'])
def delete_receipt(receipt_id):
    """
    Delete a receipt by ID.
    """
    try:
        # Delete receipt from database
        success = database.delete_receipt(receipt_id)
        
        if not success:
            return jsonify({
                'error': f'Failed to delete receipt with ID {receipt_id}.'
            }), 500
        
        # Return success
        return jsonify({
            'success': True,
            'message': f'Receipt with ID {receipt_id} deleted successfully.'
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/export', methods=['GET'])
def export_data():
    """
    Export receipt data to CSV.
    """
    try:
        # Get export parameters
        export_format = request.args.get('format', 'csv')
        from_date = request.args.get('from_date', None)
        to_date = request.args.get('to_date', None)
        
        # Get all receipts (in a real implementation, we would filter by date)
        receipts = database.get_all_receipts()
        
        # Add items to receipts
        for receipt in receipts:
            receipt_with_items = database.get_receipt(receipt['id'])
            receipt['items'] = receipt_with_items.get('items', [])
        
        # Export based on format
        if export_format.lower() == 'csv':
            receipts_path = exporter.export_to_csv(receipts)
            items_path = exporter.export_items_to_csv(receipts)
            
            return jsonify({
                'success': True,
                'message': f'Exported {len(receipts)} receipts to CSV.',
                'files': {
                    'receipts': receipts_path,
                    'items': items_path
                }
            })
        else:
            return jsonify({
                'error': f'Unsupported export format: {export_format}'
            }), 400
    
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

# Run the app
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
