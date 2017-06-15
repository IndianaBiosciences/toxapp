import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "toxapp.settings")
application = get_wsgi_application()

from django.conf import settings
from src.computation import Computation
from tp.tasks import load_group_fold_change
import tempfile
import logging
import pprint

logger = logging.getLogger(__name__)
pp = pprint.PrettyPrinter(indent=4)

#
# Set up necessary parameters
#
log_settings = settings.LOGGING
logfile = log_settings["handlers"]["file"]["filename"]
logger.debug("Log file is %s", logfile)

tmpdir  = '/var/folders/jg/96y1wjb16774h99s835sybt40000gq/T/1669202138728841260'
fc_file = os.path.join(tmpdir, "groupFC.txt")

logger.debug("fc_file is %s", fc_file)

compute = Computation(tmpdir)
load_group_fold_change(compute, fc_file)
