import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "toxapp.settings")
application = get_wsgi_application()

from src.computation import Computation
import logging
logger = logging.getLogger(__name__)
tmpdir = 'C:/Users/Jeff Sutherland/AppData/Local/Temp'

compute = Computation(tmpdir)
fc_file = compute.calc_fold_change('dummy_config.json')
#status_module = compute.init_modules()
#status_gsa = compute.init_gsa('microarray', 'RG230-2')
fc_data = compute.map_fold_change_data('microarray', 'RG230-2', fc_file)
