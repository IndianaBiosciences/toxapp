from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .models import Experiment, FoldChangeResult
from django.conf import settings
from django.core.mail import send_mail
from src.Computation import Computation

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

    compute = Computation()
    groupfc_file = compute.calc_fold_change(tmpdir, config)

    #TODO remove once meeta script running
    src = settings.BASE_DIR + '/data/sample_fc_data_DM_gemfibrozil_1d_7d_100mg_700_mg.txt'
    shutil.copyfile(src, groupfc_file)

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
                experiment = current_exp,
                gene_identifier = row[1],
                log2_fc = row[2],
                n_trt = row[3],
                n_ctl = row[4],
                expression_ctl = row[5],
                log10_p = row[6],
                log10_p_bh = row[7]
            )
            insert_count += 1

    if insert_count == 0:
        logger.error('Failed to load any records from file')
        return None

    logging.info('Inserted %s records from file %s', insert_count, groupfc_file)
    return 1

