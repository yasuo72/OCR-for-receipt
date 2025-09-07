#!/usr/bin/env python3
"""
OCR Receipt Scanner API - Railway Deployment
"""
import os
import sys
import logging
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import json
from datetime import datetime
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Try to import enhanced scanner, fallback to basic OCR
try:
    from enhanced_scanner import EnhancedReceiptScanner
    scanner = EnhancedReceiptScanner()
    SCANNER_AVAILABLE = True
    logger.info("Enhanced scanner loaded successfully")
except ImportError as e:
    logger.warning(f"Enhanced scanner not available: {e}")
    # Fallback to basic pytesseract OCR
    try:
        import pytesseract
        from PIL import Image
        import cv2
        scanner = None
        SCANNER_AVAILABLE = "basic"
        logger.info("Basic OCR available (pytesseract)")
    except ImportError:
        scanner = None
        SCANNER_AVAILABLE = False
        logger.warning("No OCR capabilities available")

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'message': 'OCR Receipt Scanner API is running',
        'scanner_available': SCANNER_AVAILABLE,
        'timestamp': datetime.now().isoformat()
    })

def basic_ocr_scan(filepath):
    """Basic OCR scanning using pytesseract with enhanced preprocessing."""
    import pytesseract
    from PIL import Image
    import cv2
    import numpy as np
    import re
    from datetime import datetime
    
    try:
        # Read and preprocess image
        img = cv2.imread(filepath)
        if img is None:
            raise ValueError("Could not read image file")
            
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply image enhancement
        # Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply threshold to get better contrast
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Extract text using pytesseract
        text = pytesseract.image_to_string(thresh, config='--psm 6')
        
        # Basic text processing and extraction
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Try to extract basic receipt information
        receipt_data = {
            'raw_text': text.strip(),
            'lines': lines,
            'method': 'basic_pytesseract',
            'status': 'processed'
        }
        
        # Try to find total amount (basic pattern matching)
        total_patterns = [
            r'total[:\s]*\$?(\d+\.?\d*)',
            r'amount[:\s]*\$?(\d+\.?\d*)',
            r'\$(\d+\.\d{2})',
            r'(\d+\.\d{2})'
        ]
        
        for pattern in total_patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                try:
                    receipt_data['total'] = float(matches[-1])  # Take the last/largest amount
                    break
                except ValueError:
                    continue
        
        # Try to find date
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                receipt_data['date'] = matches[0]
                break
        
        return receipt_data
        
    except Exception as e:
        logger.error(f"OCR processing error: {str(e)}")
        return {
            'error': str(e),
            'method': 'basic_pytesseract',
            'status': 'failed',
            'raw_text': ''
        }

@app.route('/api/scan', methods=['POST'])
def scan_receipt():
    """Receipt scanning endpoint with fallback."""
    try:
        if SCANNER_AVAILABLE == False:
            return jsonify({
                'error': 'Scanner not available',
                'message': 'No OCR capabilities loaded'
            }), 503
            
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
            
        # Create directories
        os.makedirs('data/uploads', exist_ok=True)
        os.makedirs('data/processed', exist_ok=True)
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join('data/uploads', filename)
        file.save(filepath)
        
        logger.info(f"Processing receipt: {filename}")
        
        # Process the receipt
        if SCANNER_AVAILABLE == True:
            result = scanner.scan_receipt(filepath)
        else:  # basic OCR
            result = basic_ocr_scan(filepath)
        
        logger.info(f"OCR result: {result}")
        
        # Format response for Flutter app compatibility
        response_data = {
            'success': True,
            'filename': filename,
            'scanner_type': SCANNER_AVAILABLE,
            'timestamp': datetime.now().isoformat(),
            'message': 'Receipt processed successfully'
        }
        
        # Add OCR results in expected format
        if 'error' in result:
            response_data['success'] = False
            response_data['error'] = result['error']
        else:
            response_data['receipt'] = {
                'text': result.get('raw_text', ''),
                'total': result.get('total', 0.0),
                'date': result.get('date', ''),
                'items': result.get('lines', []),
                'confidence': result.get('confidence', 'basic'),
                'method': result.get('method', 'basic_pytesseract')
            }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error processing receipt: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Processing failed',
            'message': str(e)
        }), 500

@app.route('/api/receipts', methods=['GET'])
def get_receipts():
    """Get list of processed receipts."""
    try:
        receipts_dir = 'data/uploads'
        if not os.path.exists(receipts_dir):
            return jsonify({'receipts': []})
            
        receipts = []
        for filename in os.listdir(receipts_dir):
            if allowed_file(filename):
                filepath = os.path.join(receipts_dir, filename)
                stat = os.stat(filepath)
                receipts.append({
                    'filename': filename,
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        return jsonify({
            'success': True,
            'receipts': receipts,
            'count': len(receipts)
        })
        
    except Exception as e:
        logger.error(f"Error getting receipts: {str(e)}")
        return jsonify({
            'error': 'Failed to get receipts',
            'message': str(e)
        }), 500

@app.route('/api/info')
def api_info():
    """API information endpoint."""
    return jsonify({
        'name': 'OCR Receipt Scanner API',
        'version': '2.0',
        'scanner_available': SCANNER_AVAILABLE,
        'endpoints': {
            'health': '/api/health',
            'scan': '/api/scan (POST)',
            'receipts': '/api/receipts (GET)',
            'info': '/api/info'
        }
    })

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413

if __name__ == "__main__":
    # Create necessary directories
    os.makedirs('data/uploads', exist_ok=True)
    os.makedirs('data/processed', exist_ok=True)
    os.makedirs('data/results', exist_ok=True)
    
    # Get port from environment variable for Railway deployment
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    logger.info(f"Starting OCR API server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
