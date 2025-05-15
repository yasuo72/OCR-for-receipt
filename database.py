"""
Database operations for the receipt scanner application.
"""
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional

class ReceiptDatabase:
    def __init__(self, db_path: str = "data/receipts.db"):
        """Initialize the database connection."""
        # Ensure the directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()
    
    def _create_tables(self):
        """Create necessary tables if they don't exist."""
        # Create receipts table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            merchant TEXT,
            date TEXT,
            total REAL,
            tax REAL,
            receipt_path TEXT,
            created_at TEXT,
            raw_text TEXT
        )
        ''')
        
        # Create items table for individual items on receipts
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            receipt_id INTEGER,
            name TEXT,
            quantity REAL,
            price REAL,
            FOREIGN KEY (receipt_id) REFERENCES receipts (id)
        )
        ''')
        
        self.conn.commit()
    
    def add_receipt(self, receipt_data: Dict[str, Any], items_data: List[Dict[str, Any]]) -> int:
        """
        Add a receipt and its items to the database.
        
        Args:
            receipt_data: Dictionary containing receipt information
            items_data: List of dictionaries containing item information
            
        Returns:
            int: ID of the inserted receipt
        """
        # Add timestamp
        receipt_data['created_at'] = datetime.now().isoformat()
        
        # Insert receipt
        columns = ', '.join(receipt_data.keys())
        placeholders = ', '.join(['?' for _ in receipt_data])
        query = f'INSERT INTO receipts ({columns}) VALUES ({placeholders})'
        
        self.cursor.execute(query, list(receipt_data.values()))
        receipt_id = self.cursor.lastrowid
        
        # Insert items
        if items_data:
            for item in items_data:
                item['receipt_id'] = receipt_id
                columns = ', '.join(item.keys())
                placeholders = ', '.join(['?' for _ in item])
                query = f'INSERT INTO items ({columns}) VALUES ({placeholders})'
                self.cursor.execute(query, list(item.values()))
        
        self.conn.commit()
        return receipt_id
    
    def get_receipt(self, receipt_id: int) -> Dict[str, Any]:
        """
        Get a receipt and its items by ID.
        
        Args:
            receipt_id: ID of the receipt to retrieve
            
        Returns:
            Dict containing receipt and items data
        """
        # Get receipt
        self.cursor.execute('SELECT * FROM receipts WHERE id = ?', (receipt_id,))
        receipt = self.cursor.fetchone()
        
        if not receipt:
            return {}
        
        # Convert to dict
        receipt_dict = {
            'id': receipt[0],
            'merchant': receipt[1],
            'date': receipt[2],
            'total': receipt[3],
            'tax': receipt[4],
            'receipt_path': receipt[5],
            'created_at': receipt[6],
            'raw_text': receipt[7]
        }
        
        # Get items
        self.cursor.execute('SELECT * FROM items WHERE receipt_id = ?', (receipt_id,))
        items = self.cursor.fetchall()
        
        items_list = []
        for item in items:
            items_list.append({
                'id': item[0],
                'receipt_id': item[1],
                'name': item[2],
                'quantity': item[3],
                'price': item[4]
            })
        
        receipt_dict['items'] = items_list
        return receipt_dict
    
    def get_all_receipts(self) -> List[Dict[str, Any]]:
        """
        Get all receipts from the database.
        
        Returns:
            List of dictionaries containing receipt data
        """
        self.cursor.execute('SELECT * FROM receipts ORDER BY date DESC')
        receipts = self.cursor.fetchall()
        
        result = []
        for receipt in receipts:
            receipt_dict = {
                'id': receipt[0],
                'merchant': receipt[1],
                'date': receipt[2],
                'total': receipt[3],
                'tax': receipt[4],
                'receipt_path': receipt[5],
                'created_at': receipt[6]
            }
            result.append(receipt_dict)
        
        return result
    
    def search_receipts(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for receipts by merchant name or raw text.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching receipts
        """
        search_query = f"%{query}%"
        self.cursor.execute(
            'SELECT * FROM receipts WHERE merchant LIKE ? OR raw_text LIKE ? ORDER BY date DESC',
            (search_query, search_query)
        )
        receipts = self.cursor.fetchall()
        
        result = []
        for receipt in receipts:
            receipt_dict = {
                'id': receipt[0],
                'merchant': receipt[1],
                'date': receipt[2],
                'total': receipt[3],
                'tax': receipt[4],
                'receipt_path': receipt[5],
                'created_at': receipt[6]
            }
            result.append(receipt_dict)
        
        return result
    
    def delete_receipt(self, receipt_id: int) -> bool:
        """
        Delete a receipt and its items from the database.
        
        Args:
            receipt_id: ID of the receipt to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Delete items first (foreign key constraint)
            self.cursor.execute('DELETE FROM items WHERE receipt_id = ?', (receipt_id,))
            
            # Delete receipt
            self.cursor.execute('DELETE FROM receipts WHERE id = ?', (receipt_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting receipt: {e}")
            return False
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
