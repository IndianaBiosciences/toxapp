import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "toxapp.settings")
application = get_wsgi_application()

from tp.tasks import process_user_files

tmpdir = '/tmp/2278365665375990855'
config = '/tmp/2278365665375990855/computation_data.json'
email = 'drobertson@indianabiosciences.com'

process_user_files(tmpdir, config, email)
