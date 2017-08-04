from __future__ import absolute_import, unicode_literals
from celery import shared_task, current_task
from .models import Experiment, FoldChangeResult, MeasurementTech, Gene, IdentifierVsGeneMap, ModuleScores, GeneSets,\
    GSAScores, ExperimentCorrelation
from django.conf import settings
from django.core.mail import send_mail
from src.computation import Computation

import pprint
import logging
import os
import csv
import operator

logger = logging.getLogger(__name__)

@shared_task
def add(x, y):
    return x + y


@shared_task
def process_user_files(tmpdir, config_file, email):

    from_email = 'CTox <dhrobertson@runbox.com>'  #TODO -- Move to Settings

    # step1 - calculate group fold change and load data to the database
    logger.info('Step 1')
    compute = Computation(tmpdir)
    groupfc_file = compute.calc_fold_change(config_file)

    if groupfc_file is None or not os.path.isfile(groupfc_file):
        message = 'Computation script failed to calculate fold change data'
        logger.error(message)
        send_mail('IBRI tox portal computation failed', message, from_email, [email])
        return
    logger.info('Step 1: gene-level fold change file created: %s', groupfc_file)

    status = load_group_fold_change(compute, groupfc_file)
    if status is None:
        message = 'Failed to process and load gene-level fold change data; no further computations performed'
        logger.error(message)
        send_mail('IBRI tox portal computation failed', message, from_email, [email])
        return
    logger.info('Step 1: gene-level fold change data processed and loaded')

    # step 2 - map data for this measurement technology to rat entrez gene IDs
    logger.info('Step 2')
    fc_data = compute.map_fold_change_data(groupfc_file)
    if fc_data is None:
        message = 'Failed to map fold change data to rat entrez gene IDs; no further computations performed'
        logger.error(message)
        send_mail('IBRI tox portal computation failed', message, from_email, [email])
        return
    logger.info('Step 2: gene-level fold change data mapped to genes')

    # step 3 - score experiment data using WGCNA modules and load to database
    logger.info('Step 3')
    module_scores = compute.score_modules(fc_data)
    if module_scores is None:
        message = 'Failed to score experiment results using WGCNA modules; no further computations performed'
        logger.error(message)
        send_mail('IBRI tox portal computation failed', message, from_email, [email])
        return
    logger.info('Step 3a: experiment scored using WGCNA models')

    status = load_module_scores(module_scores)
    if status is None:
        message = 'Failed to process and load WGCNA module data; no further computations performed'
        logger.error(message)
        send_mail('IBRI tox portal computation failed', message, from_email, [email])
        return
    logger.info('Step 3b: experiment scored using WGCNA models loaded to database')

    # step 4 - score experiment data using GSA
    logger.info('Step 4')
    gsa_scores = compute.score_gsa(fc_data)
    if gsa_scores is None:
        message = 'Failed to score experiment results using gene set analysis; no further computations performed'
        logger.error(message)
        send_mail('IBRI tox portal computation failed', message, from_email, [email])
        return
    logger.info('Step 4a: experiment scored using GSA')

    status = load_gsa_scores(compute, gsa_scores)
    if status is None:
        message = 'Failed to process and load gene set analysis data; no further computations performed'
        logger.error(message)
        send_mail('IBRI tox portal computation failed', message, from_email, [email])
        return
    logger.info('Step 4b: experiment scored using GSA and loaded to database')

    new_exps = Experiment.objects.filter(id__in=list(fc_data.keys()))

    # TODO -- moved ahead at the moment so it will show partial results in case of failing at later
    # stages. Need to move this back to end when all debugged
    # set status on experiments as ready for analysis
    for exp in new_exps:
        exp.results_ready = True
        exp.save()

    # step 5 - calculate near neighbors based on vector of module scores or GSA scores
    logger.info('Step 5: evaluating pairwise similarity vs. experiments  using WGCNA and RegNet')
    correl = compute.calc_exp_correl(new_exps, 'WGCNA')
    if correl is None:
        message = 'Failed to calculate correlation to existing experiments using WGCNA; no further computations performed'
        logger.error(message)
        send_mail('IBRI tox portal computation failed', message, from_email, [email])
        return
    logger.info('Step 5a: experiment correlation calculated using WGCNA and loaded to database')

    status = load_correl_results(compute, correl, 'WGCNA')
    if status is None:
        message = 'Failed to load experiment correlation for WGCNA; no further computations performed'
        logger.error(message)
        send_mail('IBRI tox portal computation failed', message, from_email, [email])
        return
    logger.info('Step 5b: experiment correl using WGCNA loaded to database')

    correl = compute.calc_exp_correl(new_exps, 'RegNet')
    if correl is None:
        message = 'Failed to calculate correlation to existing experiments using RegNet; no further computations performed'
        logger.error(message)
        send_mail('IBRI tox portal computation failed', message, from_email, [email])
        return
    logger.info('Step 5c: experiment correlation calculated using RegNet and loaded to database')

    status = load_correl_results(compute, correl, 'RegNet')
    if status is None:
        message = 'Failed to load experiment correlation for RegNet; no further computations performed'
        logger.error(message)
        send_mail('IBRI tox portal computation failed', message, from_email, [email])
        return
    logger.info('Step 5d: experiment correl using RegNet loaded to database')

    message = 'Final: Uploaded expression data is ready for analysis'
    logger.info(message)
    send_mail('IBRI tox portal computation complete', message, from_email, [email])


def load_group_fold_change(compute, groupfc_file):

    logger.info('Reading fold change data from %s', groupfc_file)

    insert_count = 0
    rownum = 0
    identifier_lookup_fail = dict()
    with open(groupfc_file) as f:
        reader = csv.reader(f, delimiter='\t')
        next(reader, None)  # skip the header

        checked_exist = dict()
        for row in reader:

            rownum += 1
            exp_id = int(row[0])
            # use the method in compute object to avoid repeatedly checking same ID
            exp_obj = compute.get_exp_obj(exp_id)
            if exp_obj is None:
                continue

            identifier_obj = compute.get_identifier_obj(exp_obj.tech, row[1])
            if identifier_obj is None:
                identifier_lookup_fail[row[1]] = 1
                continue

            # query once for existence of results for this experiment and delete all if found
            if checked_exist.get(exp_id, None) is None:

                checked_exist[exp_id] = 1
                prev_results = FoldChangeResult.objects.filter(experiment=exp_obj).all()
                if prev_results is not None and len(prev_results) > 0:
                    logger.warning('Experiment %s already had fold change results loaded; deleting old results', exp_id)
                    prev_results.delete()

            FoldChangeResult.objects.create(
                experiment=exp_obj,
                gene_identifier=identifier_obj,
                log2_fc=row[2],
                n_trt=row[3],
                n_ctl=row[4],
                expression_ctl=row[5],
                p=row[6],
                p_bh=row[7]
            )
            insert_count += 1

    if insert_count == 0:
        logger.error('Failed to load any records from file')
        return None

    if identifier_lookup_fail:
        n_fails = len(identifier_lookup_fail)
        ids = list(identifier_lookup_fail.keys())[0:10]
        id_str = ','.join(ids)
        logger.warning('A total of %s identifiers in file %s are not entrez gene IDs in database and ignored; the first 10 are: %s', n_fails, groupfc_file, id_str)
        if n_fails > int(rownum/2):
            logger.critical('More than 50% of identifiers in file (%s) lack a corresponding identifier in database; Probable error ... exiting', n_fails)
            exit(0)

    logging.info('Inserted %s out of %s records from file %s', insert_count, rownum, groupfc_file)
    return 1


def load_measurement_tech_gene_map(file):

    logger.info('Loading mapping of identifiers to genes for file %s', file)
    required_cols = ['TECH', 'TECH_DETAIL', 'SPECIES', 'IDENTIFIER', 'SPECIES_ENTREZ_GENE']

    rownum = 0
    insert_count = 0
    tech_vs_obj = dict()
    gene_lookup_fail = dict()

    with open(file) as f:
        dialect = csv.Sniffer().sniff(f.read(1024))
        f.seek(0)
        reader = csv.DictReader(f, dialect=dialect)
        for row in reader:
            rownum = rownum+1
            tech = row['TECH']
            tech_detail = row['TECH_DETAIL']
            for col in required_cols:
                if row.get(col, None) is not None:
                    pass
                else:
                    logger.error("Missing value of %s on row %s of file %s", col, rownum, file)
                    return None

            if row['SPECIES'].lower() not in ['rat', 'mouse', 'human']:
                logger.error('Species obtained is %s; only rat, mouse and human are supported', row['SPECIES'])
                return None

            thistech = tech + "-" + tech_detail
            tech_obj = tech_vs_obj.get(thistech, None)

            # first time this measurement tech encountered in file - either create or retrieve apprpriate obj
            if tech_obj is None:
                tech_obj = query_or_create_measurement_tech(tech, tech_detail)
                tech_vs_obj[thistech] = tech_obj

                prev_map = IdentifierVsGeneMap.objects.filter(tech=tech_obj).all()
                if prev_map is not None and len(prev_map) > 0:
                    logger.warning('Deleting existing identifer vs. gene map for measurement tech %s', tech_obj)
                    prev_map.delete()

            # lookup the gene obj ...don't store these as should be seen only once per file
            if row['SPECIES'].lower() == 'rat':
                gene_obj = Gene.objects.filter(rat_entrez_gene=row['SPECIES_ENTREZ_GENE']).first()
                if gene_obj is None:
                    gene_lookup_fail[row['SPECIES_ENTREZ_GENE']] = 1
            elif row['SPECIES'].lower() == 'mouse':
                gene_obj = Gene.objects.filter(mouse_entrez_gene=row['SPECIES_ENTREZ_GENE']).first()
                if gene_obj is None:
                    gene_lookup_fail[row['SPECIES_ENTREZ_GENE']] = 1
            elif row['SPECIES'].lower() == 'human':
                gene_obj = Gene.objects.filter(human_entrez_gene=row['SPECIES_ENTREZ_GENE']).first()
                if gene_obj is None:
                    gene_lookup_fail[row['SPECIES_ENTREZ_GENE']] = 1
            else:
                raise NotImplementedError

            if gene_obj is None:
                continue

            IdentifierVsGeneMap.objects.create(
                tech=tech_obj,
                gene_identifier=row['IDENTIFIER'],
                gene=gene_obj
            )
            insert_count += 1

    logging.info('Inserted %s out of %s records from file %s', insert_count, rownum, file)

    if gene_lookup_fail:
        n_fails = len(gene_lookup_fail)
        ids = list(gene_lookup_fail.keys())[0:10]
        id_str = ",".join(ids)
        logger.warning('A total of %s identifiers in file %s are not entrez gene IDs in database and ignored; the first 10 are: %s', n_fails, file, id_str)
        if n_fails > int(rownum/2):
            logger.critical('More than 50% of identifiers in file (%s) lack a corresponding entrez gene ID in database; Probable error ... exiting', n_fails)
            exit(0)

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


def load_module_scores(module_scores):

    logger.info('Loading computed module scores into database')

    insert_count_scores = 0
    insert_count_modules = 0

    # compile a list of all modules for which results will be loaded
    load_modules = dict()
    for r in module_scores:
        load_modules[r['module']] = None

    for s in load_modules:

        try:
            geneset_obj = GeneSets.objects.get(name=s)
        except:
            geneset_obj = GeneSets.objects.create(
                name=s,
                type='liver_module',
                desc='',
                source='WGCNA',
                core_set=True
            )
            insert_count_modules += 1

        load_modules[s] = geneset_obj

    checked_exist = dict()
    for r in module_scores:

        # query once for existence of results for this experiment and delete all if found
        if checked_exist.get(r['exp_id'], None) is None:

            checked_exist[r['exp_id']] = 1
            prev_results = ModuleScores.objects.filter(experiment=r['exp_obj']).all()
            if prev_results is not None and len(prev_results) > 0:
                logger.warning('Experiment %s already had module results loaded; deleting old results', r['exp_id'])
                prev_results.delete()

        ModuleScores.objects.create(
            experiment=r['exp_obj'],
            module=load_modules[r['module']],
            score=r['score']
        )
        insert_count_scores += 1

    if insert_count_scores == 0:
        logging.error('Failed to insert any module scores into database')
        return None

    logging.info('Inserted %s new module scores', insert_count_scores)
    return 1


def load_gsa_scores(compute_obj, gsa_scores):

    logger.info('Loading computed GSA scores into database')
    assert isinstance(compute_obj, Computation)

    insert_count_geneset = 0
    insert_count_scores = 0

    # compile a list of all gene sets for which results will be loaded
    load_gene_sets = dict()
    for r in gsa_scores:
        load_gene_sets[r['geneset']] = None

    info = compute_obj.gsa_info
    if info is None:
        logger.error('Did not receive a compute_obj on which init_gsa was called')
        return None

    for s in load_gene_sets:

        if info.get(s, None) is None:
            logger.error('Have no meta data for gene set %s in compute obj; skipping', s)
            continue

        try:
            geneset_obj = GeneSets.objects.get(name=s)
        except:
            geneset_obj = GeneSets.objects.create(
                name=s,
                type=info[s]['type'],
                desc=info[s]['desc'],
                source=info[s]['source'],
                core_set=info[s]['core_set']
            )
            insert_count_geneset += 1

        load_gene_sets[s] = geneset_obj

    checked_exist = dict()
    for r in gsa_scores:

        if load_gene_sets.get(r['geneset'], None) is None:
            # already warned in creating geneset
            continue

        # query once for existence of results for this experiment and delete all if found
        if checked_exist.get(r['exp_id'], None) is None:

            checked_exist[r['exp_id']] = 1
            prev_results = GSAScores.objects.filter(experiment=r['exp_obj']).all()
            if prev_results is not None and len(prev_results) > 0:
                logger.warning('Experiment %s already had GSA results loaded; deleting old results', r['exp_id'])
                prev_results.delete()

        GSAScores.objects.create(
            experiment=r['exp_obj'],
            geneset=load_gene_sets[r['geneset']],
            score=r['score'],
            p_bh=r['p_bh']
        )
        insert_count_scores += 1

    if insert_count_scores == 0:
        logging.error('Failed to insert any GSA scores into database')
        return None

    logging.info('Inserted %s new gene set definitions and %s GSA scores', insert_count_geneset, insert_count_scores)
    return 1


def load_correl_results(compute, correl, source):

    assert source in ['WGCNA', 'RegNet']

    insert_count = 0

    for qry_id in correl:

        qry_obj = compute.get_exp_obj(qry_id)
        if qry_obj is None:
            continue

        logger.debug('Working on experiment id %s', qry_id)
        sorted_exps = sorted(correl[qry_id].items(), key=operator.itemgetter(1))
        bottom50 = sorted_exps[:50]
        top50 = sorted_exps[-50:]
        top50.reverse()

        # get rid of any existing correlations
        ExperimentCorrelation.objects.filter(experiment=qry_obj, source=source).delete()

        i = 0
        for ref_exp_id, r in bottom50:
            i -= 1
            ref_obj = compute.get_exp_obj(ref_exp_id)
            if ref_obj is None:
                continue

            ExperimentCorrelation.objects.create(
                experiment=qry_obj,
                experiment_ref=ref_obj,
                source=source,
                correl=r,
                rank=i
            )
            insert_count += 1

        i = 0
        for ref_exp_id, r in top50:
            i += 1
            ref_obj = compute.get_exp_obj(ref_exp_id)
            if ref_obj is None:
                continue

            ExperimentCorrelation.objects.create(
                experiment=qry_obj,
                experiment_ref=ref_obj,
                source=source,
                correl=r,
                rank=i
            )
            insert_count += 1

    if insert_count == 0:
        logging.error('Failed to insert any experiment correlations into database')
        return None

    logging.info('Inserted %s correlations of type %s', insert_count, source)
    return 1
