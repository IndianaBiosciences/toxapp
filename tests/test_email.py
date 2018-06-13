import os
import unittest
import logging
from django.core.wsgi import get_wsgi_application
from django.conf import settings
from django.core.mail import send_mail

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "toxapp.settings")
application = get_wsgi_application()

logger = logging.getLogger(__name__)


class TestEmail(unittest.TestCase):

    def test_send(self):
        email_address = settings.TEST_EMAIL
        noreply_address = settings.FROM_EMAIL
        message = 'Test message from test_email.py'
        status = send_mail('Test Message', message, noreply_address, [email_address])
        return self.assertTrue(status)
