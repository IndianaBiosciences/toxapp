import os
from django.core.wsgi import get_wsgi_application
from django.conf import settings
from src.computation import Computation
import tempfile
import logging
import pprint
from tp.tasks import process_user_files

pp = pprint.PrettyPrinter(indent=4)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "toxapp.settings")
application = get_wsgi_application()

logger = logging.getLogger(__name__)

#
# Set up necessary parameters
#
log_settings = settings.LOGGING
logfile = log_settings["handlers"]["file"]["filename"]
logger.debug("Log file is %s", logfile)

logger.debug("temp directory is %s", tmpdir)

compute = Computation(tmpdir)
fc_file = compute.calc_fold_change('dummy_config.json')
status_module = compute.init_modules()
status_gsa = compute.init_gsa('microarray', 'RG230-2')

fc_data = compute.map_fold_change_data('microarray', 'RG230-2', fc_file)

module_scores = compute.score_modules(fc_data)
# with open('test_module.txt', 'w') as f:
#     for r in module_scores:
#         txt = "\t".join([str(r['exp_id']), r['module'], str(r['score'])])
#         txt += "\n"
#         f.write(txt)

gsa_scores = compute.score_gsa(fc_data)
# with open('test_gsa.txt', 'w') as f:
#     for r in gsa_scores:
#          txt = "\t".join([str(r['exp_id']), r['set_id'], str(r['score'])])
#          txt += "\n"
#          f.write(txt)