"""
WSGI config for project115208 project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import sys

# Ensure parent 'django' folder is on sys.path when running under certain deployers
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DJANGO_DIR = os.path.join(BASE_DIR)
if DJANGO_DIR not in sys.path:
	sys.path.insert(0, DJANGO_DIR)

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project115208.settings')

application = get_wsgi_application()
