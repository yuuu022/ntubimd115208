#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    # Ensure the 'django' subdirectory is on sys.path so project package imports work
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DJANGO_DIR = os.path.join(BASE_DIR, 'django')
    if DJANGO_DIR not in sys.path:
        sys.path.insert(0, DJANGO_DIR)

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project115208.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
