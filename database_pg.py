"""
Database operations for the receipt scanner application with PostgreSQL support.
"""
import os
import json
import sqlite3
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Dict, List, Any, Optional

class ReceiptDatabase:
    def __init__(self, db_url: str = None):
        """Initialize the database connection."""
        # Use environment variable for db_url if provided, otherwise use default
        if db_url is None:
            db_url = os.environ.get('DATABASE_URL', "data/receipts.db")
        
        self.db_url = db_url
        self.is_postgres = db_url.startswith('postgresql')
        
        if self.is_postgres:
            # PostgreSQL connection
            self.conn = psycopg2.connect(db_url)
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        else:
            # SQLite connection
            os.makedirs(os.path.dirname(db_url), exist_ok=True)
            self.conn = sqlite3.connect(db_url)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
        
        self._create_tables()
    
    def _create_tables(self):
        """Create necessary tables if they don't exist."""
        if self.is_postgres:
            # Create receipts table for PostgreSQL
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS receipts (
                id SERIAL PRIMARY KEY,
                merchant TEXT,
                date TEXT,
                total REAL,
                tax REAL,
                receipt_path TEXT,
                created_at TEXT,
                raw_text TEXT
            )
            ''')
            
            # Create items table for PostgreSQL
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id SERIAL PRIMARY KEY,
                receipt_id INTEGER,
                name TEXT,
                quantity REAL,
                price REAL,
                FOREIGN KEY (receipt_id) REFERENCES receipts (id)
            )
            ''')
        else:
            # Create receipts table for SQLite
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
            
            # Create items table for SQLite
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
        
        if self.is_postgres:
            # Insert receipt for PostgreSQL
            columns = list(receipt_data.keys())
            placeholders = [f'%s' for _ in receipt_data]
            
            query = sql.SQL("INSERT INTO receipts ({}) VALUES ({}) RETURNING id").format(
                sql.SQL(', ').join(map(sql.Identifier, columns)),
                sql.SQL(', ').join(sql.Placeholder() * len(columns))
            )
            
            self.cursor.execute(query, list(receipt_data.values()))
            receipt_id = self.cursor.fetchone()['id']
            
            # Insert items for PostgreSQL
            if items_data:
                for item in items_data:
                    item['receipt_id'] = receipt_id
                    columns = list(item.keys())
                    placeholders = [f'%s' for _ in item]
                    
                    query = sql.SQL("INSERT INTO items ({}) VALUES ({})").format(
                        sql.SQL(', ').join(map(sql.Identifier, columns)),
                        sql.SQL(', ').join(sql.Placeholder() * len(columns))
                    )
                    
                    self.cursor.execute(query, list(item.values()))
        else:
            # Insert receipt for SQLite
            columns = ', '.join(receipt_data.keys())
            placeholders = ', '.join(['?' for _ in receipt_data])
            query = f'INSERT INTO receipts ({columns}) VALUES ({placeholders})'
            
            self.cursor.execute(query, list(receipt_data.values()))
            receipt_id = self.cursor.lastrowid
            
            # Insert items for SQLite
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
        if self.is_postgres:
            # Get receipt for PostgreSQL
            self.cursor.execute('SELECT * FROM receipts WHERE id = %s', (receipt_id,))
            receipt = self.cursor.fetchone()
            
            if not receipt:
                return {}
            
            # Convert to dict
            receipt_dict = dict(receipt)
            
            # Get items for PostgreSQL
            self.cursor.execute('SELECT * FROM items WHERE receipt_id = %s', (receipt_id,))
            items = self.cursor.fetchall()
            
            items_list = []
            for item in items:
                items_list.append(dict(item))
        else:
            # Get receipt for SQLite
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
            
            # Get items for SQLite
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
        if self.is_postgres:
            # Get all receipts for PostgreSQL
            self.cursor.execute('SELECT * FROM receipts ORDER BY date DESC')
            receipts = self.cursor.fetchall()
            
            result = []
            for receipt in receipts:
                receipt_dict = dict(receipt)
                # Exclude raw_text to reduce payload size
                if 'raw_text' in receipt_dict:
                    del receipt_dict['raw_text']
                result.append(receipt_dict)
        else:
            # Get all receipts for SQLite
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
        if self.is_postgres:
            # Search receipts for PostgreSQL
            search_query = f"%{query}%"
            self.cursor.execute(
                'SELECT * FROM receipts WHERE merchant ILIKE %s OR raw_text ILIKE %s ORDER BY date DESC',
                (search_query, search_query)
            )
            receipts = self.cursor.fetchall()
            
            result = []
            for receipt in receipts:
                receipt_dict = dict(receipt)
                # Exclude raw_text to reduce payload size
                if 'raw_text' in receipt_dict:
                    del receipt_dict['raw_text']
                result.append(receipt_dict)
        else:
            # Search receipts for SQLite
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
            if self.is_postgres:
                # Delete items first (foreign key constraint) for PostgreSQL
                self.cursor.execute('DELETE FROM items WHERE receipt_id = %s', (receipt_id,))
                
                # Delete receipt for PostgreSQL
                self.cursor.execute('DELETE FROM receipts WHERE id = %s', (receipt_id,))
            else:
                # Delete items first (foreign key constraint) for SQLite
                self.cursor.execute('DELETE FROM items WHERE receipt_id = ?', (receipt_id,))
                
                # Delete receipt for SQLite
                self.cursor.execute('DELETE FROM receipts WHERE id = ?', (receipt_id,))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting receipt: {e}")
            self.conn.rollback()
            return False
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
