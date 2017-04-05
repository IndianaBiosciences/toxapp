from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .models import Experiment, FoldChangeResult
from django.conf import settings

import shutil
import logging
import os
import csv

logger = logging.getLogger(__name__)

@shared_task
def add(x, y):
    return x + y

@shared_task
def process_user_files(tmpdir):

    #TODO run Meeta's script to produce real output

    # temp code to put a file in our directory
    src = settings.BASE_DIR + '/data/sample_fc_data_DM_gemfibrozil_1d_7d_100mg_700_mg.txt'
    groupfc_file = tmpdir + '/groupFC.txt'
    shutil.copyfile(src, groupfc_file)

    if not os.path.isfile(groupfc_file):
        logger.error('File %s not found; fold change calculation failed', groupfc_file)

    logger.info('Reading fold change data from %s', groupfc_file)

    insert_count = 0
    with open(groupfc_file) as f:
        reader = csv.reader(f, delimiter='\t')
        next(reader, None)  # skip the header

        last_exp_id = None
        current_exp = None

        for row in reader:

            exp_id = int(row[0])

            # querying for the experiment only when it changes in the file
            if last_exp_id is None or last_exp_id != exp_id:
                try:
                    current_exp = Experiment.objects.get(pk=exp_id)
                except:
                    logger.error('Experiment id %s does not exist yet; define experiment before loading data', exp_id)

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

    logging.info('Inserted %s records from file %s', insert_count, groupfc_file)
