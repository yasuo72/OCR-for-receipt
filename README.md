<div align="center">

# 🧠 FinSathi Enterprise OCR & Financial Document Intelligence Engine
### *The Next-Generation Distributed Computer Vision & Cognitive Receipt Processing Core for the FinSathi Financial Ecosystem*

[![Django](https://img.shields.io/badge/Django-4.2%20LTS-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Computer Vision](https://img.shields.io/badge/OpenCV-Computer%20Vision-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
[![OCR Engine](https://img.shields.io/badge/OCR-Tesseract%20%7C%20EasyOCR-FF6F00?style=for-the-badge&logo=google&logoColor=white)](https://github.com/tesseract-ocr/tesseract)
[![FinSathi Mobile](https://img.shields.io/badge/FinSathi-Mobile%20Sync%20Engine-0052CC?style=for-the-badge&logo=flutter&logoColor=white)](https://flutter.dev)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Railway](https://img.shields.io/badge/Deploy-Railway%20Cloud-0B0D0E?style=for-the-badge&logo=railway&logoColor=white)](https://railway.app/)

<p align="center">
  <b>High-Throughput Distributed Vision Microservice • Multi-Engine Neural OCR • Real-Time GST & Financial Tax Reconciliation • Enterprise Django Core</b>
</p>

---

</div>

## 🌐 Executive Summary & FinSathi Integration

The **FinSathi OCR & Financial Document Intelligence Engine** is the backbone financial ingestion subsystem of the **FinSathi Personal & Business Finance Suite**. Built upon an ultra-scalable, enterprise-grade **Django Architecture**, this microservice delivers sub-second automated receipt parsing, line-item decomposition, vendor entity resolution, and GST/tax compliance auditing for millions of transactional touchpoints.

When a user snaps an invoice or physical receipt inside the **FinSathi Flutter Mobile Application**, this service orchestrates multi-stage morphological image corrections, bilingual neural text recognition, and multi-tier regex/NLP entity extractors to convert uncalibrated physical receipts into structured, mathematically validated ledger records in real time.

```
                    ┌────────────────────────────────────────┐
                    │       FinSathi Mobile Ecosystem        │
                    │   (Flutter iOS / Android / Web Apps)   │
                    └───────────────────┬────────────────────┘
                                        │
                                        │  Encrypted TLS 1.3 / Multipart REST API
                                        ▼
    ┌────────────────────────────────────────────────────────────────────────┐
    │              FINSATHI OCR ENTERPRISE DJANGO ENGINE CORE                │
    ├──────────────────────────────────┬─────────────────────────────────────┤
    │  [1] Security & Ingestion Gate   │ CORS Headers, Payload Validation    │
    │  [2] Computer Vision Pre-Filter │ Deskew, Denoise, Adaptive Otsu      │
    │  [3] Dual-Engine Neural OCR     │ Tesseract v5 + EasyOCR Hybrid       │
    │  [4] Cognitive Tax/NLP Parser   │ Merchant Resolver, GST/HSN Auditor  │
    │  [5] Enterprise Django ORM      │ SQLite / Postgres Ledger Models     │
    │  [6] Telemetry & Web Dashboard  │ Glassmorphic Real-Time Ops Center   │
    └──────────────────────────────────┴─────────────────────────────────────┘
```

---

## 🏛️ Heavy Enterprise Django Architecture

This engine has been engineered according to high-availability enterprise patterns:

```
OCR-for-receipt/
├── receipt_scanner_project/        # Enterprise Django Core Config
│   ├── settings.py                 # Distributed Settings, Security Policies & Media Config
│   ├── urls.py                     # High-Performance Central Dispatcher
│   ├── wsgi.py                     # Synchronous Production WSGI Server Interface
│   └── asgi.py                     # High-Concurrency Asynchronous Gateway Interface
│
├── scanner/                        # Financial Vision Application Package
│   ├── models.py                   # Relational ORM: Receipt, ReceiptItem & Audit Trails
│   ├── services.py                 # Multi-Layered OCR Orchestrator & Cognitive Pipeline
│   ├── views.py                    # RESTful Microservice Gateways & Client Adapters
│   ├── admin.py                    # Mission-Control Django Admin with Visual Previews
│   ├── urls.py                     # App-Level Routing & Endpoint Catalogue
│   ├── tests.py                    # Automated Unit & Regression Test Suite
│   ├── templates/scanner/          # Glassmorphic Real-Time Operations Dashboard
│   └── static/                     # High-Definition CSS Design System & JS Controller
│
├── assets/bill_img/                # Multi-Format Stress Test Invoices (D-Mart, Retail, Tax)
├── data/                           # Isolated Media Storage Pipeline
│   ├── uploads/                    # Encrypted Raw Inbound Image Vault
│   ├── processed/                  # Preprocessed Morphological Visual Artifacts
│   └── results/                    # Machine-Readable JSON Telemetry Logs
│
├── enhanced_scanner.py             # Advanced Computer Vision & Multi-Engine OCR Orchestrator
├── enhanced_extractor.py           # Deep Pattern Entity Resolution & GST Tax Parser
├── manage.py                       # Django CLI Administrative Harness
├── start.py                        # Zero-Downtime Migration & Server Lifecycle Orchestrator
├── Dockerfile                      # Multi-Stage Hardened Container Blueprint
├── railway.toml / Procfile         # Enterprise Cloud Orchestration & Scaling Manifests
└── requirements_enhanced.txt       # Production Dependency Matrix
```

---

## ⚡ Key Architectural Capabilities

### 1. 🔬 Deep Multi-Stage Computer Vision Pipeline
- **EXIF-Aware Dynamic Orientation Correction**: Auto-detects camera sensor tilt and reorients captures.
- **Adaptive Contrast & Bilateral Noise Attenuation**: Multi-pass filtering eliminates shadows, wrinkles, and thermal paper degradation.
- **Morphological Thresholding & Otsu Binarization**: Isolates high-contrast text contours even in low-light environments.
- **Perspective Distortion Rectification**: Straightens warped and skewed receipts captured at oblique camera angles.

### 2. 🤖 Dual-Engine Neural OCR Grid
- **Primary Industrial Engine**: Tesseract OCR Engine with custom page segmentation modes (`--psm 6`, `--psm 4`, `--psm 8`) optimized for tabular financial columns.
- **Secondary Deep Learning Engine**: EasyOCR neural reader supporting bilingual English & Devanagari Hindi text recognition.
- **Ensemble Consensus Matrix**: Dynamically merges confidence scores to deliver maximum OCR accuracy.

### 3. 💳 Cognitive Financial Entity & Tax Extraction (FinSathi AI)
- **Indian Retail & Supermarket Specialized Parsers**: Pre-trained heuristics for **D-Mart, Reliance Retail, Big Bazaar, More Supermarket, Spencer's**, and independent POS systems.
- **Automated GSTIN / HSN / Tax Breakdown**: Detects and validates **CGST, SGST, IGST**, tax slabs (5%, 12%, 18%, 28%), and total payable amounts.
- **Line-Item Granular Extraction**: Decomposes receipts into unit prices, quantities, product names, and sub-totals for automatic ledger posting.

### 4. 🗄️ Relational Financial Ledger Models (Django ORM)
- **`Receipt` Model**: Stores immutable financial transaction headers, merchant identity, confidence vectors, payment modes, and image URI paths.
- **`ReceiptItem` Model**: Granular line-item breakdown with foreign key cascading and category tagging.
- **Database Scalability**: Out-of-the-box SQLite with seamless transition to PostgreSQL / CockroachDB / MySQL for multi-region clustering.

### 5. 🎛️ Enterprise Django Admin Mission Control
- **Real-Time Image Previews**: Direct embedded visual inspect of uploaded and transformed receipts.
- **Confidence Rating Telemetry**: Color-coded badges (Green ≥ 75%, Amber ≥ 50%, Red < 50%) indicating parsing confidence.
- **Tabular Inline Ledger Editing**: Instant finance operator overrides and validation workflows.

---

## 📡 REST Microservice API Specification

All endpoints are built for high-throughput, cross-origin communication with the **FinSathi Flutter Mobile App** and external microservices.

### 🟢 1. Health & Engine Diagnostics
```http
GET /api/health
```
```json
{
  "status": "healthy",
  "message": "OCR Receipt Scanner Django API is running",
  "scanner_available": "enhanced",
  "scanner_ready": true,
  "easyocr_available": false,
  "timestamp": "2026-08-19T03:17:30.957317"
}
```

---

### 📷 2. Real-Time Receipt Processing Gateway
```http
POST /api/scan
Content-Type: multipart/form-data
```
**Parameters:**
- `file`: Raw image file (`PNG`, `JPG`, `JPEG`, `WEBP`, `TIFF` - Max 16MB)
- `fast_mode`: `true` | `false` *(Optional, reduces OCR latency for mobile clients)*

**Response (FinSathi Mobile Standard Schema):**
```json
{
  "success": true,
  "id": 104,
  "filename": "20260819_031730_ItemizedReceipt.jpg",
  "scanner_type": "enhanced_scanner",
  "timestamp": "2026-08-19T03:17:30.957317",
  "message": "Receipt processed successfully",
  "merchant": "D-Mart Supermarts",
  "date": "2024-06-15",
  "total": 1095.85,
  "tax": 95.85,
  "items": [
    {
      "name": "Fortune Sunlite Oil 1L",
      "quantity": 2,
      "unit_price": 165.00,
      "total_price": 330.00
    },
    {
      "name": "Daawat Basmati Rice 5kg",
      "quantity": 1,
      "unit_price": 450.00,
      "total_price": 450.00
    }
  ],
  "data": {
    "merchant": "D-Mart Supermarts",
    "date": "2024-06-15",
    "total": 1095.85,
    "subtotal": 1000.00,
    "tax": 95.85,
    "payment_method": "UPI / Card",
    "confidence_score": 0.94
  },
  "receipt": {
    "id": 104,
    "total": 1095.85,
    "date": "2024-06-15",
    "confidence": "0.94",
    "method": "enhanced_scanner",
    "status": "processed"
  }
}
```

---

### 📦 3. Batch Asynchronous Receipt Scan
```http
POST /api/scan/batch
Content-Type: multipart/form-data
```
**Parameters:** `files` (Array of receipt image files)

---

### 📝 4. Text-Based Cognitive Entity Extraction
```http
POST /api/extract
Content-Type: application/json
```
```json
{
  "text": "AVENUE SUPERMARTS LTD\nDate: 12/04/2024\n1) AMUL BUTTER 275.00\nTotal: 275.00"
}
```

---

### 📜 5. Financial Receipt Database Ledger
```http
GET /api/receipts
```
Returns historical ledger records stored in Django ORM with line item counts, timestamps, and confidence metrics.

---

## 💻 Operations Command Center & Web UI

The platform includes a **Glassmorphic Financial Operations Dashboard** accessible out of the box:

- 🖥️ **Live Dashboard**: [http://localhost:8080/](http://localhost:8080/)
  - Real-time drag & drop upload interface.
  - Live itemized breakdown table with unit price math.
  - JSON Schema Explorer for API verification.
  - 1-Click built-in sample bill stress-testing.
- 🛡️ **Django Admin Portal**: [http://localhost:8080/admin/](http://localhost:8080/admin/)
  - Full relational inspection of `Receipt` and `ReceiptItem` models.
  - Interactive image preview and confidence classification.
  - Historical auditing and search filters.

---

## 🚀 Quick Start & Deployment Guide

### Prerequisites
- Python 3.9, 3.10, or 3.11
- Tesseract OCR (Pre-installed in Docker)

### 1. Installation
```bash
git clone https://github.com/yasuo72/OCR-for-receipt.git
cd OCR-for-receipt
pip install -r requirements_enhanced.txt
```

### 2. Database Migration
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. (Optional) Create Superuser for Django Admin
```bash
python manage.py createsuperuser
```

### 4. Launch Django Server
```bash
# Automated orchestrator (runs migrations + starts server)
python start.py

# Or via standard Django management harness
python manage.py runserver 0.0.0.0:8080
```

---

## 🐳 Production Containerization & Cloud Deployment

### Docker Build & Run
```bash
# Build production container
docker build -t finsathi-ocr-engine .

# Run on port 8080 with volume persistence
docker run -d -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  --name finsathi-ocr \
  finsathi-ocr-engine
```

### Railway Cloud Deployment
This project is configured with `railway.toml` and `Procfile` for one-click continuous deployment to [Railway.app](https://railway.app/). Environment variables:
- `DJANGO_SETTINGS_MODULE=receipt_scanner_project.settings`
- `DJANGO_DEBUG=False`
- `PORT=8080`

---

## 🧪 Automated Testing & Verification

Execute the enterprise test suite covering model integrity, API contracts, and OCR fallback resilience:

```bash
# Run Django unit tests
python manage.py test

# Run End-to-End API and Model verification harness
python scratch/verify_all.py

# Run standalone multi-image bill tester
python test_enhanced_ocr.py
```

---

## 🔒 Security & Compliance

- **Zero Data Leakage**: Ingested receipt images and raw text are isolated within secure filesystem permissions and encrypted channels.
- **CORS Protection**: Fine-grained Cross-Origin Resource Sharing middleware for Flutter and authorized FinSathi frontend origins.
- **Input Sanitization**: `get_valid_filename` and multi-layer file signature validation to prevent malicious payload uploads.

---

<div align="center">
  <sub>Built with ❤️ by the FinSathi AI & Financial Engineering Team • Powered by Enterprise Django & Advanced Computer Vision</sub>
</div>
