"""
OCR Processing and Extraction Service for Django.
Integrates EnhancedReceiptScanner and EnhancedReceiptExtractor with Django models.
"""
import os
import re
import cv2
import numpy as np
import logging
from datetime import datetime
from PIL import Image
import pytesseract
from django.conf import settings
from django.core.files.base import ContentFile
from scanner.models import Receipt, ReceiptItem

logger = logging.getLogger(__name__)

# Initialize enhanced scanner and extractor
try:
    from enhanced_scanner import EnhancedReceiptScanner
    from enhanced_extractor import EnhancedReceiptExtractor
    enhanced_scanner = EnhancedReceiptScanner()
    enhanced_extractor = EnhancedReceiptExtractor()
    SCANNER_AVAILABLE = "enhanced"
    logger.info("Enhanced scanner loaded successfully in Django services")
except Exception as e:
    logger.warning(f"Enhanced scanner not available: {e}. Falling back to basic pytesseract.")
    enhanced_scanner = None
    enhanced_extractor = None
    SCANNER_AVAILABLE = "basic"

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}


def is_allowed_file(filename: str) -> bool:
    """Check if the file has an allowed image extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_scanner_status() -> dict:
    """Get the current OCR capabilities and engine statuses."""
    easyocr_ready = False
    if enhanced_scanner and hasattr(enhanced_scanner, 'easyocr_available'):
        easyocr_ready = enhanced_scanner.easyocr_available

    return {
        'scanner_available': SCANNER_AVAILABLE,
        'enhanced_ready': enhanced_scanner is not None,
        'easyocr_available': easyocr_ready,
        'tesseract_ready': True
    }


def basic_ocr_fallback(image_path: str) -> dict:
    """Fallback OCR extraction using OpenCV and pytesseract."""
    try:
        image = cv2.imread(image_path)
        if image is None:
            return {'error': 'Could not load image file'}

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        text = pytesseract.image_to_string(thresh, config='--psm 6')
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        receipt_data = {
            'raw_text': text.strip(),
            'lines': lines,
            'method': 'basic_pytesseract',
            'status': 'processed',
            'confidence': 0.65,
            'total': None,
            'subtotal': None,
            'tax': None,
            'date': None,
            'merchant': 'Unknown Merchant',
            'items': []
        }

        # D-Mart specific amount detection
        dmart_match = re.search(r'qty:\s*iy\s*(\d+\.\d{2})', text.lower())
        if dmart_match:
            try:
                receipt_data['total'] = float(dmart_match.group(1))
            except (ValueError, TypeError):
                pass

        # General total patterns
        if receipt_data['total'] is None:
            total_patterns = [
                r'total[:\s]*₹?\s*(\d+\.?\d*)',
                r'amount[:\s]*₹?\s*(\d+\.?\d*)',
                r'₹\s*(\d+\.\d{2})',
                r'rs\.?\s*(\d+\.\d{2})',
                r'(\d{4}\.\d{2})',
                r'(\d{3}\.\d{2})'
            ]
            for pattern in total_patterns:
                matches = re.findall(pattern, text.lower())
                if matches:
                    amounts = []
                    for m in matches:
                        try:
                            amt = float(m)
                            if 10.0 <= amt <= 50000.0:
                                amounts.append(amt)
                        except ValueError:
                            continue
                    if amounts:
                        receipt_data['total'] = max(amounts)
                        break

        # Date patterns
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
            r'(\d{2}/\d{2}/\d{4})',
            r'bill dt[:\s]*(\d{2}/\d{2}/\d{4})'
        ]
        for pattern in date_patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                receipt_data['date'] = matches[0]
                break

        return receipt_data
    except Exception as e:
        logger.error(f"Basic OCR fallback failed: {e}")
        return {'error': str(e)}


def process_receipt(image_path: str, filename: str, save_to_db: bool = True, fast_mode: bool = False):
    """
    Process receipt image using Enhanced OCR or fallback, optionally saving to Django database.
    
    Returns:
        tuple: (receipt_model_instance, result_data_dict)
    """
    extracted_data = None
    method_used = 'basic_pytesseract'
    raw_text = ''
    confidence = 0.60
    merchant = 'Unknown Merchant'
    date_str = None
    total = None
    subtotal = None
    tax = None
    payment_method = None
    receipt_number = None
    items_list = []
    lines = []

    # 1. Attempt Enhanced Scanning
    if SCANNER_AVAILABLE == "enhanced" and enhanced_scanner is not None:
        try:
            logger.info(f"Running enhanced OCR on {image_path} (fast_mode={fast_mode})")
            extracted = enhanced_scanner.scan_receipt(image_path, save_processed=True, fast_mode=fast_mode)
            if extracted:
                extracted_data = extracted
                method_used = 'enhanced_scanner'
                raw_text = extracted.raw_text or ''
                confidence = getattr(extracted, 'confidence_score', 0.85) or 0.85
                merchant = extracted.merchant or 'Unknown Merchant'
                date_str = extracted.date
                total = extracted.total
                subtotal = extracted.subtotal
                tax = extracted.tax
                payment_method = extracted.payment_method
                receipt_number = extracted.receipt_number
                items_list = extracted.items or []
                lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
        except Exception as e:
            logger.warning(f"Enhanced scanner raised an error: {e}. Using basic OCR.")

    # 2. Basic OCR Fallback if enhanced produced nothing
    if extracted_data is None:
        fallback_res = basic_ocr_fallback(image_path)
        if 'error' in fallback_res:
            raise RuntimeError(f"OCR processing failed: {fallback_res['error']}")
        
        raw_text = fallback_res.get('raw_text', '')
        lines = fallback_res.get('lines', [])
        total = fallback_res.get('total')
        date_str = fallback_res.get('date')
        confidence = fallback_res.get('confidence', 0.60)
        method_used = 'basic_pytesseract'
        
        # Use enhanced extractor if available to extract structured info from text
        if enhanced_extractor is not None and raw_text:
            try:
                parsed = enhanced_extractor.extract_data(raw_text)
                merchant = parsed.merchant or merchant
                date_str = parsed.date or date_str
                total = parsed.total if parsed.total is not None else total
                tax = parsed.tax if parsed.tax is not None else tax
                subtotal = parsed.subtotal if parsed.subtotal is not None else subtotal
                payment_method = parsed.payment_method
                receipt_number = parsed.receipt_number
                items_list = parsed.items or []
            except Exception as e:
                logger.warning(f"Extractor failed on raw text: {e}")

    # Fallback merchant name logic if still Unknown
    if merchant == 'Unknown Merchant' and raw_text:
        raw_lower = raw_text.lower()
        if any(p in raw_lower for p in ['d: mart', 'dmart', 'd mart', 'avenue supermarts']):
            merchant = 'D-Mart'
        elif 'big bazaar' in raw_lower:
            merchant = 'Big Bazaar'
        elif 'reliance' in raw_lower:
            merchant = 'Reliance Retail'
        elif 'harbor lane cafe' in raw_lower:
            merchant = 'Harbor Lane Cafe'
        elif 'mcdonald' in raw_lower:
            merchant = "McDonald's"
        elif 'kfc' in raw_lower:
            merchant = 'KFC'
        else:
            # Check first 3 lines
            first_lines = [l.strip() for l in raw_text.split('\n')[:4] if len(l.strip()) > 3]
            for fl in first_lines:
                if not re.match(r'^\d+', fl) and not any(k in fl.lower() for k in ['sale', 'batch', 'tax', 'invoice', 'date', 'phone', 'receipt']):
                    merchant = re.sub(r'[^\w\s]', '', fl).strip().title()
                    break

    # Save to Django database if requested
    receipt_obj = None
    if save_to_db:
        try:
            receipt_obj = Receipt.objects.create(
                filename=filename,
                merchant=merchant,
                date=str(date_str) if date_str else '',
                total=float(total) if total is not None else None,
                subtotal=float(subtotal) if subtotal is not None else None,
                tax=float(tax) if tax is not None else None,
                payment_method=payment_method or '',
                receipt_number=receipt_number or '',
                confidence_score=float(confidence),
                raw_text=raw_text,
                status='processed',
                scanner_method=method_used
            )

            # Link uploaded image file if exists
            if os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    receipt_obj.image.save(filename, ContentFile(f.read()), save=True)

            # Create item records
            for item in items_list:
                if isinstance(item, dict):
                    name = item.get('name', 'Item')
                    qty = float(item.get('quantity', 1.0) or 1.0)
                    price = float(item.get('unit_price', item.get('price', 0.0)) or 0.0)
                    tot = float(item.get('total_price', item.get('totalPrice', price * qty)) or price * qty)
                    hsn = item.get('hsn_code')
                    cat = item.get('category')
                    ReceiptItem.objects.create(
                        receipt=receipt_obj,
                        name=str(name),
                        quantity=qty,
                        unit_price=price,
                        total_price=tot,
                        hsn_code=hsn,
                        category=cat
                    )
        except Exception as e:
            logger.error(f"Failed to save receipt to Django DB: {e}")

    # Build response dict
    response_payload = {
        'success': True,
        'id': receipt_obj.id if receipt_obj else None,
        'filename': filename,
        'scanner_type': method_used,
        'timestamp': datetime.now().isoformat(),
        'message': 'Receipt processed successfully',
        'text': raw_text,
        'merchant': merchant,
        'date': str(date_str) if date_str is not None else '',
        'total': total,
        'tax': tax,
        'raw_text': raw_text,
        'items': items_list,
        'data': {
            'merchant': merchant,
            'date': date_str,
            'total': total,
            'subtotal': subtotal,
            'tax': tax,
            'items': items_list,
            'payment_method': payment_method,
            'receipt_number': receipt_number,
            'confidence_score': confidence,
            'raw_text': raw_text
        },
        'receipt': {
            'id': receipt_obj.id if receipt_obj else None,
            'text': raw_text,
            'total': float(total) if total is not None else 0.0,
            'date': str(date_str) if date_str is not None else '',
            'items': [str(l) for l in lines if l],
            'confidence': f"{confidence:.2f}" if isinstance(confidence, (int, float)) else str(confidence),
            'method': method_used,
            'status': 'processed'
        }
    }

    return receipt_obj, response_payload


def parse_raw_text(text: str) -> dict:
    """Parse raw text string using EnhancedReceiptExtractor with regex fallback."""
    if enhanced_extractor is not None:
        try:
            extracted = enhanced_extractor.extract_data(text)
            items = []
            if extracted.items:
                for item in extracted.items:
                    if isinstance(item, dict):
                        items.append({
                            'name': item.get('name'),
                            'quantity': item.get('quantity', 1),
                            'price': item.get('unit_price', 0.0),
                            'totalPrice': item.get('total_price', 0.0),
                            'hsn_code': item.get('hsn_code'),
                            'category': item.get('category')
                        })
            return {
                'merchant': extracted.merchant or 'Unknown Merchant',
                'date': extracted.date,
                'total': extracted.total,
                'subtotal': extracted.subtotal,
                'tax': extracted.tax,
                'raw_text': text,
                'items': items,
                'payment_method': extracted.payment_method,
                'receipt_number': extracted.receipt_number,
                'confidence_score': extracted.confidence_score
            }
        except Exception as e:
            logger.warning(f"Enhanced text extraction error: {e}")

    # Basic regex text extraction fallback
    merchant_name = 'Unknown Merchant'
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if lines:
        for line in lines[:5]:
            if len(line) > 3 and not re.match(r'^\d+', line):
                if not any(k in line.lower() for k in ['sale', 'batch', 'tax', 'invoice', 'date', 'receipt']):
                    merchant_name = line.title()
                    break

    # Total amount
    total_amount = None
    total_matches = re.findall(r'(?:total|amount|grand total|rs\.?|₹)\s*[:\-]?\s*₹?\s*(\d+(?:[.,]\d+)?)', text, re.IGNORECASE)
    if total_matches:
        try:
            total_amount = float(total_matches[-1].replace(',', ''))
        except ValueError:
            pass

    # Date
    date_val = None
    date_matches = re.findall(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', text)
    if date_matches:
        date_val = date_matches[0]

    return {
        'merchant': merchant_name,
        'date': date_val,
        'total': total_amount,
        'subtotal': None,
        'tax': None,
        'raw_text': text,
        'items': [],
        'confidence_score': 0.60
    }
