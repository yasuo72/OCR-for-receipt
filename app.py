#!/usr/bin/env python3
"""
Simple Flask app entry point for Railway deployment
"""
import os
import sys
from flask import Flask, jsonify

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import the enhanced API
try:
    from enhanced_api import app as enhanced_app
    app = enhanced_app
except ImportError as e:
    print(f"Import error: {e}")
    # Fallback simple app
    app = Flask(__name__)
    
    @app.route('/api/health')
    def health():
        return jsonify({'status': 'ok', 'message': 'Fallback app running'})

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
