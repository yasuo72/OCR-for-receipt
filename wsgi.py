#!/usr/bin/env python3
"""
WSGI entry point for Railway deployment
"""
import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from enhanced_api import app

# For gunicorn
application = app

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
