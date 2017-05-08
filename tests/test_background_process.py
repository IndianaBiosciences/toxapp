import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "toxapp.settings")
application = get_wsgi_application()

from tp.tasks import process_user_files

tmpdir = '/var/folders/jg/96y1wjb16774h99s835sybt40000gq/T/222092004455828672'
config = '/var/folders/jg/96y1wjb16774h99s835sybt40000gq/T/222092004455828672/computation_data.json'
email = 'drobertson@indianabiosciences.com'

process_user_files(tmpdir, config, email)
