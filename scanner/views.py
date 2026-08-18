"""
Django views for OCR Receipt Scanner API and Dashboard.
"""
import os
import json
import logging
from datetime import datetime
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.text import get_valid_filename
from django.conf import settings
from scanner.models import Receipt, ReceiptItem
from scanner.services import (
    process_receipt,
    parse_raw_text,
    get_scanner_status,
    is_allowed_file,
    SCANNER_AVAILABLE
)

logger = logging.getLogger(__name__)


def health_check(request):
    """Health check endpoint."""
    status = get_scanner_status()
    return JsonResponse({
        'status': 'healthy',
        'message': 'OCR Receipt Scanner Django API is running',
        'scanner_available': status['scanner_available'],
        'scanner_ready': status['enhanced_ready'],
        'easyocr_available': status['easyocr_available'],
        'timestamp': datetime.now().isoformat()
    })


def api_info(request):
    """API info endpoint."""
    status = get_scanner_status()
    return JsonResponse({
        'name': 'OCR Receipt Scanner Django API',
        'version': '3.0 (Django)',
        'scanner_available': status['scanner_available'],
        'endpoints': {
            'health': '/api/health (GET)',
            'scan': '/api/scan (POST - multipart/form-data)',
            'scan_batch': '/api/scan/batch (POST - multipart/form-data)',
            'extract': '/api/extract (POST - JSON {"text": "..."})',
            'receipts': '/api/receipts (GET)',
            'receipt_detail': '/api/receipts/<id>/ (GET, DELETE)',
            'test': '/api/test (GET)',
            'processed_image': '/api/processed/<filename> (GET)',
            'dashboard': '/ (GET - Web UI)'
        }
    })


@csrf_exempt
@require_http_methods(["POST"])
def scan_receipt(request):
    """
    Receipt scanning endpoint.
    Accepts an uploaded image file under 'file' (or 'image'), executes OCR,
    persists result to Django SQLite DB, and returns structured data.
    """
    try:
        # Check if file was provided
        file_obj = request.FILES.get('file') or request.FILES.get('image')
        if not file_obj:
            return JsonResponse({
                'success': False,
                'error': 'No file provided',
                'message': 'Please upload an image file in the "file" field',
                'timestamp': datetime.now().isoformat()
            }, status=400)

        filename = file_obj.name
        if not filename or not is_allowed_file(filename):
            return JsonResponse({
                'success': False,
                'error': 'Invalid file type',
                'message': 'Allowed formats: PNG, JPG, JPEG, GIF, BMP, TIFF, WEBP',
                'timestamp': datetime.now().isoformat()
            }, status=400)

        # Ensure upload directories exist
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'processed'), exist_ok=True)
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'results'), exist_ok=True)

        clean_filename = get_valid_filename(filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        saved_filename = f"{timestamp}_{clean_filename}"
        filepath = os.path.join(upload_dir, saved_filename)

        # Write uploaded file to disk
        with open(filepath, 'wb+') as dest:
            for chunk in file_obj.chunks():
                dest.write(chunk)

        # Fast mode check from query params or form data
        fast_mode = request.POST.get('fast_mode', 'false').lower() in ('true', '1') or \
                    request.GET.get('fast_mode', 'false').lower() in ('true', '1')

        # Run OCR processing & save to DB
        receipt_obj, response_payload = process_receipt(
            image_path=filepath,
            filename=saved_filename,
            save_to_db=True,
            fast_mode=fast_mode
        )

        # Save result JSON log
        result_file = os.path.join(settings.MEDIA_ROOT, 'results', f"{timestamp}_result.json")
        try:
            with open(result_file, 'w') as f:
                json.dump(response_payload, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Could not write result log: {e}")

        return JsonResponse(response_payload)

    except Exception as e:
        logger.error(f"Error scanning receipt: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Processing failed',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def scan_batch(request):
    """
    Batch receipt scanning endpoint.
    Accepts multiple image files and returns list of scanned receipts.
    """
    try:
        files = request.FILES.getlist('files') or request.FILES.getlist('file')
        if not files:
            return JsonResponse({'error': 'No files provided in "files" field'}, status=400)

        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)

        results = []
        for f in files:
            if not f.name or not is_allowed_file(f.name):
                continue

            clean_filename = get_valid_filename(f.name)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            saved_filename = f"{timestamp}_{clean_filename}"
            filepath = os.path.join(upload_dir, saved_filename)

            with open(filepath, 'wb+') as dest:
                for chunk in f.chunks():
                    dest.write(chunk)

            try:
                receipt_obj, payload = process_receipt(filepath, saved_filename, save_to_db=True)
                results.append({
                    'filename': f.name,
                    'saved_filename': saved_filename,
                    'success': True,
                    'id': receipt_obj.id if receipt_obj else None,
                    'data': payload.get('data')
                })
            except Exception as e:
                results.append({
                    'filename': f.name,
                    'success': False,
                    'error': str(e)
                })

        return JsonResponse({
            'success': True,
            'processed_count': len(results),
            'results': results
        })

    except Exception as e:
        logger.error(f"Error in batch scan: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def extract_data(request):
    """
    Extract structured data from raw OCR text string.
    Expects JSON body: {"text": "..."}
    """
    try:
        if request.content_type == 'application/json':
            body = json.loads(request.body.decode('utf-8'))
            text = body.get('text', '')
        else:
            text = request.POST.get('text', '')

        if not text:
            return JsonResponse({'error': 'No text provided'}, status=400)

        data = parse_raw_text(text)
        return JsonResponse({
            'success': True,
            'data': data
        })

    except Exception as e:
        logger.error(f"Error in extract_data view: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_receipts(request):
    """
    Get list of scanned receipts from SQLite database and disk storage.
    """
    try:
        db_receipts = Receipt.objects.all()[:100]
        receipts_data = []

        if db_receipts.exists():
            for r in db_receipts:
                receipts_data.append({
                    'id': r.id,
                    'filename': r.filename,
                    'merchant': r.merchant,
                    'date': r.date,
                    'total': r.total,
                    'tax': r.tax,
                    'confidence': r.confidence_score,
                    'status': r.status,
                    'scanner_method': r.scanner_method,
                    'items_count': r.items.count(),
                    'image_url': r.image.url if r.image else None,
                    'created': r.created_at.isoformat() if r.created_at else None,
                    'modified': r.updated_at.isoformat() if r.updated_at else None
                })
        else:
            # Fallback to scanning disk directory if database has no entries
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
            if os.path.exists(upload_dir):
                for fname in os.listdir(upload_dir):
                    if is_allowed_file(fname):
                        fpath = os.path.join(upload_dir, fname)
                        stat = os.stat(fpath)
                        receipts_data.append({
                            'filename': fname,
                            'size': stat.st_size,
                            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                        })

        return JsonResponse({
            'success': True,
            'count': len(receipts_data),
            'receipts': receipts_data
        })

    except Exception as e:
        logger.error(f"Error listing receipts: {e}", exc_info=True)
        return JsonResponse({'error': 'Failed to get receipts', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def receipt_detail(request, pk):
    """
    Get or delete a single receipt record by ID.
    """
    receipt = get_object_or_404(Receipt, pk=pk)

    if request.method == 'DELETE':
        # Delete image files if desired
        if receipt.image:
            try:
                receipt.image.delete(save=False)
            except Exception:
                pass
        receipt.delete()
        return JsonResponse({'success': True, 'message': f'Receipt {pk} deleted successfully'})

    return JsonResponse({
        'success': True,
        'receipt': receipt.to_dict()
    })


@require_http_methods(["GET"])
def test_with_samples(request):
    """
    Test endpoint that processes sample bill images from assets/bill_img/.
    """
    try:
        sample_dir = os.path.join(settings.BASE_DIR, 'assets', 'bill_img')
        if not os.path.exists(sample_dir):
            return JsonResponse({'error': 'Sample images directory not found', 'path': sample_dir}, status=404)

        sample_files = [f for f in os.listdir(sample_dir) if is_allowed_file(f)]
        if not sample_files:
            return JsonResponse({'error': 'No sample images found in assets/bill_img'}, status=404)

        results = []
        # Test first 3 samples
        for sfile in sample_files[:3]:
            try:
                fpath = os.path.join(sample_dir, sfile)
                receipt_obj, payload = process_receipt(fpath, sfile, save_to_db=True, fast_mode=True)
                results.append({
                    'sample_file': sfile,
                    'success': True,
                    'id': receipt_obj.id if receipt_obj else None,
                    'data': payload.get('data')
                })
            except Exception as e:
                results.append({
                    'sample_file': sfile,
                    'success': False,
                    'error': str(e)
                })

        return JsonResponse({
            'success': True,
            'message': 'Sample bills tested successfully',
            'count': len(results),
            'results': results
        })

    except Exception as e:
        logger.error(f"Error testing samples: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_processed_image(request, filename):
    """
    Serve processed/debug image file.
    """
    clean_name = get_valid_filename(filename)
    filepath = os.path.join(settings.MEDIA_ROOT, 'processed', clean_name)
    if os.path.exists(filepath):
        return FileResponse(open(filepath, 'rb'), content_type='image/jpeg')
    return JsonResponse({'error': 'Processed image not found'}, status=404)


def dashboard_view(request):
    """
    Interactive Web Dashboard for Receipt Scanning & OCR Management.
    """
    status = get_scanner_status()
    recent_receipts = Receipt.objects.all().prefetch_related('items')[:15]
    total_scanned = Receipt.objects.count()
    
    # Get available sample bills from assets/bill_img
    sample_dir = os.path.join(settings.BASE_DIR, 'assets', 'bill_img')
    sample_images = []
    if os.path.exists(sample_dir):
        sample_images = [f for f in os.listdir(sample_dir) if is_allowed_file(f)]

    context = {
        'status': status,
        'recent_receipts': recent_receipts,
        'total_scanned': total_scanned,
        'sample_images': sample_images,
    }
    return render(request, 'scanner/dashboard.html', context)
