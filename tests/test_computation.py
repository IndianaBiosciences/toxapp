import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "toxapp.settings")
application = get_wsgi_application()

from django.conf import settings
from src.computation import Computation
from tp.tasks import load_gsa_scores
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

tmpdir = 'C:\\Users\Jeff Sutherland\AppData\Local\Temp\.7530676274658962134'

logger.debug("temp directory is %s", tmpdir)

compute = Computation(tmpdir)
fc_file = compute.calc_fold_change('dummy_config.json')
fc_data = compute.map_fold_change_data(fc_file)

module_scores = compute.score_modules(fc_data)
with open('test_module.txt', 'w') as f:
    for r in module_scores:
        txt = "\t".join([str(r['exp_id']), r['module'], str(r['score'])])
        txt += "\n"
        f.write(txt)

gsa_scores = compute.score_gsa(fc_data)
with open('test_gsa.txt', 'w') as f:
    for r in gsa_scores:
         txt = "\t".join([str(r['exp_id']), r['geneset'], str(r['score']), str(r['log10_p_BH'])])
         txt += "\n"
         f.write(txt)

