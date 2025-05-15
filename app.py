"""
Main entry point for the Receipt Scanner application.
"""
import sys
import os
from PyQt5.QtWidgets import QApplication

from scanner import ReceiptScanner
from extractor import ReceiptExtractor
from database import ReceiptDatabase
from exporter import ReceiptExporter
from ui import ReceiptScannerUI

def main():
    """Main function to start the application."""
    # Check if Tesseract is installed and set path if needed
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
    
    # Initialize components
    scanner = ReceiptScanner(tesseract_path)
    extractor = ReceiptExtractor()
    database = ReceiptDatabase()
    exporter = ReceiptExporter()
    
    # Create application
    app = QApplication(sys.argv)
    
    # Create and show UI
    ui = ReceiptScannerUI(scanner, extractor, database, exporter)
    ui.show()
    
    # Run application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
