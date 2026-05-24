"""
ASGI config for project115208 project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os
import sys

# Ensure parent 'django' folder is on sys.path for ASGI servers
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DJANGO_DIR = os.path.join(BASE_DIR)
if DJANGO_DIR not in sys.path:
	sys.path.insert(0, DJANGO_DIR)

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project115208.settings')

application = get_asgi_application()
