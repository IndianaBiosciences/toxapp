import os
import logging
import pprint
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "toxapp.settings")
application = get_wsgi_application()

from django.conf import settings
from src.computation import Computation
from tp.models import Experiment

logger = logging.getLogger(__name__)
pp = pprint.PrettyPrinter(indent=4)

#
# Set up necessary parameters
#
log_settings = settings.LOGGING
logfile = log_settings['handlers']['file']['filename']
logger.debug('Log file is %s', logfile)

# TODO - need to archive content of ready-to-calc directory for a sample exp and use that
tmpdir = '/tmp/test'

logger.debug('temp directory is %s', tmpdir)

compute = Computation(tmpdir)

fc_file = compute.calc_fold_change('computation_data.json')
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
         txt = "\t".join([str(r['exp_id']), r['geneset'], str(r['score']), str(r['p_bh'])])
         txt += "\n"
         f.write(txt)

# must have module score data loaded in DB
qry_exps = Experiment.objects.filter(id__in=[9067, 9070])
correl = compute.calc_exp_correl(qry_exps, 'WGCNA')
