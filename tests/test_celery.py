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
import logging
import time
import unittest
import uuid
import tempfile
import shutil
from django.core.wsgi import get_wsgi_application
from django.conf import settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "toxapp.settings")
application = get_wsgi_application()

from django.contrib.auth.models import User
from tp.tasks import add, make_leiden_csv, process_user_files
from tp.models import Experiment

logger = logging.getLogger(__name__)

# NOTE - the delays below are appropriate for a test system with no other tasks running
# tests may fail is running on a server with other celery tasks running and this job waiting in the queue


class TestCelery(unittest.TestCase):

    def test_add(self):
        res = add.delay(5, 2)
        time.sleep(5)
        status = res.ready()
        result = res.get(timeout=1)
        logger.info('Obtained celery status %s and result of %s', status, result)
        return self.assertEqual(result, 7)

    def test_make_leiden_csv(self):

        loc = os.path.join(settings.COMPUTATION['url_dir'], 'leiden_exports')
        if not os.path.isdir(loc):
            os.makedirs(loc)

        code = uuid.uuid4().hex
        localf = code + '.csv'
        fullfile = os.path.join(loc, localf)

        # get the first experiment
        exp = Experiment.objects.first()
        res = make_leiden_csv.delay(fullfile, [exp.id])

        time.sleep(40)
        status = res.ready()
        result = res.get(timeout=1)
        logger.info('Obtained celery status %s', status)
        return self.assertTrue(status) and self.assertTrue(result)

    def test_process_user_files(self):

        tmpdir = os.path.join(tempfile.gettempdir(), '{}'.format(hash(time.time())))
        sourcedir = os.path.join(settings.BASE_DIR, 'tests/test_data/')
        if not os.path.exists(sourcedir):
            logging.error('Test data directory %s is not readable', sourcedir)
            exit(1)

        shutil.copytree(sourcedir, tmpdir)
        logger.debug('temp directory is %s', tmpdir)
        user = User.objects.get(username='admin')
        config_file = os.path.join(tmpdir, 'computation_data.json')

        logger.debug('Running process_user_files')
        res = process_user_files.delay(tmpdir, config_file, user.email, True)
        time.sleep(20)
        status = res.ready()
        message = res.get(timeout=1)

        logger.info('Obtained celery status %s and message %s', status, message)
        return self.assertTrue(status) and self.assertTrue(message)


if __name__ == '__main__':
    unittest.main()

