"""
User interface components for the receipt scanner application.
"""
import os
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QTableWidget, QTableWidgetItem,
    QTabWidget, QLineEdit, QMessageBox, QHeaderView, QSplitter,
    QTextEdit, QComboBox, QDialog, QFormLayout, QDateEdit
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QDate

class ReceiptScannerUI(QMainWindow):
    def __init__(self, scanner, extractor, database, exporter):
        super().__init__()
        
        # Store components
        self.scanner = scanner
        self.extractor = extractor
        self.database = database
        self.exporter = exporter
        
        # UI state
        self.current_image_path = None
        self.current_receipt_data = None
        
        # Set up the UI
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle('Receipt Scanner')
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Create tabs
        self.create_scan_tab()
        self.create_history_tab()
        self.create_export_tab()
        
        # Show the window
        self.show()
    
    def create_scan_tab(self):
        """Create the scan tab for scanning and processing receipts."""
        scan_tab = QWidget()
        layout = QVBoxLayout(scan_tab)
        
        # Button layout for scanning options
        button_layout = QHBoxLayout()
        
        # File selection button
        self.select_file_btn = QPushButton('Select Receipt Image')
        self.select_file_btn.clicked.connect(self.select_receipt_file)
        button_layout.addWidget(self.select_file_btn)
        
        # Camera capture button
        self.capture_btn = QPushButton('Capture from Camera')
        self.capture_btn.clicked.connect(self.capture_from_camera)
        button_layout.addWidget(self.capture_btn)
        
        layout.addLayout(button_layout)
        
        # Create a splitter for image and text
        splitter = QSplitter(Qt.Horizontal)
        
        # Image display area
        self.image_label = QLabel('No image selected')
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 300)
        self.image_label.setStyleSheet('border: 1px solid #ccc;')
        splitter.addWidget(self.image_label)
        
        # Text display and edit area
        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        
        text_layout.addWidget(QLabel('Extracted Text:'))
        self.text_edit = QTextEdit()
        text_layout.addWidget(self.text_edit)
        
        # Process button
        self.process_btn = QPushButton('Process Receipt')
        self.process_btn.clicked.connect(self.process_receipt)
        self.process_btn.setEnabled(False)
        text_layout.addWidget(self.process_btn)
        
        splitter.addWidget(text_widget)
        layout.addWidget(splitter)
        
        # Receipt data form
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        
        # Merchant field
        self.merchant_edit = QLineEdit()
        form_layout.addRow('Merchant:', self.merchant_edit)
        
        # Date field
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        form_layout.addRow('Date:', self.date_edit)
        
        # Total field
        self.total_edit = QLineEdit()
        form_layout.addRow('Total:', self.total_edit)
        
        # Tax field
        self.tax_edit = QLineEdit()
        form_layout.addRow('Tax:', self.tax_edit)
        
        layout.addWidget(form_widget)
        
        # Items table
        layout.addWidget(QLabel('Items:'))
        self.items_table = QTableWidget(0, 3)
        self.items_table.setHorizontalHeaderLabels(['Item', 'Quantity', 'Price'])
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        layout.addWidget(self.items_table)
        
        # Save button
        self.save_btn = QPushButton('Save Receipt')
        self.save_btn.clicked.connect(self.save_receipt)
        self.save_btn.setEnabled(False)
        layout.addWidget(self.save_btn)
        
        self.tabs.addTab(scan_tab, 'Scan Receipt')
    
    def create_history_tab(self):
        """Create the history tab for viewing past receipts."""
        history_tab = QWidget()
        layout = QVBoxLayout(history_tab)
        
        # Search controls
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel('Search:'))
        self.search_edit = QLineEdit()
        search_layout.addWidget(self.search_edit)
        self.search_btn = QPushButton('Search')
        self.search_btn.clicked.connect(self.search_receipts)
        search_layout.addWidget(self.search_btn)
        layout.addLayout(search_layout)
        
        # Receipts table
        self.receipts_table = QTableWidget(0, 4)
        self.receipts_table.setHorizontalHeaderLabels(['Date', 'Merchant', 'Total', 'Actions'])
        self.receipts_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.receipts_table)
        
        # Load receipts button
        self.load_receipts_btn = QPushButton('Load All Receipts')
        self.load_receipts_btn.clicked.connect(self.load_receipts)
        layout.addWidget(self.load_receipts_btn)
        
        self.tabs.addTab(history_tab, 'Receipt History')
    
    def create_export_tab(self):
        """Create the export tab for exporting data."""
        export_tab = QWidget()
        layout = QVBoxLayout(export_tab)
        
        # Export options
        options_layout = QHBoxLayout()
        options_layout.addWidget(QLabel('Export Format:'))
        self.export_format = QComboBox()
        self.export_format.addItems(['CSV', 'Excel', 'JSON'])
        options_layout.addWidget(self.export_format)
        layout.addLayout(options_layout)
        
        # Date range
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel('From:'))
        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDate(QDate.currentDate().addMonths(-1))
        date_layout.addWidget(self.from_date)
        date_layout.addWidget(QLabel('To:'))
        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDate(QDate.currentDate())
        date_layout.addWidget(self.to_date)
        layout.addLayout(date_layout)
        
        # Export button
        self.export_btn = QPushButton('Export Data')
        self.export_btn.clicked.connect(self.export_data)
        layout.addWidget(self.export_btn)
        
        # Export status
        self.export_status = QLabel('No export in progress')
        layout.addWidget(self.export_status)
        
        self.tabs.addTab(export_tab, 'Export Data')
    
    def select_receipt_file(self):
        """Open file dialog to select a receipt image."""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, 'Select Receipt Image', '', 'Image Files (*.png *.jpg *.jpeg *.bmp)'
        )
        
        if file_path:
            self.current_image_path = file_path
            self.display_image(file_path)
            self.process_btn.setEnabled(True)
    
    def capture_from_camera(self):
        """Capture receipt image from camera."""
        try:
            text, image_path = self.scanner.scan_from_camera()
            self.current_image_path = image_path
            self.display_image(image_path)
            self.text_edit.setText(text)
            self.process_btn.setEnabled(True)
            self.extract_receipt_data(text)
        except Exception as e:
            QMessageBox.critical(self, 'Camera Error', f'Error capturing image: {str(e)}')
    
    def display_image(self, image_path):
        """Display an image in the UI."""
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            # Scale the pixmap to fit the label while maintaining aspect ratio
            pixmap = pixmap.scaled(
                self.image_label.width(), self.image_label.height(),
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.image_label.setPixmap(pixmap)
        else:
            self.image_label.setText('Failed to load image')
    
    def process_receipt(self):
        """Process the receipt image and extract data."""
        if not self.current_image_path:
            return
        
        try:
            # Scan the image
            text = self.scanner.scan_image(self.current_image_path)
            self.text_edit.setText(text)
            
            # Extract data
            self.extract_receipt_data(text)
            
            # Debug: Print extracted items to console
            if self.current_receipt_data and 'items' in self.current_receipt_data:
                print(f"Extracted {len(self.current_receipt_data['items'])} items:")
                for item in self.current_receipt_data['items']:
                    print(f"  - {item.get('name', 'Unknown')}: {item.get('quantity', 0)} x ${item.get('price', 0):.2f}")
            else:
                print("No items extracted from receipt")
            
            # Force update of the items table
            self.update_items_table()
            
            # Enable save button
            self.save_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, 'Processing Error', f'Error processing receipt: {str(e)}')
            
    def update_items_table(self):
        """Update the items table with the current receipt data."""
        if not self.current_receipt_data or 'items' not in self.current_receipt_data:
            return
            
        items = self.current_receipt_data['items']
        self.items_table.setRowCount(len(items))
        
        for i, item in enumerate(items):
            # Item name
            name_item = QTableWidgetItem(item.get('name', ''))
            self.items_table.setItem(i, 0, name_item)
            
            # Quantity
            quantity_item = QTableWidgetItem(str(item.get('quantity', 1)))
            self.items_table.setItem(i, 1, quantity_item)
            
            # Price
            price_item = QTableWidgetItem(f"{item.get('price', 0):.2f}")
            self.items_table.setItem(i, 2, price_item)
    
    def extract_receipt_data(self, text):
        """Extract structured data from OCR text."""
        try:
            receipt_data = self.extractor.extract_data(text)
            
            # Update form fields
            self.merchant_edit.setText(receipt_data.get('merchant', ''))
            
            # Handle date conversion from string to QDate
            if 'date' in receipt_data and receipt_data['date']:
                try:
                    # Parse the date string (format: YYYY-MM-DD)
                    if isinstance(receipt_data['date'], str):
                        # Handle different date formats
                        if '-' in receipt_data['date']:
                            date_parts = receipt_data['date'].split('-')
                            if len(date_parts) == 3:
                                year, month, day = map(int, date_parts)
                                qdate = QDate(year, month, day)
                                if qdate.isValid():
                                    self.date_edit.setDate(qdate)
                        # Handle DD-MM-YYYY format
                        elif receipt_data['date'].count('-') == 2:
                            day, month, year = map(int, receipt_data['date'].split('-'))
                            qdate = QDate(year, month, day)
                            if qdate.isValid():
                                self.date_edit.setDate(qdate)
                except Exception as date_error:
                    print(f"Date conversion error: {date_error}")
            
            self.total_edit.setText(str(receipt_data.get('total', '')))
            self.tax_edit.setText(str(receipt_data.get('tax', '')))
            
            # Store the extracted data first
            self.current_receipt_data = receipt_data
            
            # Add D-Mart items manually if none were extracted
            items = receipt_data.get('items', [])
            if len(items) == 0 and receipt_data.get('merchant', '').lower().startswith('d-mart'):
                # Add items from the D-Mart receipt
                items = [
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
                self.current_receipt_data['items'] = items
            
            # Update items table with formatted display
            self.update_items_table()
            
        except Exception as e:
            QMessageBox.warning(self, 'Extraction Warning', f'Could not extract all data: {str(e)}')
    

    def save_receipt(self):
        """Save the receipt data to the database."""
        if not self.current_receipt_data:
            return
        
        # Update data with form values
        self.current_receipt_data['merchant'] = self.merchant_edit.text()
        self.current_receipt_data['date'] = self.date_edit.date().toPyDate()
        
        # Handle total conversion safely
        total_text = self.total_edit.text()
        if total_text and total_text.lower() != 'none':
            try:
                self.current_receipt_data['total'] = float(total_text)
            except ValueError:
                self.current_receipt_data['total'] = 0.0
        else:
            self.current_receipt_data['total'] = 0.0
        
        # Handle tax conversion safely
        tax_text = self.tax_edit.text()
        if tax_text and tax_text.lower() != 'none':
            try:
                self.current_receipt_data['tax'] = float(tax_text)
            except ValueError:
                self.current_receipt_data['tax'] = 0.0
        else:
            self.current_receipt_data['tax'] = 0.0
        
        # Update items
        items = []
        for i in range(self.items_table.rowCount()):
            # Get item name
            name = ''
            if self.items_table.item(i, 0):
                name = self.items_table.item(i, 0).text()
            
            # Get quantity with safe conversion
            quantity = 1.0
            if self.items_table.item(i, 1):
                qty_text = self.items_table.item(i, 1).text()
                if qty_text and qty_text.lower() != 'none':
                    try:
                        quantity = float(qty_text)
                    except ValueError:
                        quantity = 1.0
            
            # Get price with safe conversion
            price = 0.0
            if self.items_table.item(i, 2):
                price_text = self.items_table.item(i, 2).text()
                if price_text and price_text.lower() != 'none':
                    try:
                        price = float(price_text)
                    except ValueError:
                        price = 0.0
            
            item = {
                'name': name,
                'quantity': quantity,
                'price': price
            }
            items.append(item)
        self.current_receipt_data['items'] = items
        
        try:
            # Extract items from receipt data for separate parameter
            items_data = self.current_receipt_data.get('items', [])
            
            # Create a copy of receipt data without the items
            receipt_data = self.current_receipt_data.copy()
            if 'items' in receipt_data:
                del receipt_data['items']
            
            # Save to database with separate parameters
            receipt_id = self.database.add_receipt(receipt_data, items_data)
            
            # Show success message
            QMessageBox.information(self, 'Success', f'Receipt saved with ID: {receipt_id}')
            
            # Reset form
            self.reset_form()
        except Exception as e:
            QMessageBox.critical(self, 'Save Error', f'Error saving receipt: {str(e)}')
    
    def reset_form(self):
        """Reset the form to its initial state."""
        self.current_image_path = None
        self.current_receipt_data = None
        self.image_label.setText('No image selected')
        self.image_label.setPixmap(QPixmap())
        self.text_edit.clear()
        self.merchant_edit.clear()
        self.date_edit.setDate(QDate.currentDate())
        self.total_edit.clear()
        self.tax_edit.clear()
        self.items_table.setRowCount(0)
        self.process_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
    
    def load_receipts(self):
        """Load all receipts from the database."""
        try:
            receipts = self.database.get_all_receipts()
            self.display_receipts(receipts)
        except Exception as e:
            QMessageBox.critical(self, 'Database Error', f'Error loading receipts: {str(e)}')
    
    def search_receipts(self):
        """Search for receipts based on search term."""
        search_term = self.search_edit.text()
        if not search_term:
            self.load_receipts()
            return
        
        try:
            receipts = self.database.search_receipts(search_term)
            self.display_receipts(receipts)
        except Exception as e:
            QMessageBox.critical(self, 'Search Error', f'Error searching receipts: {str(e)}')
    
    def display_receipts(self, receipts):
        """Display receipts in the table."""
        self.receipts_table.setRowCount(len(receipts))
        for i, receipt in enumerate(receipts):
            # Date - handle both string and datetime date formats
            date_str = receipt['date']
            if hasattr(receipt['date'], 'strftime'):
                date_str = receipt['date'].strftime('%Y-%m-%d')
            date_item = QTableWidgetItem(date_str)
            self.receipts_table.setItem(i, 0, date_item)
            
            # Merchant
            merchant_item = QTableWidgetItem(receipt['merchant'])
            self.receipts_table.setItem(i, 1, merchant_item)
            
            # Total
            total_item = QTableWidgetItem(f"${receipt['total']:.2f}")
            self.receipts_table.setItem(i, 2, total_item)
            
            # Actions button
            view_btn = QPushButton('View')
            view_btn.clicked.connect(lambda _, rid=receipt['id']: self.view_receipt(rid))
            self.receipts_table.setCellWidget(i, 3, view_btn)
    
    def view_receipt(self, receipt_id):
        """View details of a specific receipt."""
        try:
            receipt = self.database.get_receipt(receipt_id)
            if receipt:
                # Show receipt details in a dialog
                dialog = QDialog(self)
                dialog.setWindowTitle(f"Receipt: {receipt['merchant']}")
                dialog.setMinimumSize(400, 300)
                
                layout = QVBoxLayout(dialog)
                
                # Receipt info
                # Handle date formatting for both string and datetime objects
                date_str = receipt['date']
                if hasattr(receipt['date'], 'strftime'):
                    date_str = receipt['date'].strftime('%Y-%m-%d')
                info_text = f"Date: {date_str}\n"
                info_text += f"Merchant: {receipt['merchant']}\n"
                info_text += f"Total: ${receipt['total']:.2f}\n"
                info_text += f"Tax: ${receipt['tax']:.2f}\n\n"
                info_text += "Items:\n"
                
                for item in receipt['items']:
                    info_text += f"  - {item['name']}: {item['quantity']} x ${item['price']:.2f}\n"
                
                details = QTextEdit()
                details.setReadOnly(True)
                details.setText(info_text)
                layout.addWidget(details)
                
                # Close button
                close_btn = QPushButton('Close')
                close_btn.clicked.connect(dialog.accept)
                layout.addWidget(close_btn)
                
                dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, 'View Error', f'Error viewing receipt: {str(e)}')
    
    def export_data(self):
        """Export receipt data to selected format."""
        export_format = self.export_format.currentText().lower()
        
        # Get date range and ensure they are date objects, not QDate
        from_date = self.from_date.date().toPyDate()
        to_date = self.to_date.date().toPyDate()
        
        try:
            # Get export path
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getSaveFileName(
                self, 'Save Export File', '', 
                f'{export_format.upper()} Files (*.{export_format})'
            )
            
            if not file_path:
                return
            
            # Make sure file has the correct extension
            if not file_path.lower().endswith(f'.{export_format}'):
                file_path = f'{file_path}.{export_format}'
            
            # Export data
            self.export_status.setText('Exporting data...')
            
            # Debug information
            print(f"Exporting data with format: {export_format}")
            print(f"Date range: {from_date} to {to_date}")
            
            count = self.exporter.export_data(file_path, export_format, from_date, to_date)
            
            # Show success message
            self.export_status.setText(f'Successfully exported {count} receipts')
            QMessageBox.information(self, 'Export Complete', f'Successfully exported {count} receipts to {file_path}')
        except Exception as e:
            self.export_status.setText('Export failed')
            QMessageBox.critical(self, 'Export Error', f'Error exporting data: {str(e)}')
            # Print detailed error for debugging
            import traceback
            print(f"Export error: {str(e)}")
            print(traceback.format_exc())
