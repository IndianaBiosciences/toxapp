"""
WSGI config for toxapp project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""

import os
import sys
from django.core.wsgi import get_wsgi_application

#os.environ.setdefault("DJANGO_SETTINGS_MODULE", "toxapp.toxapp.settings")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

APP_NAME = os.path.abspath(__file__).split('/')[-2]
settings_module = APP_NAME + '.settings'
os.environ["DJANGO_SETTINGS_MODULE"] = settings_module

application = get_wsgi_application()
