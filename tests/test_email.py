# Copyright 2019 Indiana Biosciences Research Institute (IBRI)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
