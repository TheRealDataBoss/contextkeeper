"""WSGI config for contextkeeper SaaS."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "contextkeeper_saas.settings.production")

application = get_wsgi_application()
