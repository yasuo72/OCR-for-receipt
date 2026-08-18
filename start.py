#!/usr/bin/env python3
"""
Direct Django server startup for local and cloud deployment (Railway, Render, Heroku).
Automatically runs migrations and starts the Django development/production server.
"""
import os
import sys

def main():
    """Start the Django app directly with migrations"""
    print("Starting FinSathi OCR Receipt Scanner Django Server...")
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'receipt_scanner_project.settings')
    os.environ['PYTHONUNBUFFERED'] = '1'
    
    # Create required data directories
    os.makedirs('data/uploads', exist_ok=True)
    os.makedirs('data/processed', exist_ok=True)
    os.makedirs('data/results', exist_ok=True)
    os.makedirs('data/receipts', exist_ok=True)
    
    try:
        from django.core.management import execute_from_command_line
        
        # 1. Run migrations
        print("Running database migrations...")
        execute_from_command_line(['manage.py', 'migrate', '--noinput'])
        
        # 2. Get port and launch server
        port = os.environ.get('PORT', '8080')
        bind_address = f"0.0.0.0:{port}"
        print(f"Server starting on http://{bind_address}")
        
        execute_from_command_line(['manage.py', 'runserver', bind_address, '--noreload'])
        
    except Exception as e:
        print(f"Error starting Django app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
