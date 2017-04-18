from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .models import Experiment, FoldChangeResult, MeasurementTech, IdentifierVsGeneMap
from django.conf import settings
from django.core.mail import send_mail
from src.computation import Computation

import shutil
import logging
import os
import csv

logger = logging.getLogger(__name__)

@shared_task
def add(x, y):
    return x + y

@shared_task
def process_user_files(tmpdir, config, email):

    # step1 - calculate group fold change and load data to the database

    compute = Computation(tmpdir)
    groupfc_file = compute.calc_fold_change(config)

    if groupfc_file is None or not os.path.isfile(groupfc_file):
        message = 'Computation script failed to calculate fold change data'
        logger.error(message)
        send_mail('IBRI tox portal results ready', message, 'do_not_reply@indianabiosciences.org', [email])
        return

    status = load_group_fold_change(groupfc_file)

    if status is None:
        message = 'Failed to process and load gene-level fold change data; no further computations performed'
        logger.error(message)
        send_mail('IBRI tox portal results ready', message, 'do_not_reply@indianabiosciences.org', [email])
        return



def load_group_fold_change(groupfc_file):

    logger.info('Reading fold change data from %s', groupfc_file)

    insert_count = 0
    with open(groupfc_file) as f:
        reader = csv.reader(f, delimiter='\t')
        next(reader, None)  # skip the header

        # build up a dictionary mapping experiment id vs. the corresponding db object
        last_exp_id = None
        expid_vs_obj = dict()
        tried_expid = dict()

        for row in reader:

            exp_id = int(row[0])
            #TODO - temp adjustment to match what's in DB
            exp_id += 4

            # if we don't yet have the map from id to obj and the exp_id has changed, look it up
            if tried_expid.get(exp_id, None) is None and (last_exp_id is None or last_exp_id != exp_id):

                # track that we tried retrieving an experiment object to avoid multiple lookups
                tried_expid[exp_id] = 1

                try:
                    exp_obj = Experiment.objects.get(pk=exp_id)
                    # store the object in dictionary in case the file is not sorted with rows ordered by exp_id
                    expid_vs_obj[exp_id] = exp_obj
                except:
                    logger.error('Experiment id %s does not exist yet; define experiment before loading data', exp_id)

            last_exp_id = exp_id

            current_exp = expid_vs_obj.get(exp_id, None)
            if current_exp is None:
                continue

            FoldChangeResult.objects.create(
                experiment=current_exp,
                gene_identifier=row[1],
                log2_fc=row[2],
                n_trt=row[3],
                n_ctl=row[4],
                expression_ctl=row[5],
                log10_p=row[6],
                log10_p_bh=row[7]
            )
            insert_count += 1

    if insert_count == 0:
        logger.error('Failed to load any records from file')
        return None

    logging.info('Inserted %s records from file %s', insert_count, groupfc_file)
    return 1

def load_measurement_tech_gene_map(file):

    logger.info('Loading mapping of identifiers to genes for file %s', file)
    required_cols = ['TECH', 'TECH_DETAIL', 'IDENTIFIER', 'RAT_ENTREZ_GENE']

    #TODO - need a warning that existing data is overwritten
    rownum = 0
    insert_count = 0
    tech_vs_obj = dict()
    with open(file) as f:
        dialect = csv.Sniffer().sniff(f.read(1024))
        f.seek(0)
        reader = csv.DictReader(f, dialect=dialect)
        for row in reader:
            rownum = rownum+1
            tech = row['TECH']
            tech_detail = row['TECH_DETAIL']
            for col in required_cols:
                if row[col]:
                    pass
                else:
                    logger.error("Missing value of %s on row %s of file %s", col, rownum, file)
                    return None

            thistech = tech + "-" + tech_detail

            tech_obj = tech_vs_obj.get(thistech, None)
            # first time this measurement tech encountered in file - either create or retrieve apprpriate obj
            if tech_obj is None:
                tech_obj = query_or_create_measurement_tech(tech, tech_detail)
                tech_vs_obj[thistech] = tech_obj

            IdentifierVsGeneMap.objects.create(
                tech=tech_obj,
                gene_identifier=row['IDENTIFIER'],
                rat_entrez_gene=row['RAT_ENTREZ_GENE']
            )
            insert_count += 1

    logging.info('Inserted %s records from file %s', insert_count, file)
    return insert_count

def query_or_create_measurement_tech(tech, tech_detail):

    logger.debug('Querying measurement tech on %s and %s', tech, tech_detail)

    tech_obj = MeasurementTech.objects.filter(tech=tech, tech_detail=tech_detail).first()

    if tech_obj is None:

        logger.info('Measurement tech entry for %s-%s does not exist; creating', tech, tech_detail)
        tech_obj = MeasurementTech.objects.create(
                tech=tech,
                tech_detail=tech_detail
        )

    return tech_obj