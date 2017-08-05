import os
import time
from django.core.wsgi import get_wsgi_application
from django.conf import settings
from tp import utils

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "toxapp.settings")
application = get_wsgi_application()

utils.get_user_qc_urls('drobertson')