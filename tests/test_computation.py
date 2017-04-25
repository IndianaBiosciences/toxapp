import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "toxapp.settings")
application = get_wsgi_application()

from src.computation import Computation
import logging
logger = logging.getLogger(__name__)
tmpdir = 'C:/Users/Jeff Sutherland/AppData/Local/Temp'

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