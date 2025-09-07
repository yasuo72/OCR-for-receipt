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

# Try to import enhanced scanner, fallback to basic functionality
try:
    from enhanced_scanner import EnhancedReceiptScanner
    scanner = EnhancedReceiptScanner()
    SCANNER_AVAILABLE = True
    logger.info("Enhanced scanner loaded successfully")
except ImportError as e:
    logger.warning(f"Enhanced scanner not available: {e}")
    scanner = None
    SCANNER_AVAILABLE = False

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

@app.route('/api/scan', methods=['POST'])
def scan_receipt():
    """Enhanced receipt scanning endpoint."""
    try:
        if not SCANNER_AVAILABLE:
            return jsonify({
                'error': 'Scanner not available',
                'message': 'Enhanced OCR scanner could not be loaded'
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
        
        # Process the receipt
        result = scanner.scan_receipt(filepath)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error processing receipt: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': 'Processing failed',
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
