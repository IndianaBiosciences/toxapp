import os
import logging
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "toxapp.settings")
application = get_wsgi_application()

from django.conf import settings
from src.computation import Computation
from tp.models import ToxPhenotype, GeneSets

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# don't need a tmpdir for this script
compute = Computation('foo')

genesets = [
    'BIOCARTA_P53_PATHWAY',
    'DM:liver:205',
    'KEGG_GLUTATHIONE_METABOLISM',
    'DM:liver:42m',
    'BIOCARTA_NUCLEARRS_PATHWAY',
    'DM:liver:206',
    'GO:0009062',
    'DM:liver:17m',
    'REACTOME_XENOBIOTICS',
    'DM:liver:108',
    'GO:0070301',
    'DM:liver:18m',
    'Bioset 5: Rat Genotoxicity Biomarker',
    'Bioset 3: Rat CAR Biomarker',
    'Bioset 4: Rat ER Biomarker',
    'Bioset 6: Rat PPARalpha Biomarker',
    'Bioset 2: Rat AhR Biomarker',
    'Bioset 1: Cytotox biomarker',
]

tox = ToxPhenotype.objects.get(name='hepatic tumorigen')

stats = ['mean_pos', 'mean_neg', 'n_pos', 'n_neg', 'effect_size', 'p_single', 'coef', 'p_adj']
header = ['geneset_name', 'time'] + stats
print('\t'.join(header))

for time in [1, 4]:
    for geneset_nm in genesets:

        geneset = GeneSets.objects.get(name=geneset_nm)
        table = compute.make_score_vs_tox_association_table(geneset, tox, time=time)
        results = compute.run_score_vs_tox_association(table)

        row = [geneset_nm, str(time)]
        for stat in stats:
            row.append(str(results[stat]))

        print('\t'.join(row))

