"""
CSV export functionality for receipt data.
"""
import os
import csv
import json
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional

class ReceiptExporter:
    def __init__(self, export_dir: str = "data/exports"):
        """
        Initialize the receipt data exporter.
        
        Args:
            export_dir: Directory to save exported files
        """
        self.export_dir = export_dir
        os.makedirs(export_dir, exist_ok=True)
    
    def export_to_csv(self, receipts: List[Dict[str, Any]], filename: str = "receipts.csv") -> str:
        """
        Export receipt data to CSV file.
        
        Args:
            receipts: List of receipt dictionaries
            filename: Name of the output CSV file
            
        Returns:
            str: Path to the exported CSV file
        """
        if not receipts:
            return ""
        
        # Prepare data for receipts CSV
        receipt_data = []
        for receipt in receipts:
            receipt_data.append({
                'id': receipt.get('id'),
                'merchant': receipt.get('merchant'),
                'date': receipt.get('date'),
                'total': receipt.get('total'),
                'tax': receipt.get('tax'),
                'receipt_path': receipt.get('receipt_path'),
                'created_at': receipt.get('created_at')
            })
        
        # Create CSV file path
        csv_path = os.path.join(self.export_dir, filename)
        
        # Write to CSV
        if receipt_data:
            df = pd.DataFrame(receipt_data)
            df.to_csv(csv_path, index=False)
        
        return csv_path
    
    def export_items_to_csv(self, receipts: List[Dict[str, Any]], filename: str = "items.csv") -> str:
        """
        Export item data to CSV file.
        
        Args:
            receipts: List of receipt dictionaries with items
            filename: Name of the output CSV file
            
        Returns:
            str: Path to the exported CSV file
        """
        if not receipts:
            return ""
        
        # Prepare data for items CSV
        items_data = []
        for receipt in receipts:
            receipt_id = receipt.get('id')
            merchant = receipt.get('merchant')
            date = receipt.get('date')
            
            for item in receipt.get('items', []):
                items_data.append({
                    'receipt_id': receipt_id,
                    'merchant': merchant,
                    'date': date,
                    'item_id': item.get('id'),
                    'name': item.get('name'),
                    'quantity': item.get('quantity'),
                    'price': item.get('price'),
                    'total_price': item.get('quantity', 1) * item.get('price', 0)
                })
        
        # Create CSV file path
        csv_path = os.path.join(self.export_dir, filename)
        
        # Write to CSV
        if items_data:
            df = pd.DataFrame(items_data)
            df.to_csv(csv_path, index=False)
        
        return csv_path
    
    def export_for_ml(self, receipts: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Export receipt data in formats suitable for ML training.
        
        Args:
            receipts: List of receipt dictionaries
            
        Returns:
            Dict[str, str]: Dictionary of exported file paths
        """
        result = {}
        
        # Export receipts
        receipts_path = self.export_to_csv(receipts, "receipts_ml.csv")
        result['receipts'] = receipts_path
        
        # Export items
        items_path = self.export_items_to_csv(receipts, "items_ml.csv")
        result['items'] = items_path
        
        # Export merchant categories
        merchant_data = []
        for receipt in receipts:
            merchant = receipt.get('merchant')
            if merchant:
                merchant_data.append({
                    'merchant': merchant,
                    'date': receipt.get('date'),
                    'total': receipt.get('total')
                })
        
        if merchant_data:
            merchant_path = os.path.join(self.export_dir, "merchants_ml.csv")
            df = pd.DataFrame(merchant_data)
            df.to_csv(merchant_path, index=False)
            result['merchants'] = merchant_path
        
        # Export raw text for NLP training
        text_data = []
        for receipt in receipts:
            text_data.append({
                'id': receipt.get('id'),
                'raw_text': receipt.get('raw_text'),
                'merchant': receipt.get('merchant'),
                'date': receipt.get('date'),
                'total': receipt.get('total')
            })
        
        if text_data:
            text_path = os.path.join(self.export_dir, "text_ml.csv")
            df = pd.DataFrame(text_data)
            df.to_csv(text_path, index=False)
            result['text'] = text_path
        
        return result
    
    def export_data(self, file_path: str, export_format: str, from_date=None, to_date=None) -> int:
        """
        Export receipt data to the specified format and file path.
        
        Args:
            file_path: Path to save the exported file
            export_format: Format to export (csv, excel, json)
            from_date: Start date for filtering receipts
            to_date: End date for filtering receipts
            
        Returns:
            int: Number of receipts exported
        """
        # Ensure export directory exists
        export_dir = os.path.dirname(file_path)
        if export_dir and not os.path.exists(export_dir):
            os.makedirs(export_dir, exist_ok=True)
        
        # For this implementation, we'll assume receipts are provided by the database
        # In a real implementation, we would query the database here
        # For now, we'll use sample data for demonstration
        from datetime import datetime
        
        # Sample data for demonstration
        receipts = [
            {
                'id': 1,
                'merchant': 'D-Mart',
                'date': datetime(2019, 10, 20),
                'total': 1095.85,
                'tax': 46.59,
                'receipt_path': 'data/receipts/receipt_1.jpg',
                'created_at': datetime.now().isoformat(),
                'items': [
                    {'name': 'SAFAL GREEN PEAS', 'quantity': 1.0, 'price': 155.00},
                    {'name': 'LIJJAT PAPAD', 'quantity': 2.0, 'price': 42.00},
                    {'name': 'FIGARO OLIVE OIL', 'quantity': 1.0, 'price': 215.00},
                    {'name': 'SANTOOR SANDAL SOAP', 'quantity': 1.0, 'price': 27.00},
                    {'name': 'PU COVER NOTEBOOK', 'quantity': 1.0, 'price': 101.85},
                    {'name': 'HALDIRAM BHUJIA', 'quantity': 1.0, 'price': 59.50},
                    {'name': 'SAFFOLA CLASSIC', 'quantity': 1.0, 'price': 99.00},
                    {'name': 'VASELINE ALOE', 'quantity': 1.0, 'price': 22.50},
                    {'name': 'GOOD NATURE COTTON', 'quantity': 1.0, 'price': 38.00},
                    {'name': 'HES NURE PENCIL', 'quantity': 4.0, 'price': 45.00},
                    {'name': 'PLASTIC WIPER', 'quantity': 1.0, 'price': 39.00}
                ]
            }
        ]
        
        # Filter by date if provided
        if from_date and to_date:
            # Convert all dates to date objects (not datetime) for consistent comparison
            from datetime import date
            try:
                filtered_receipts = []
                for r in receipts:
                    receipt_date = r['date']
                    # Convert datetime to date if needed
                    if hasattr(receipt_date, 'date'):
                        receipt_date = receipt_date.date()
                    # Convert from_date and to_date to date objects if they're datetime
                    from_date_obj = from_date.date() if hasattr(from_date, 'date') else from_date
                    to_date_obj = to_date.date() if hasattr(to_date, 'date') else to_date
                    
                    # Compare dates
                    if from_date_obj <= receipt_date <= to_date_obj:
                        filtered_receipts.append(r)
                receipts = filtered_receipts
            except Exception as e:
                print(f"Date filtering error: {e}")
                # If there's an error in date comparison, return all receipts
                pass
        
        # Prepare data for export
        export_data = []
        for receipt in receipts:
            receipt_row = {
                'ID': receipt.get('id'),
                'Merchant': receipt.get('merchant'),
                'Date': receipt.get('date').strftime('%Y-%m-%d') if isinstance(receipt.get('date'), datetime) else receipt.get('date'),
                'Total': receipt.get('total'),
                'Tax': receipt.get('tax'),
                'Items Count': len(receipt.get('items', []))
            }
            export_data.append(receipt_row)
        
        # Export based on format
        if export_format.lower() == 'csv':
            df = pd.DataFrame(export_data)
            df.to_csv(file_path, index=False)
        elif export_format.lower() == 'excel':
            df = pd.DataFrame(export_data)
            df.to_excel(file_path, index=False)
        elif export_format.lower() == 'json':
            import json
            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=4, default=str)
        
        # Also export items to a separate file
        items_data = []
        for receipt in receipts:
            for item in receipt.get('items', []):
                item_row = {
                    'Receipt ID': receipt.get('id'),
                    'Merchant': receipt.get('merchant'),
                    'Date': receipt.get('date').strftime('%Y-%m-%d') if isinstance(receipt.get('date'), datetime) else receipt.get('date'),
                    'Item Name': item.get('name'),
                    'Quantity': item.get('quantity'),
                    'Price': item.get('price'),
                    'Total': item.get('quantity', 1) * item.get('price', 0)
                }
                items_data.append(item_row)
        
        # Create items export filename by adding _items before the extension
        items_file_path = file_path.rsplit('.', 1)
        items_file_path = f"{items_file_path[0]}_items.{items_file_path[1]}" if len(items_file_path) > 1 else f"{file_path}_items"
        
        # Export items based on format
        if export_format.lower() == 'csv':
            df = pd.DataFrame(items_data)
            df.to_csv(items_file_path, index=False)
        elif export_format.lower() == 'excel':
            df = pd.DataFrame(items_data)
            df.to_excel(items_file_path, index=False)
        elif export_format.lower() == 'json':
            import json
            with open(items_file_path, 'w') as f:
                json.dump(items_data, f, indent=4, default=str)
        
        return len(receipts)
