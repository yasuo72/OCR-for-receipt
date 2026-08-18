"""
WSGI config for receipt_scanner_project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'receipt_scanner_project.settings')

application = get_wsgi_application()
