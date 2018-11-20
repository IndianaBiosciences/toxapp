import os
from django.core.wsgi import get_wsgi_application
from django.conf import settings
import logging
import unittest
import tempfile
import time
import shutil
import filecmp
import pickle
import pprint
import rpy2
import rpy2.robjects
from rpy2.robjects.packages import importr

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "toxapp.settings")
application = get_wsgi_application()


logger = logging.getLogger(__name__)


class TestR(unittest.TestCase):

    def test_installed(self):
        base = importr('base')

        utils = importr('utils')

        installer = importr('BiocInstaller')
        piano = importr('piano')

        pi = rpy2.robjects.r['pi']
        print(pi)
        r_version = str(rpy2.__version__)
        r_version = r_version.split(".")
        if(int(r_version[0]) == 3 and int(r_version[1]) == 5 ):
            print(r_version)
        else:
            logger.warning("The R Version installed currently differs from the recomended 3.5.x, you are running: " + str(rpy2.__version__))




if __name__ == '__main__':
    unittest.main()