import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "toxapp.settings")
application = get_wsgi_application()

from src.computation import Computation
import logging
logger = logging.getLogger(__name__)
tmpdir = 'C:\tmp'

compute = Computation(tmpdir)
status_module = compute.init_modules()
status_gsa = compute.init_gsa('microarray', 'RG230-2')
