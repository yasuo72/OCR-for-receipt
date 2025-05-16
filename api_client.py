"""
API client for the Receipt Scanner API.
"""
import os
import sys
import json
import base64
import requests
from datetime import datetime

class ReceiptScannerClient:
    def __init__(self, base_url="http://localhost:5000"):
        """Initialize the API client with the base URL."""
        self.base_url = base_url
    
    def health_check(self):
        """Check if the API is running."""
        response = requests.get(f"{self.base_url}/api/health")
        return response.json()
    
    def scan_receipt(self, image_path):
        """
        Scan a receipt image and extract text.
        
        Args:
            image_path: Path to the receipt image
            
        Returns:
            dict: API response with extracted text
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        with open(image_path, 'rb') as f:
            files = {'file': (os.path.basename(image_path), f)}
            response = requests.post(f"{self.base_url}/api/scan", files=files)
        
        return response.json()
    
    def scan_receipt_base64(self, image_path):
        """
        Scan a receipt image using base64 encoding.
        
        Args:
            image_path: Path to the receipt image
            
        Returns:
            dict: API response with extracted text
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        data = {'image_base64': image_data}
        response = requests.post(f"{self.base_url}/api/scan", data=data)
        
        return response.json()
    
    def extract_data(self, text):
        """
        Extract structured data from receipt text.
        
        Args:
            text: OCR text from receipt
            
        Returns:
            dict: API response with extracted data
        """
        data = {'text': text}
        response = requests.post(
            f"{self.base_url}/api/extract", 
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        return response.json()
    
    def save_receipt(self, receipt_data):
        """
        Save a receipt to the database.
        
        Args:
            receipt_data: Dictionary containing receipt information
            
        Returns:
            dict: API response with receipt ID
        """
        response = requests.post(
            f"{self.base_url}/api/receipts", 
            json=receipt_data,
            headers={'Content-Type': 'application/json'}
        )
        
        return response.json()
    
    def get_receipts(self, query=None):
        """
        Get all receipts or search for receipts.
        
        Args:
            query: Optional search query
            
        Returns:
            dict: API response with receipts
        """
        params = {}
        if query:
            params['query'] = query
        
        response = requests.get(f"{self.base_url}/api/receipts", params=params)
        
        return response.json()
    
    def get_receipt(self, receipt_id):
        """
        Get a receipt by ID.
        
        Args:
            receipt_id: ID of the receipt to retrieve
            
        Returns:
            dict: API response with receipt data
        """
        response = requests.get(f"{self.base_url}/api/receipts/{receipt_id}")
        
        return response.json()
    
    def delete_receipt(self, receipt_id):
        """
        Delete a receipt by ID.
        
        Args:
            receipt_id: ID of the receipt to delete
            
        Returns:
            dict: API response with success status
        """
        response = requests.delete(f"{self.base_url}/api/receipts/{receipt_id}")
        
        return response.json()
    
    def export_data(self, export_format='csv', from_date=None, to_date=None):
        """
        Export receipt data.
        
        Args:
            export_format: Format to export (csv, excel, json)
            from_date: Start date for filtering receipts (YYYY-MM-DD)
            to_date: End date for filtering receipts (YYYY-MM-DD)
            
        Returns:
            dict: API response with export information
        """
        params = {'format': export_format}
        if from_date:
            params['from_date'] = from_date
        if to_date:
            params['to_date'] = to_date
        
        response = requests.get(f"{self.base_url}/api/export", params=params)
        
        return response.json()

def main():
    """Example usage of the API client."""
    client = ReceiptScannerClient()
    
    # Check if API is running
    try:
        health = client.health_check()
        print(f"API Status: {health['status']}")
    except Exception as e:
        print(f"API is not running: {str(e)}")
        print("Make sure to start the API server first with: python api.py")
        sys.exit(1)
    
    # Example: Scan a receipt image
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        image_path = sys.argv[1]
        print(f"\nScanning receipt: {image_path}")
        
        # Scan the image
        scan_result = client.scan_receipt(image_path)
        
        if 'success' in scan_result and scan_result['success']:
            print("Scan successful!")
            print(f"Extracted text: {scan_result['text'][:100]}...")
            
            # Extract data from text
            extract_result = client.extract_data(scan_result['text'])
            
            if 'success' in extract_result and extract_result['success']:
                print("\nExtracted data:")
                data = extract_result['data']
                print(f"Merchant: {data.get('merchant')}")
                print(f"Date: {data.get('date')}")
                print(f"Total: {data.get('total')}")
                print(f"Tax: {data.get('tax')}")
                
                if data.get('items'):
                    print("\nItems:")
                    for item in data['items']:
                        print(f"- {item.get('name')}: {item.get('quantity')} x {item.get('price')}")
                
                # Save receipt to database
                save_result = client.save_receipt(data)
                if 'success' in save_result and save_result['success']:
                    print(f"\nReceipt saved with ID: {save_result['receipt_id']}")
                else:
                    print(f"\nFailed to save receipt: {save_result.get('error')}")
            else:
                print(f"\nFailed to extract data: {extract_result.get('error')}")
        else:
            print(f"\nFailed to scan receipt: {scan_result.get('error')}")
    else:
        # If no image provided, show available receipts
        print("\nNo image provided. Showing available receipts:")
        receipts_result = client.get_receipts()
        
        if 'success' in receipts_result and receipts_result['success']:
            receipts = receipts_result['receipts']
            if receipts:
                print(f"Found {len(receipts)} receipts:")
                for receipt in receipts:
                    print(f"- ID: {receipt['id']}, Merchant: {receipt['merchant']}, Date: {receipt['date']}, Total: {receipt['total']}")
            else:
                print("No receipts found in the database.")
        else:
            print(f"Failed to get receipts: {receipts_result.get('error')}")
    
    print("\nExample API usage complete!")

if __name__ == "__main__":
    main()
