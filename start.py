#!/usr/bin/env python3
"""
Direct Python server startup - bypasses all gunicorn issues
"""
import os
import sys
import subprocess

def main():
    """Start the Flask app directly"""
    print("Starting OCR Receipt Scanner API...")
    print("Bypassing gunicorn completely...")
    
    # Set environment variables
    os.environ['FLASK_ENV'] = 'production'
    os.environ['PYTHONUNBUFFERED'] = '1'
    
    # Import and run the app
    try:
        from app import app
        port = int(os.environ.get('PORT', 8080))
        print(f"Starting server on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        print(f"Error starting app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
