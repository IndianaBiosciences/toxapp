import os
from django.core.wsgi import get_wsgi_application
from tp.tasks import process_user_files

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "toxapp.settings")
application = get_wsgi_application()


tmpdir = '/tmp/.8104953327121739898'
config = '/tmp/.8104953327121739898/computation_data.json'
email = 'sutherland.jeffrey.j@gmail.com'

process_user_files(tmpdir, config, email)
