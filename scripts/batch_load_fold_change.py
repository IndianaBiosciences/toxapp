# Copyright 2019 Indiana Biosciences Research Institute (IBRI)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import logging
import csv
import time
import argparse
from tempfile import gettempdir, NamedTemporaryFile
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "toxapp.settings")
application = get_wsgi_application()

from django.conf import settings
from tp.models import Study, Experiment, MeasurementTech
from tp.tasks import load_module_scores, load_gsa_scores, load_correl_results, load_group_fold_change
from src.computation import Computation
from django.contrib.auth.models import User

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(asctime)s %(message)s')
logger = logging.getLogger(__name__)


def load_experiments(ef):

    assert os.path.isfile(ef)
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
            if args.user_id:
                owner = User.objects.get(id=args.user_id)
                study, status = Study.objects.get_or_create(study_name=row['study_name'], source=row['source'], permission='P', owner=owner)
            else:
                study, status = Study.objects.get_or_create(study_name=row['study_name'], source=row['source'], permission='P')
            # delete attributes that pertained to study ... don't try loading in exp
            del row['source']
            del row['study_name']
            row['study'] = study
            row['results_ready'] = False

            tech_obj = MeasurementTech.objects.get(tech_detail=row['tech_name'])
            del row['tech_name']
            row['tech'] = tech_obj

            # lookup the exp obj; update if exists create otherwise
            exp = Experiment.objects.filter(experiment_name=row['experiment_name'])
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


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Batch load pre-computed fold change data')
    parser.add_argument('--experiments_txt', dest='experiments_txt', required=True, help='Tab-delimited text file with experiments meta data')
    parser.add_argument('--groupfc_txt', dest='groupfc_txt', required=True, help='Tab-delimited text file with group fold change data')
    parser.add_argument('--user_id', type=int, dest='user_id', required=False, help='user ID for study ownership')


    args = parser.parse_args()
    if not os.path.isfile(args.experiments_txt):
        logger.error('Experiments file %s not readable', args.experiments_txt)
        exit(1)

    groupfc_file = args.groupfc_txt
    if not os.path.isfile(groupfc_file):
        logger.error('Group fold change file %s not readable', groupfc_file)
        exit(1)

    tmpdir = os.path.join(gettempdir(), '{}'.format(hash(time.time())))
    os.makedirs(tmpdir)
    compute = Computation(tmpdir)
    logger.debug('Creating temporary working directory %s', tmpdir)

    new_exps = load_experiments(args.experiments_txt)

    status = load_group_fold_change(compute, groupfc_file, use_experiment_name=False)
    if status is None:
        message = 'Step 1b Failed: Error processing and loading gene-level fold change data; no further computations performed'
        logger.error(message)
        exit(1)
    logger.info('Step 1: gene-level fold change data processed and loaded')

    logger.info('Step 2: Loading fold change results')
    fc_data = compute.map_fold_change_data(groupfc_file, use_experiment_name=False)
    if fc_data is None:
        message = 'Step 2 Failed: Error mapping fold change data to rat entrez gene IDs; no further computations performed'
        logger.error(message)
        exit(1)

    logger.info('Step 2: gene-level fold change data mapped to genes')

    # step 3 - score experiment data using WGCNA modules and load to database
    logger.info('Step 3')
    module_scores = compute.score_modules(fc_data)
    if module_scores is None:
        message = 'Step 3a Failed: Error scoring experiment results using WGCNA modules; no further computations performed'
        logger.error(message)
        exit(1)

    logger.info('Step 3a: experiment scored using WGCNA models')

    status = load_module_scores(module_scores)
    if status is None:
        message = 'Step 3b Failed: Error processing and load WGCNA module data; no further computations performed'
        logger.error(message)
        exit(1)
    logger.info('Step 3b: experiment scored using WGCNA models loaded to database')

    logger.info('Step 4')
    gsa_scores = compute.score_gsa(fc_data)
    if gsa_scores is None:
        message = 'Step 4a Failed: Error scoring experiment results using GAS; no further computations performed'
        logger.error(message)
        exit(1)
    logger.info('Step 4a: experiment scored using GSA')

    status = load_gsa_scores(gsa_scores)
    if status is None:
        message = 'Step 4b Failed: Error processing and loading GSA data; no further computations performed'
        logger.error(message)
        exit(1)
    logger.info('Step 4b: experiment scored using GSA and loaded to database')

    # step 5 - calculate near neighbors based on vector of module scores or GSA scores
    logger.info('Step 5: evaluating pairwise similarity vs. experiments using WGCNA, RegNet and PathNR')
    correl = compute.calc_exp_correl(new_exps, 'WGCNA')
    if correl is None:
        message = 'Step 5a Failed: Error calculating correlation to existing experiments using WGCNA; no further computations performed'
        logger.error(message)
        exit(1)
    logger.info('Step 5a: experiment correlation calculated using WGCNA')

    status = load_correl_results(compute, correl, 'WGCNA')
    if status is None:
        message = 'Step 5b Failed: Error loading experiment correlation for WGCNA; no further computations performed'
        logger.error(message)
        exit(1)
    logger.info('Step 5b: experiment correl using WGCNA loaded to database')

    correl = compute.calc_exp_correl(new_exps, 'RegNet')
    if correl is None:
        message = 'Failed to calculate correlation to existing experiments using RegNet; no further computations performed'
        logger.error(message)
        exit(1)
    logger.info('Step 5c: experiment correlation calculated using RegNet')

    status = load_correl_results(compute, correl, 'RegNet')
    if status is None:
        message = 'Failed to load experiment correlation for RegNet; no further computations performed'
        logger.error(message)
        exit(1)
    logger.info('Step 5d: experiment correl using RegNet loaded to database')

    correl = compute.calc_exp_correl(new_exps, 'PathNR')
    if correl is None:
        message = 'Failed to calculate correlation to existing experiments using PathNR; no further computations performed'
        logger.error(message)
        exit(1)
    logger.info('Step 5e: experiment correlation calculated using PathNR')

    status = load_correl_results(compute, correl, 'PathNR')
    if status is None:
        message = 'Failed to load experiment correlation for PathNR; no further computations performed'
        logger.error(message)
        exit(1)
    logger.info('Step 5f: experiment correl using PathNR loaded to database')

    for exp in new_exps:
        exp.results_ready = True
        exp.save()

    logger.info('Script complete')
