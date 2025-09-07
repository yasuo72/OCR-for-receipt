"""
Enhanced Receipt Data Extractor with AI-powered parsing and multi-format support.
Supports Indian receipts, invoices, and various international formats.
"""
import re
import datetime
import json
from typing import Dict, List, Any, Tuple, Optional, Union
from dateutil import parser as date_parser
import numpy as np
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ItemData:
    """Container for extracted item information."""
    name: str
    quantity: float = 1.0
    unit_price: float = 0.0
    total_price: float = 0.0
    hsn_code: str = None
    tax_rate: float = 0.0
    category: str = None

class EnhancedReceiptExtractor:
    def __init__(self):
        """Initialize the enhanced receipt data extractor."""
        # Indian currency patterns
        self.currency_patterns = [
            r'₹\s*(\d+(?:[.,]\d+)?)',
            r'Rs\.?\s*(\d+(?:[.,]\d+)?)',
            r'INR\s*(\d+(?:[.,]\d+)?)',
            r'(\d+(?:[.,]\d+)?)\s*₹',
            r'(\d+(?:[.,]\d+)?)\s*Rs\.?'
        ]
        
        # Date patterns for Indian formats
        self.date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # DD/MM/YYYY or MM/DD/YYYY
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})',
            r'(\d{2,4}[/-]\d{1,2}[/-]\d{1,2})',  # YYYY/MM/DD
            r'(\d{1,2}\.?\d{1,2}\.?\d{2,4})',    # DD.MM.YYYY
        ]
        
        # Common Indian merchant patterns
        self.merchant_patterns = [
            r'(?:^|\n)\s*([A-Z][A-Z\s&]{2,30}(?:LTD|LIMITED|PVT|PRIVATE|MART|STORE|SHOP|SUPERMARKET)?)\s*(?:\n|$)',
            r'(?:^|\n)\s*([A-Z][A-Z\s&]{2,30})\s*(?:®|™|©)\s*(?:\n|$)',
            r'(?:^|\n)\s*(D[\s-]?MART|BIG\s*BAZAAR|RELIANCE|MORE|SPENCER\'?S|FOOD\s*WORLD)\s*(?:\n|$)',
        ]
        
        # Tax patterns for Indian GST
        self.tax_patterns = [
            r'(?:CGST|cgst)\s*[@:]\s*(\d+(?:\.\d+)?)\s*%\s*[:\-]?\s*(?:₹|Rs\.?)?\s*(\d+(?:[.,]\d+)?)',
            r'(?:SGST|sgst)\s*[@:]\s*(\d+(?:\.\d+)?)\s*%\s*[:\-]?\s*(?:₹|Rs\.?)?\s*(\d+(?:[.,]\d+)?)',
            r'(?:IGST|igst)\s*[@:]\s*(\d+(?:\.\d+)?)\s*%\s*[:\-]?\s*(?:₹|Rs\.?)?\s*(\d+(?:[.,]\d+)?)',
            r'(?:GST|gst|TAX|tax)\s*[:\-]?\s*(?:₹|Rs\.?)?\s*(\d+(?:[.,]\d+)?)',
            r'(?:Total\s+)?(?:Tax|GST)\s*[:\-]?\s*(?:₹|Rs\.?)?\s*(\d+(?:[.,]\d+)?)',
        ]

    def extract_data(self, text: str, ocr_results: List = None) -> 'ExtractedData':
        """
        Extract structured data from OCR text using enhanced parsing.
        
        Args:
            text: Raw OCR text from receipt
            ocr_results: List of OCR results from different engines
            
        Returns:
            ExtractedData: Structured receipt data
        """
        from enhanced_scanner import ExtractedData
        
        # Clean and normalize text
        cleaned_text = self._clean_text(text)
        
        # Initialize result
        result = ExtractedData()
        result.raw_text = text
        
        # Extract merchant information
        result.merchant = self._extract_merchant_enhanced(cleaned_text)
        
        # Extract date with multiple strategies
        result.date = self._extract_date_enhanced(cleaned_text)
        
        # Extract amounts (total, subtotal, tax)
        amounts = self._extract_amounts_enhanced(cleaned_text)
        result.total = amounts.get('total')
        result.subtotal = amounts.get('subtotal')
        result.tax = amounts.get('tax')
        
        # Extract items with intelligent parsing
        result.items = self._extract_items_enhanced(cleaned_text)
        
        # Extract additional information
        result.receipt_number = self._extract_receipt_number(cleaned_text)
        result.payment_method = self._extract_payment_method(cleaned_text)
        
        # Calculate confidence score
        result.confidence_score = self._calculate_extraction_confidence(result)
        
        # Validate and cross-check extracted data
        result = self._validate_and_correct(result, cleaned_text)
        
        return result

    def _clean_text(self, text: str) -> str:
        """Clean and normalize OCR text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common OCR errors
        text = text.replace('|', 'I')
        text = text.replace('0', 'O', 1)  # First 0 might be O in merchant name
        text = text.replace('5', 'S', 1)  # First 5 might be S in merchant name
        
        # Normalize currency symbols
        text = re.sub(r'[₹Rs\.]+', '₹', text)
        
        # Fix decimal separators
        text = re.sub(r'(\d+),(\d{2})\b', r'\1.\2', text)
        
        return text.strip()

    def _extract_merchant_enhanced(self, text: str) -> Optional[str]:
        """Enhanced merchant name extraction with multiple strategies."""
        lines = text.split('\n')
        
        # Strategy 1: Look for known Indian retailers
        known_merchants = {
            'D MART': 'D-Mart',
            'DMART': 'D-Mart',
            'AVENUE SUPERMARTS': 'D-Mart (Avenue Supermarts Ltd)',
            'BIG BAZAAR': 'Big Bazaar',
            'RELIANCE': 'Reliance Fresh/Smart',
            'MORE': 'More Supermarket',
            'SPENCERS': 'Spencer\'s Retail',
            'FOOD WORLD': 'Food World',
            'STAR BAZAAR': 'Star Bazaar',
            'EASYDAY': 'Easyday Club',
            'HYPERCITY': 'HyperCITY',
            'NATURE\'S BASKET': 'Nature\'s Basket'
        }
        
        for line in lines[:10]:
            line_upper = line.upper().strip()
            for pattern, name in known_merchants.items():
                if pattern in line_upper:
                    return name
        
        # Strategy 2: Pattern-based extraction
        for pattern in self.merchant_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                merchant = match.group(1).strip()
                if len(merchant) > 2 and not self._is_likely_not_merchant(merchant):
                    return merchant
        
        # Strategy 3: First meaningful line analysis
        exclude_patterns = ['CIN', 'GSTIN', 'PAN', 'TIN', 'FSSAI', 'VAT', 'TAX', 'INVOICE', 'RECEIPT']
        
        for line in lines[:8]:
            line = line.strip()
            if len(line) > 3:
                if not any(pattern in line.upper() for pattern in exclude_patterns):
                    if not re.match(r'^[\d\s\-:]+$', line):
                        if not any(x in line.lower() for x in ['tel:', 'phone', 'www.', 'http', 'email']):
                            return line
        
        return None

    def _extract_date_enhanced(self, text: str) -> Optional[str]:
        """Enhanced date extraction with multiple strategies."""
        # Strategy 1: Look for labeled dates
        date_labels = [
            r'(?:bill|invoice|receipt)\s+(?:date|dt)\s*[:\.]?\s*([^\n]+)',
            r'date\s*[:\.]?\s*([^\n]+)',
            r'dt\s*[:\.]?\s*([^\n]+)',
            r'dated?\s*[:\.]?\s*([^\n]+)'
        ]
        
        for pattern in date_labels:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1).strip()
                parsed_date = self._parse_date_string(date_str)
                if parsed_date:
                    return parsed_date
        
        # Strategy 2: Find dates in common formats
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                parsed_date = self._parse_date_string(match)
                if parsed_date:
                    return parsed_date
        
        # Strategy 3: Look for time patterns which often accompany dates
        time_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+(\d{1,2}:\d{2})'
        match = re.search(time_pattern, text)
        if match:
            return self._parse_date_string(match.group(1))
        
        return None

    def _parse_date_string(self, date_str: str) -> Optional[str]:
        """Parse various date string formats."""
        try:
            # Clean the date string
            date_str = re.sub(r'[^\d\-/\.\s\w]', '', date_str).strip()
            
            # Try parsing with dateutil
            parsed = date_parser.parse(date_str, fuzzy=True, dayfirst=True)
            
            # Validate the date (not too far in future or past)
            current_year = datetime.datetime.now().year
            if 2000 <= parsed.year <= current_year + 1:
                return parsed.strftime('%Y-%m-%d')
        except:
            pass
        
        return None

    def _extract_amounts_enhanced(self, text: str) -> Dict[str, Optional[float]]:
        """Enhanced amount extraction for total, subtotal, and tax."""
        amounts = {'total': None, 'subtotal': None, 'tax': None}
        
        lines = text.split('\n')
        
        # Extract total amount
        amounts['total'] = self._extract_total_enhanced(lines)
        
        # Extract tax amount
        amounts['tax'] = self._extract_tax_enhanced(lines)
        
        # Extract subtotal
        amounts['subtotal'] = self._extract_subtotal_enhanced(lines, amounts['total'], amounts['tax'])
        
        return amounts

    def _extract_total_enhanced(self, lines: List[str]) -> Optional[float]:
        """Enhanced total amount extraction."""
        # Patterns for total amount (prioritized)
        total_patterns = [
            r'(?:grand\s+)?total\s*(?:amount)?\s*[:\-]?\s*(?:₹|Rs\.?)?\s*(\d+(?:[.,]\d+)?)',
            r'(?:net\s+)?amount\s*(?:payable|due)?\s*[:\-]?\s*(?:₹|Rs\.?)?\s*(\d+(?:[.,]\d+)?)',
            r'(?:final\s+)?total\s*[:\-]?\s*(?:₹|Rs\.?)?\s*(\d+(?:[.,]\d+)?)',
            r'(?:bill\s+)?amount\s*[:\-]?\s*(?:₹|Rs\.?)?\s*(\d+(?:[.,]\d+)?)',
            r'(?:you\s+)?pay\s*[:\-]?\s*(?:₹|Rs\.?)?\s*(\d+(?:[.,]\d+)?)',
            r'balance\s*[:\-]?\s*(?:₹|Rs\.?)?\s*(\d+(?:[.,]\d+)?)',
        ]
        
        # Search from bottom to top (totals usually at bottom)
        for line in reversed(lines):
            line_lower = line.lower()
            for pattern in total_patterns:
                match = re.search(pattern, line_lower)
                if match:
                    try:
                        amount = float(match.group(1).replace(',', '.'))
                        if 1 <= amount <= 100000:  # Reasonable range
                            return amount
                    except:
                        continue
        
        # Fallback: Look for the largest reasonable amount near the bottom
        for line in reversed(lines[-10:]):
            amounts = re.findall(r'(?:₹|Rs\.?)?\s*(\d+(?:[.,]\d+)?)', line)
            for amount_str in amounts:
                try:
                    amount = float(amount_str.replace(',', '.'))
                    if 10 <= amount <= 100000:
                        return amount
                except:
                    continue
        
        return None

    def _extract_tax_enhanced(self, lines: List[str]) -> Optional[float]:
        """Enhanced tax amount extraction for Indian GST."""
        total_tax = 0.0
        found_tax = False
        
        # Look for GST breakdown
        for line in lines:
            line_lower = line.lower()
            
            # CGST + SGST pattern
            cgst_match = re.search(r'cgst\s*[@:]\s*(\d+(?:\.\d+)?)\s*%\s*[:\-]?\s*(?:₹|Rs\.?)?\s*(\d+(?:[.,]\d+)?)', line_lower)
            if cgst_match:
                try:
                    tax_amount = float(cgst_match.group(2).replace(',', '.'))
                    total_tax += tax_amount
                    found_tax = True
                except:
                    pass
            
            sgst_match = re.search(r'sgst\s*[@:]\s*(\d+(?:\.\d+)?)\s*%\s*[:\-]?\s*(?:₹|Rs\.?)?\s*(\d+(?:[.,]\d+)?)', line_lower)
            if sgst_match:
                try:
                    tax_amount = float(sgst_match.group(2).replace(',', '.'))
                    total_tax += tax_amount
                    found_tax = True
                except:
                    pass
            
            # IGST pattern
            igst_match = re.search(r'igst\s*[@:]\s*(\d+(?:\.\d+)?)\s*%\s*[:\-]?\s*(?:₹|Rs\.?)?\s*(\d+(?:[.,]\d+)?)', line_lower)
            if igst_match:
                try:
                    tax_amount = float(igst_match.group(2).replace(',', '.'))
                    total_tax += tax_amount
                    found_tax = True
                except:
                    pass
            
            # Total tax pattern
            total_tax_match = re.search(r'(?:total\s+)?(?:tax|gst)\s*[:\-]?\s*(?:₹|Rs\.?)?\s*(\d+(?:[.,]\d+)?)', line_lower)
            if total_tax_match and not found_tax:
                try:
                    return float(total_tax_match.group(1).replace(',', '.'))
                except:
                    pass
        
        return total_tax if found_tax else None

    def _extract_subtotal_enhanced(self, lines: List[str], total: Optional[float], tax: Optional[float]) -> Optional[float]:
        """Extract subtotal amount."""
        # Look for explicit subtotal
        subtotal_patterns = [
            r'sub\s*total\s*[:\-]?\s*(?:₹|Rs\.?)?\s*(\d+(?:[.,]\d+)?)',
            r'subtotal\s*[:\-]?\s*(?:₹|Rs\.?)?\s*(\d+(?:[.,]\d+)?)',
            r'(?:before\s+)?tax\s*[:\-]?\s*(?:₹|Rs\.?)?\s*(\d+(?:[.,]\d+)?)',
        ]
        
        for line in lines:
            line_lower = line.lower()
            for pattern in subtotal_patterns:
                match = re.search(pattern, line_lower)
                if match:
                    try:
                        return float(match.group(1).replace(',', '.'))
                    except:
                        continue
        
        # Calculate from total - tax if both available
        if total is not None and tax is not None:
            return total - tax
        
        return None

    def _extract_items_enhanced(self, text: str) -> List[Dict[str, Any]]:
        """Enhanced item extraction with intelligent parsing."""
        items = []
        lines = text.split('\n')
        
        # Find item section boundaries
        item_start, item_end = self._find_item_section(lines)
        
        if item_start >= 0 and item_end > item_start:
            # Process items in the identified section
            for i in range(item_start, item_end):
                line = lines[i].strip()
                if not line:
                    continue
                
                item = self._parse_item_line_enhanced(line)
                if item:
                    items.append(item)
        
        # If no items found, try alternative parsing
        if not items:
            items = self._extract_items_fallback(lines)
        
        return items

    def _find_item_section(self, lines: List[str]) -> Tuple[int, int]:
        """Find the start and end of the items section."""
        start_idx = -1
        end_idx = -1
        
        # Look for header indicators
        header_keywords = ['item', 'description', 'particulars', 'qty', 'rate', 'amount', 'hsn']
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Check for item section start
            if start_idx == -1:
                header_count = sum(1 for keyword in header_keywords if keyword in line_lower)
                if header_count >= 2:
                    start_idx = i + 1
                    continue
                
                # Alternative start indicators
                if any(x in line_lower for x in ['s.no', 'sr.no', 'sl.no']):
                    start_idx = i + 1
                    continue
            
            # Check for item section end
            if start_idx >= 0:
                if any(x in line_lower for x in ['subtotal', 'total', 'tax', 'discount', 'amount payable']):
                    if re.search(r'(?:sub)?total\s*[:\-]', line_lower):
                        end_idx = i
                        break
        
        return start_idx, end_idx if end_idx > 0 else len(lines)

    def _parse_item_line_enhanced(self, line: str) -> Optional[Dict[str, Any]]:
        """Enhanced item line parsing with multiple patterns."""
        # Skip obvious non-item lines
        if self._is_non_item_line(line):
            return None
        
        # Pattern 1: HSN/Code + Description + Qty + Rate + Amount
        pattern1 = r'(?:\d+)\s+([\w\s\-/&]+?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)'
        match = re.search(pattern1, line)
        if match:
            name = match.group(1).strip()
            qty = float(match.group(2))
            rate = float(match.group(3))
            amount = float(match.group(4))
            
            # Validate: qty * rate should approximately equal amount
            if abs(qty * rate - amount) < max(1.0, amount * 0.1):
                return {
                    'name': name,
                    'quantity': qty,
                    'unit_price': rate,
                    'total_price': amount
                }
        
        # Pattern 2: Description + Qty + Rate + Amount (no HSN)
        pattern2 = r'^([\w\s\-/&]+?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)$'
        match = re.search(pattern2, line.strip())
        if match:
            name = match.group(1).strip()
            if len(name) > 2:
                qty = float(match.group(2))
                rate = float(match.group(3))
                amount = float(match.group(4))
                
                return {
                    'name': name,
                    'quantity': qty,
                    'unit_price': rate,
                    'total_price': amount
                }
        
        # Pattern 3: Description + Amount (quantity assumed as 1)
        pattern3 = r'^([\w\s\-/&]+?)\s+(\d+(?:\.\d+)?)$'
        match = re.search(pattern3, line.strip())
        if match:
            name = match.group(1).strip()
            if len(name) > 2:
                amount = float(match.group(2))
                
                return {
                    'name': name,
                    'quantity': 1.0,
                    'unit_price': amount,
                    'total_price': amount
                }
        
        return None

    def _is_non_item_line(self, line: str) -> bool:
        """Check if line is likely not an item."""
        line_lower = line.lower()
        
        # Skip tax lines
        if re.search(r'(?:cgst|sgst|igst|tax)\s*[@%]', line_lower):
            return True
        
        # Skip header lines
        if any(x in line_lower for x in ['hsn', 'particulars', 'description', 'qty', 'rate', 'amount']):
            return True
        
        # Skip total/subtotal lines
        if any(x in line_lower for x in ['total', 'subtotal', 'discount']):
            return True
        
        # Skip lines with only numbers or special characters
        if re.match(r'^[\d\s\-:.]+$', line):
            return True
        
        return False

    def _extract_items_fallback(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Fallback item extraction method."""
        items = []
        
        # Look for lines that might contain items
        for line in lines:
            line = line.strip()
            if len(line) < 3:
                continue
            
            # Skip obvious non-item lines
            if self._is_non_item_line(line):
                continue
            
            # Try to extract item from line
            item = self._parse_item_line_enhanced(line)
            if item:
                items.append(item)
        
        return items

    def _extract_receipt_number(self, text: str) -> Optional[str]:
        """Extract receipt/bill number."""
        patterns = [
            r'(?:receipt|bill|invoice)\s*(?:no|number|#)\s*[:\-]?\s*([A-Z0-9\-/]+)',
            r'(?:ref|reference)\s*(?:no|number)?\s*[:\-]?\s*([A-Z0-9\-/]+)',
            r'(?:transaction|txn)\s*(?:id|no)?\s*[:\-]?\s*([A-Z0-9\-/]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None

    def _extract_payment_method(self, text: str) -> Optional[str]:
        """Extract payment method."""
        payment_methods = {
            'cash': ['cash', 'cash payment'],
            'card': ['card', 'credit card', 'debit card', 'visa', 'mastercard'],
            'upi': ['upi', 'paytm', 'gpay', 'phonepe', 'bhim'],
            'wallet': ['wallet', 'digital wallet'],
            'net_banking': ['net banking', 'netbanking', 'online']
        }
        
        text_lower = text.lower()
        
        for method, keywords in payment_methods.items():
            if any(keyword in text_lower for keyword in keywords):
                return method
        
        return None

    def _is_likely_not_merchant(self, text: str) -> bool:
        """Check if text is likely not a merchant name."""
        text_upper = text.upper()
        
        # Skip if contains ID patterns
        if re.search(r'\b(?:CIN|GSTIN|PAN|TIN|FSSAI)\b', text_upper):
            return True
        
        # Skip if mostly numbers
        if len(re.findall(r'\d', text)) > len(text) * 0.5:
            return True
        
        # Skip if too short or too long
        if len(text.strip()) < 3 or len(text.strip()) > 50:
            return True
        
        return False

    def _calculate_extraction_confidence(self, result: 'ExtractedData') -> float:
        """Calculate confidence score for extracted data."""
        score = 0.0
        max_score = 100.0
        
        # Merchant found
        if result.merchant:
            score += 20
        
        # Date found and valid
        if result.date:
            score += 15
        
        # Total amount found and reasonable
        if result.total and 1 <= result.total <= 100000:
            score += 25
        
        # Tax amount found
        if result.tax:
            score += 10
        
        # Items found
        if result.items:
            score += 20
            # Bonus for multiple items
            if len(result.items) > 1:
                score += 5
        
        # Receipt number found
        if result.receipt_number:
            score += 5
        
        return min(score / max_score, 1.0)

    def _validate_and_correct(self, result: 'ExtractedData', text: str) -> 'ExtractedData':
        """Validate and correct extracted data."""
        # Validate total vs items sum
        if result.items and result.total:
            items_total = sum(item.get('total_price', item.get('unit_price', 0)) for item in result.items)
            
            # If items total is close to extracted total, use items total
            if abs(items_total - result.total) < 5:
                result.total = items_total
        
        # Validate subtotal + tax = total
        if result.subtotal and result.tax and result.total:
            calculated_total = result.subtotal + result.tax
            if abs(calculated_total - result.total) < 2:
                result.total = calculated_total
        
        return result
