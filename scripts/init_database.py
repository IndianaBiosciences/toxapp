import os
import logging
import csv
import configparser
import pprint
import gzip
import time
import subprocess
import collections
from tempfile import gettempdir, NamedTemporaryFile
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "toxapp.settings")
application = get_wsgi_application()

from django.conf import settings
from tp.models import MeasurementTech, IdentifierVsGeneMap, Gene, Study, Experiment
from tp.tasks import load_measurement_tech_gene_map, load_module_scores, load_gsa_scores
from src.computation import Computation

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def setup_gene_table():

    Gene.objects.all().delete()
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


def setup_measurement_tech():

    mt = config['DEFAULT']['measurement_tech']
    md = config['DEFAULT']['measurement_detail']
    mf = os.path.join(settings.BASE_DIR, config['DEFAULT']['measurement_tech_file'])

    logger.info('Checking existence of default measurement technology: %s %s', mt, md)
    obj = MeasurementTech.objects.filter(tech=mt, tech_detail=md).first()
    mapping = IdentifierVsGeneMap.objects.filter(tech=obj).first()
    if not obj or not mapping:
        logger.info('Creating measurement technology entry from %s', mf)
        recs = load_measurement_tech_gene_map(mf)
        if not recs:
            logger.critical('Failed to load measurement tech file')
            exit(1)

        obj = MeasurementTech.objects.filter(tech=mt, tech_detail=md).first()

    return obj


def load_DM_TG_experiments():

    ef = os.path.join(settings.BASE_DIR, config['DEFAULT']['experiments_file'])
    logger.info('Loading experiments table from file %s', ef)
    updatecount = 0
    createcount = 0
    created_exps = list()
    rowcount = 0
    with open(ef) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            rowcount += 1

            # lookup the study obj on study name; so little meta data besides name that will not update if exists
            study, status = Study.objects.get_or_create(study_name=row['study_name'], source=row['source'], permission='P')
            # delete attributes that pertained to study ... don't try loading in exp
            del row['source']
            del row['study_name']
            row['study'] = study
            row['results_ready'] = False
            row['tech'] = tech_obj

            # lookup the exp obj; update if exists create otherwise
            exp = Experiment.objects.filter(id=row['id'])
            if exp:
                exp.update(**row)
                updatecount += 1
            else:
                Experiment.objects.create(**row)
                createcount += 1

            # exp is a queryset with one instance
            created_exps.append(exp.first())

    logging.info('Number of experiments created: %s, number updated: %s', createcount, updatecount)
    return created_exps


def load_fold_change_data():
    fc_loc = os.path.join(settings.BASE_DIR, config['DEFAULT']['groupfc_file_location'])
    logger.info('Loading group fold change data from dir %s', fc_loc)

    pgloader_conf = os.path.join(settings.BASE_DIR, config['DEFAULT']['pgloader_groupfc_conf'])
    cmd = '/usr/bin/pgloader ' + pgloader_conf
    outf = NamedTemporaryFile(delete=False, suffix='.txt', dir=tmpdir)
    logger.debug('Temporary file for loading fold change data is %s', outf.name)
    # set environment variable used by pgloader script
    os.environ['PG_LOADER_FILE'] = outf.name

    createcount = 0
    rowcount = 0
    files = os.listdir(fc_loc)

    for f in files:

        if f[-7:] != ".txt.gz":
            continue

        fp = os.path.join(fc_loc, f)
        logging.info('Working on file %s', fp)

        with gzip.open(fp, 'rt') as gz:

            reader = csv.reader(gz, delimiter='\t')
            # get rid of header
            next(reader, None)

            for row in reader:
                rowcount += 1
                exp_id = row.pop(0)
                probeset = row.pop(0)

                exp_obj = compute.get_exp_obj(exp_id)
                if exp_obj is None:
                    continue

                identifier_obj = compute.get_identifier_obj(exp_obj.tech, probeset)
                if identifier_obj is None:
                    continue

                createcount += 1
                row.append(str(exp_id))
                row.append(str(identifier_obj.id))
                line = '\t'.join(row) + '\n'
                outf.write(str.encode(line))

    if createcount > 10000:
        logger.info('Starting pgload of group fold change data; may take up to 30 minutes')
        logger.debug('Running command %s', cmd)
        output = subprocess.getoutput(cmd)
        logger.debug('Received output %s', output)
        logger.info('Loaded %s records out of %s in files', createcount, rowcount)
        os.remove(outf.name)
    else:
        logger.error('Did not receive at least 10000 records for load of fold change result; anything in %s?', outf.name)
        exit(1)


def score_experiments(created_exps):
    failed_scoring = collections.defaultdict(list)

    # don't keep re-initializing GSA calc; these are all RG230-2 exps
    success = compute.init_gsa(tech_obj)
    if not success:
        logger.critical('Failed to initialize GSA calc')
        exit(1)

    for exp in created_exps:

        logger.info('Scoring fold change data for experiment %s', exp.experiment_name)

        logger.debug('Retrieving mapped fold change data')
        fc_data = compute.map_fold_change_from_exp(exp)
        if fc_data is None:
            failed_scoring['fold_change_data'].append(exp.experiment_name)
            continue

        logger.debug('Calculating WGCNA results')
        module_scores = compute.score_modules(fc_data)
        if module_scores is None:
            failed_scoring['WGCNA_calc'].append(exp.experiment_name)
            continue
        else:
            status = load_module_scores(module_scores)
            if status is None:
                failed_scoring['WGCNA_load'].append(exp.experiment_name)
                continue

        logger.debug('Calculating GSA results')
        gsa_scores = compute.score_gsa(fc_data, tech_obj)
        if gsa_scores is None:
            failed_scoring['GSA_calc'].append(exp.experiment_name)
            continue
        else:
            status = load_gsa_scores(compute, gsa_scores)
            if status is None:
                failed_scoring['GSA_load'].append(exp.experiment_name)
                continue

        # set the status as ready
        exp.results_ready = True
        exp.save()

    if failed_scoring:
        logger.warning('The following experiments were not successfully scored: %s', pprint.pformat(failed_scoring))


if __name__ == '__main__':

    config_file = os.path.join(settings.BASE_DIR, 'data/toxapp.cfg')
    if not os.path.isfile(config_file):
        logger.critical('Configuration file %s not readable', config_file)
        exit(1)

    # vars used in main scope and accessible to all functs
    config = configparser.ConfigParser()
    config.read(config_file)
    tech_obj = None

    # file loading requires tmp space ... set up
    tmpdir = os.path.join(gettempdir(), '{}'.format(hash(time.time())))
    os.makedirs(tmpdir)
    compute = Computation(tmpdir)
    logger.debug('Creating temporary working directory %s', tmpdir)

    # step 1 - load gene info the Gene model
    setup_gene_table()

    # step 2) establish that RG230-2 microarray is avail, otherwise load it
    tech_obj = setup_measurement_tech()

    # step 3) load the DM/TG studies and experiments
    created_exp_list = load_DM_TG_experiments()

    # step 4) load the fold change data
    load_fold_change_data()

    # step 5 - iterate through newly added experiments and perform module / GSA scoring
    # TODO - temp for testing
    #created_exp_list = Experiment.objects.all()
    #tech_obj = created_exp_list[0].tech

    score_experiments(created_exp_list)
