from django.urls import path
from scanner import views

urlpatterns = [
    # Web Dashboard
    path('', views.dashboard_view, name='dashboard'),
    path('dashboard/', views.dashboard_view, name='dashboard_alt'),

    # Core REST API Endpoints
    path('api/health', views.health_check, name='api_health'),
    path('api/info', views.api_info, name='api_info'),
    path('api/scan', views.scan_receipt, name='api_scan'),
    path('api/scan/batch', views.scan_batch, name='api_scan_batch'),
    path('api/extract', views.extract_data, name='api_extract'),
    path('api/receipts', views.get_receipts, name='api_receipts'),
    path('api/receipts/<int:pk>/', views.receipt_detail, name='api_receipt_detail'),
    path('api/test', views.test_with_samples, name='api_test'),
    path('api/processed/<str:filename>', views.get_processed_image, name='api_processed_image'),
]
