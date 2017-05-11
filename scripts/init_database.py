import os
import logging
import csv
import configparser
import pprint
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "toxapp.settings")
application = get_wsgi_application()

from django.conf import settings
from tp.models import MeasurementTech, IdentifierVsGeneMap, Gene, Study, Experiment
from tp.tasks import load_measurement_tech_gene_map

logger = logging.getLogger(__name__)

config_file = os.path.join(settings.BASE_DIR, 'data/toxapp.cfg')
if not os.path.isfile(config_file):
    logger.critical('Configuration file %s not readable', config_file)
    exit(1)


config = configparser.ConfigParser()
config.read(config_file)

# step 1) set-up the master gene table
gene = Gene.objects.all().delete()
gf = os.path.join(settings.BASE_DIR, config['DEFAULT']['gene_file'])
logger.info('Loading orthology gene table from file %s', gf)
required_cols = ['rat_entrez_gene', 'rat_gene_symbol']
createcount = 0
rowcount = 0
with open(gf) as f:
    dialect = csv.Sniffer().sniff(f.read(1024))
    f.seek(0)
    reader = csv.DictReader(f, dialect=dialect)
    for row in reader:
        rowcount += 1
        for col in required_cols:
            if row.get(col, None) is not None:
                pass
            else:
                logger.critical('Missing value of %s on row %s of file %s', col, rowcount, gf)
                exit(1)

        # database needs a None for blank fields
        for col in row:
            if row[col] == '':
                row[col] = None

        Gene.objects.create(**row)
        createcount += 1

logging.info('Number of genes created: %s', createcount)


# step 2) establish that RG230-2 microarray is avail, otherwise load it
mt = config['DEFAULT']['measurement_tech']
md = config['DEFAULT']['measurement_detail']
mf = os.path.join(settings.BASE_DIR, config['DEFAULT']['measurement_tech_file'])

logger.info('Checking existence of default measurement technology: %s %s', mt, md )
tech_obj = MeasurementTech.objects.filter(tech=mt, tech_detail=md).first()
mapping = IdentifierVsGeneMap.objects.filter(tech=tech_obj).first()
if not tech_obj or not mapping:
    logger.info('Creating measurement technology entry from %s', mf)
    recs = load_measurement_tech_gene_map(mf)
    if not recs:
        logger.critical('Failed to load measurement tech file')
        exit(1)

# step 3) load the DM/TG studies and experiments
ef = os.path.join(settings.BASE_DIR, config['DEFAULT']['experiments_file'])
logger.info('Loading experiments table from file %s', ef)
updatecount = 0
createcount = 0
rowcount = 0
with open(ef) as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        rowcount += 1

        # lookup the study obj on study name; so little meta data besides name that will not update if exists
        study,status = Study.objects.get_or_create(study_name=row['study_name'], source=row['source'], permission='P')
        # delete attributes that pertained to study ... don't try loading in exp
        del row['source']
        del row['study_name']
        row['study'] = study
        row['results_ready'] = True
        row['tech'] = tech_obj

        # lookup the exp obj; update if exists create otherwise
        exp = Experiment.objects.filter(id=row['id'])
        if exp:
            exp.update(**row)
            updatecount += 1
        else:
            Experiment.objects.create(**row)
            createcount += 1

logging.info('Number of experiments created: %s, number of genes updated: %s', createcount, updatecount)
