"""
Development settings — imports everything from base and adds dev-only stuff.
"""

from .base import *  # noqa

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '.vercel.app', 'style-hub-amber.vercel.app', '*']

# Django Debug Toolbar
INSTALLED_APPS += ['debug_toolbar']

MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

INTERNAL_IPS = ['127.0.0.1']

# Use local file storage instead of Cloudinary during dev (optional)
# Uncomment the line below if you don't want to hit Cloudinary on every upload
# DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
# MEDIA_ROOT = BASE_DIR / 'media'
