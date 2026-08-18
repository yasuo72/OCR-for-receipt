import os
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from scanner.models import Receipt, ReceiptItem


class ScannerAPITests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_health_check(self):
        """Test /api/health endpoint"""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'healthy')
        self.assertIn('scanner_available', data)

    def test_api_info(self):
        """Test /api/info endpoint"""
        response = self.client.get('/api/info')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('name'), 'OCR Receipt Scanner Django API')
        self.assertIn('endpoints', data)

    def test_extract_endpoint(self):
        """Test /api/extract text parsing"""
        sample_text = """
        D-MART AVENUE SUPERMARTS LTD
        Date: 12/04/2024
        1) AMUL BUTTER 500G 275.00
        2) BASMATI RICE 5KG 450.00
        Qty: iY 725.00
        Total: 725.00
        """
        response = self.client.post(
            '/api/extract',
            data=json.dumps({'text': sample_text}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        extracted = data.get('data', {})
        self.assertIn('merchant', extracted)
        self.assertIn('total', extracted)

    def test_receipt_models_and_list(self):
        """Test Receipt and ReceiptItem creation & /api/receipts endpoint"""
        receipt = Receipt.objects.create(
            filename='test_receipt.jpg',
            merchant='D-Mart',
            date='12/04/2024',
            total=1095.85,
            subtotal=1000.00,
            tax=95.85,
            confidence_score=0.92,
            raw_text='D-Mart ... Total: 1095.85',
            status='processed'
        )
        ReceiptItem.objects.create(
            receipt=receipt,
            name='Fortune Oil 1L',
            quantity=1,
            unit_price=165.00,
            total_price=165.00
        )

        response = self.client.get('/api/receipts')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertGreaterEqual(data.get('count'), 1)
        self.assertEqual(data['receipts'][0]['merchant'], 'D-Mart')

        # Test detail endpoint
        detail_res = self.client.get(f'/api/receipts/{receipt.id}/')
        self.assertEqual(detail_res.status_code, 200)
        detail_data = detail_res.json()
        self.assertTrue(detail_data.get('success'))
        self.assertEqual(detail_data['receipt']['total'], 1095.85)

    def test_dashboard_view(self):
        """Test Web UI dashboard view renders successfully"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'FinSathi')
        self.assertContains(response, 'Django 4.2')
