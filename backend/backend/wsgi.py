"""
WSGI configuration.

It exposes the WSGI callable as a module-level variable named ``application``.

https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
application = get_wsgi_application()

application = WhiteNoise(application, autorefresh=True)  # helps us serve static files when DEBUG=False
