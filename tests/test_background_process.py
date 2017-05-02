import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "toxapp.settings")
application = get_wsgi_application()

from tp.tasks import process_user_files

tmpdir = 'C:\\Users\Jeff Sutherland\AppData\Local\Temp\.7530676274658962134'
config = 'C:\\Users\Jeff Sutherland\AppData\Local\Temp\.7530676274658962134\computation_data.json'
email = 'sutherland.jeffrey.j@gmail.com'

process_user_files(tmpdir, config, email)
