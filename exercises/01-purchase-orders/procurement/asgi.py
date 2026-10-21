"""ASGI config for the procurement project."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "procurement.settings")

application = get_asgi_application()
