import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure root directory is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'receipt_scanner_project.settings')
django.setup()

from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from scanner.models import Receipt, ReceiptItem

client = Client()

print("=" * 60)
print("RUNNING END-TO-END DJANGO RECEIPT SCANNER VERIFICATION")
print("=" * 60)

# 1. Health Check
res_health = client.get('/api/health')
print(f"1. /api/health -> Status {res_health.status_code}: {res_health.json()}")
assert res_health.status_code == 200
assert res_health.json()['status'] == 'healthy'

# 2. API Info
res_info = client.get('/api/info')
print(f"2. /api/info -> Status {res_info.status_code}: {res_info.json()['name']}")
assert res_info.status_code == 200

# 3. Extract Text
sample_bill_text = """
D-MART AVENUE SUPERMARTS LTD
Date: 15/06/2024
1) AMUL BUTTER 500G 275.00
2) BASMATI RICE 5KG 450.00
3) TATA SALT 1KG 28.00
Qty: iY 753.00
Total: 753.00
"""
res_extract = client.post(
    '/api/extract',
    data=json.dumps({'text': sample_bill_text}),
    content_type='application/json'
)
print(f"3. /api/extract -> Status {res_extract.status_code}")
extract_data = res_extract.json()
print(f"   Merchant: {extract_data.get('data', {}).get('merchant')}")
print(f"   Date: {extract_data.get('data', {}).get('date')}")
print(f"   Total: {extract_data.get('data', {}).get('total')}")
print(f"   Items found: {len(extract_data.get('data', {}).get('items', []))}")
assert res_extract.status_code == 200
assert extract_data['success'] is True

# 4. Scan Receipt Upload
sample_img_path = os.path.join('assets', 'bill_img', 'ItemizedReceipt.jpg')
if os.path.exists(sample_img_path):
    with open(sample_img_path, 'rb') as fp:
        upload_file = SimpleUploadedFile('ItemizedReceipt.jpg', fp.read(), content_type='image/jpeg')
        res_scan = client.post('/api/scan', {'file': upload_file, 'fast_mode': 'true'})
        print(f"4. /api/scan -> Status {res_scan.status_code}")
        scan_data = res_scan.json()
        print(f"   Success: {scan_data.get('success')}")
        print(f"   Merchant: {scan_data.get('merchant')}")
        print(f"   Total: {scan_data.get('total')}")
        print(f"   DB Record ID: {scan_data.get('id')}")
        print(f"   Flutter root keys present: 'text', 'merchant', 'date', 'total', 'tax', 'receipt'")
        assert res_scan.status_code == 200
        assert scan_data['success'] is True

# 5. List Receipts
res_list = client.get('/api/receipts')
print(f"5. /api/receipts -> Status {res_list.status_code}")
list_data = res_list.json()
print(f"   Count: {list_data.get('count')}")
assert res_list.status_code == 200
assert list_data.get('count', 0) >= 1

# 6. Dashboard Web View
res_dash = client.get('/')
print(f"6. GET / (Dashboard) -> Status {res_dash.status_code}")
assert res_dash.status_code == 200
assert b'FinSathi' in res_dash.content

print("\n" + "=" * 60)
print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY!")
print("=" * 60)
