from django.db import models
from django.utils import timezone


class Receipt(models.Model):
    """
    Stores scanned receipts with extracted metadata and raw OCR text.
    """
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
    ]

    filename = models.CharField(max_length=255)
    image = models.FileField(upload_to='uploads/%Y/%m/', null=True, blank=True)
    processed_image = models.FileField(upload_to='processed/%Y/%m/', null=True, blank=True)
    
    merchant = models.CharField(max_length=255, default='Unknown Merchant')
    date = models.CharField(max_length=100, null=True, blank=True)
    total = models.FloatField(null=True, blank=True)
    subtotal = models.FloatField(null=True, blank=True)
    tax = models.FloatField(null=True, blank=True)
    
    payment_method = models.CharField(max_length=100, null=True, blank=True)
    receipt_number = models.CharField(max_length=100, null=True, blank=True)
    confidence_score = models.FloatField(default=0.0)
    raw_text = models.TextField(blank=True, default='')
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='processed')
    scanner_method = models.CharField(max_length=100, default='enhanced_scanner')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Receipt'
        verbose_name_plural = 'Receipts'

    def __str__(self):
        total_display = f"₹{self.total:.2f}" if self.total is not None else "N/A"
        return f"{self.merchant} ({self.date or 'No Date'}) - {total_display}"

    def to_dict(self):
        """Standard serialization for API responses."""
        return {
            'id': self.id,
            'filename': self.filename,
            'merchant': self.merchant,
            'date': self.date or '',
            'total': self.total,
            'subtotal': self.subtotal,
            'tax': self.tax,
            'payment_method': self.payment_method,
            'receipt_number': self.receipt_number,
            'confidence_score': self.confidence_score,
            'raw_text': self.raw_text,
            'status': self.status,
            'scanner_method': self.scanner_method,
            'image_url': self.image.url if self.image else None,
            'processed_image_url': self.processed_image.url if self.processed_image else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'items': [item.to_dict() for item in self.items.all()]
        }

    def to_flutter_dict(self, lines=None):
        """Format matching Flutter app compatibility expectations."""
        item_list = [item.to_dict() for item in self.items.all()]
        text_lines = lines if lines is not None else (self.raw_text.split('\n') if self.raw_text else [])

        return {
            'success': self.status == 'processed',
            'id': self.id,
            'filename': str(self.filename),
            'scanner_type': str(self.scanner_method),
            'timestamp': timezone.now().isoformat(),
            'message': 'Receipt processed successfully' if self.status == 'processed' else 'Receipt processing failed',
            'text': str(self.raw_text),
            'merchant': self.merchant or 'Unknown Merchant',
            'date': str(self.date or ''),
            'total': self.total,
            'tax': self.tax,
            'raw_text': str(self.raw_text),
            'items': item_list,
            'data': {
                'merchant': self.merchant,
                'date': self.date,
                'total': self.total,
                'subtotal': self.subtotal,
                'tax': self.tax,
                'items': item_list,
                'payment_method': self.payment_method,
                'receipt_number': self.receipt_number,
                'confidence_score': self.confidence_score,
                'raw_text': self.raw_text
            },
            'receipt': {
                'id': self.id,
                'text': str(self.raw_text),
                'total': float(self.total) if self.total is not None else 0.0,
                'date': str(self.date or ''),
                'items': [str(line) for line in text_lines if line.strip()],
                'confidence': f"{self.confidence_score:.2f}" if self.confidence_score else 'basic',
                'method': str(self.scanner_method),
                'status': str(self.status)
            }
        }


class ReceiptItem(models.Model):
    """
    Individual line items extracted from a receipt.
    """
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=255)
    quantity = models.FloatField(default=1.0)
    unit_price = models.FloatField(default=0.0)
    total_price = models.FloatField(default=0.0)
    hsn_code = models.CharField(max_length=100, null=True, blank=True)
    tax_rate = models.FloatField(default=0.0)
    category = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        ordering = ['id']
        verbose_name = 'Receipt Item'
        verbose_name_plural = 'Receipt Items'

    def __str__(self):
        return f"{self.name} (Qty: {self.quantity}, Price: ₹{self.total_price:.2f})"

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'quantity': self.quantity,
            'price': self.unit_price,
            'unit_price': self.unit_price,
            'totalPrice': self.total_price,
            'total_price': self.total_price,
            'hsn_code': self.hsn_code,
            'tax_rate': self.tax_rate,
            'category': self.category
        }
