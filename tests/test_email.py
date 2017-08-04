import os
import time
from django.core.wsgi import get_wsgi_application
from django.conf import settings
from django.core.mail import send_mail

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "toxapp.settings")
application = get_wsgi_application()

email_address = "drobertson@indianabiosciences.org"
message = 'Test message from test_email.py'
send_mail('Test Message', message, 'do_not_reply@indianabiosciences.org', [email_address])
