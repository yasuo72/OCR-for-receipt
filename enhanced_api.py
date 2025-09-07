"""
Enhanced API for receipt scanning with improved OCR and data extraction.
"""
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
import logging
from enhanced_scanner import EnhancedReceiptScanner
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize the enhanced scanner
scanner = EnhancedReceiptScanner()

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/scan', methods=['POST'])
def scan_receipt():
    """
    Enhanced receipt scanning endpoint.
    
    Accepts image file and returns structured receipt data.
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed: PNG, JPG, JPEG, GIF, BMP, TIFF, WEBP'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join('data/uploads', filename)
        
        os.makedirs('data/uploads', exist_ok=True)
        file.save(filepath)
        
        logger.info(f"Processing file: {filepath}")
        
        # Scan the receipt using enhanced scanner
        extracted_data = scanner.scan_receipt(filepath, save_processed=True)
        
        # Convert to dictionary for JSON response
        result = {
            'success': True,
            'data': {
                'merchant': extracted_data.merchant,
                'date': extracted_data.date,
                'total': extracted_data.total,
                'subtotal': extracted_data.subtotal,
                'tax': extracted_data.tax,
                'items': extracted_data.items or [],
                'payment_method': extracted_data.payment_method,
                'receipt_number': extracted_data.receipt_number,
                'confidence_score': extracted_data.confidence_score,
                'raw_text': extracted_data.raw_text
            },
            'metadata': {
                'filename': filename,
                'processed_at': datetime.now().isoformat(),
                'file_size': os.path.getsize(filepath)
            }
        }
        
        # Save result to database/file for tracking
        result_file = os.path.join('data/results', f"{timestamp}_result.json")
        os.makedirs('data/results', exist_ok=True)
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Scan completed successfully. Confidence: {extracted_data.confidence_score:.2f}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing receipt: {str(e)}")
        logger.error(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to process receipt. Please try again with a clearer image.'
        }), 500

@app.route('/api/scan/batch', methods=['POST'])
def scan_receipts_batch():
    """
    Batch receipt scanning endpoint.
    
    Accepts multiple image files and returns structured data for each.
    """
    try:
        files = request.files.getlist('files')
        
        if not files:
            return jsonify({'error': 'No files provided'}), 400
        
        results = []
        
        for file in files:
            if file.filename == '' or not allowed_file(file.filename):
                continue
            
            try:
                # Save and process each file
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join('data/uploads', filename)
                
                file.save(filepath)
                
                # Scan the receipt
                extracted_data = scanner.scan_receipt(filepath, save_processed=False)
                
                results.append({
                    'filename': file.filename,
                    'success': True,
                    'data': {
                        'merchant': extracted_data.merchant,
                        'date': extracted_data.date,
                        'total': extracted_data.total,
                        'subtotal': extracted_data.subtotal,
                        'tax': extracted_data.tax,
                        'items': extracted_data.items or [],
                        'payment_method': extracted_data.payment_method,
                        'receipt_number': extracted_data.receipt_number,
                        'confidence_score': extracted_data.confidence_score
                    }
                })
                
            except Exception as e:
                results.append({
                    'filename': file.filename,
                    'success': False,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'results': results,
            'processed_count': len(results)
        })
        
    except Exception as e:
        logger.error(f"Error in batch processing: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/test', methods=['GET'])
def test_with_sample():
    """
    Test endpoint using sample bill images.
    """
    try:
        sample_dir = 'assets/bill_img'
        if not os.path.exists(sample_dir):
            return jsonify({'error': 'Sample images directory not found'}), 404
        
        sample_files = [f for f in os.listdir(sample_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if not sample_files:
            return jsonify({'error': 'No sample images found'}), 404
        
        results = []
        
        for sample_file in sample_files[:3]:  # Test first 3 samples
            try:
                filepath = os.path.join(sample_dir, sample_file)
                logger.info(f"Testing with sample: {sample_file}")
                
                extracted_data = scanner.scan_receipt(filepath, save_processed=True)
                
                results.append({
                    'sample_file': sample_file,
                    'success': True,
                    'data': {
                        'merchant': extracted_data.merchant,
                        'date': extracted_data.date,
                        'total': extracted_data.total,
                        'subtotal': extracted_data.subtotal,
                        'tax': extracted_data.tax,
                        'items': extracted_data.items or [],
                        'confidence_score': extracted_data.confidence_score
                    }
                })
                
            except Exception as e:
                results.append({
                    'sample_file': sample_file,
                    'success': False,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'message': 'Sample testing completed',
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error in sample testing: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'scanner_ready': True,
        'easyocr_available': scanner.easyocr_available
    })

@app.route('/api/processed/<filename>', methods=['GET'])
def get_processed_image(filename):
    """Get processed image for debugging."""
    try:
        filepath = os.path.join('data/processed', filename)
        if os.path.exists(filepath):
            return send_file(filepath)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('data/uploads', exist_ok=True)
    os.makedirs('data/processed', exist_ok=True)
    os.makedirs('data/results', exist_ok=True)
    
    # Get port from environment variable for Railway deployment
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    # Run the app
    app.run(host='0.0.0.0', port=port, debug=debug)
