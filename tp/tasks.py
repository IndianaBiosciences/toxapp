from __future__ import absolute_import, unicode_literals
from celery import shared_task, current_task
from .models import Experiment, FoldChangeResult, MeasurementTech, Gene, IdentifierVsGeneMap, ModuleScores, GeneSets,\
    GSAScores, ExperimentCorrelation, BenchmarkDoseResult
from django.conf import settings
from django.core.mail import send_mail
from src.computation import Computation

import pprint
import json
import logging
import os
import csv
import operator
import pickle
import shutil

logger = logging.getLogger(__name__)

@shared_task
def add(x, y):
    return x + y


@shared_task
def make_leiden_csv(fullfile, exp_list):
    """
    Action:  creates a leiden csv from experimemnts given
    Returns: True

    """
    rows = FoldChangeResult.objects.filter(experiment__pk__in=exp_list)

    colnames = ['experiment_id', 'experiment_name', 'entrez_gene_id', 'gene_symbol', 'log2_fc', 'p_value', 'p_adj']
    attributes = ['experiment_id', 'experiment.experiment_name', 'gene_identifier.gene.human_entrez_gene', 'gene_identifier.gene.human_gene_symbol', 'log2_fc', 'p', 'p_bh']

    rowcount = 0
    with open (fullfile, 'w', newline='') as csvfile:
        wr = csv.writer(csvfile)
        wr.writerow(colnames)

        for r in rows:

            # our model is rat-centric; some genes lack a human EG
            if r.gene_identifier.gene.human_entrez_gene is None:
                continue

            vals = map(lambda x: operator.attrgetter(x)(r), attributes)
            wr.writerow(vals)
            rowcount += 1

    logger.info('Number of rows in the Leiden export: %s', rowcount)
    return True


@shared_task
def process_user_files(tmpdir, config_file, user, testmode=False):

    """
    A function to calculate a user's fold change results and other downstream bioinfo calculations

    :param tmpdir: the temporary directory from which computations will be run
    :param config_file: the config file set up in the view that dictates how samples map to experiments, etc
    :param user: Django user object for name/email
    :param testmode: a parameter intended for testing celery computation within a test script and bail after fold-change
        calc - i.e. no insertion of test results into DB
    :return: the body of email message sent to user when testmode is false
    """

    from_email = settings.FROM_EMAIL
    compute = Computation(tmpdir)

    # step1 - calculate group fold change and load data to the database
    logger.info('Step 1')
    groupfc_file = compute.calc_fold_change(config_file)

    email_message = "Workflow status\n"

    if groupfc_file is None or not os.path.isfile(groupfc_file):
        message = 'Step 1a Failed: Computation script failed to calculate fold change data'
        logger.error(message)
        email_message += message
        if not testmode:
            send_mail('IBRI CTox Computation: Error at Step 1a', email_message, from_email, [user.email])
        return

    logger.info('Step 1: gene-level fold change file created: %s', groupfc_file)

    email_message += "Step 1a Completed: gene-fold change\n"

    if testmode:
        return email_message

    status = load_group_fold_change(compute, groupfc_file)
    if status is None:
        message = 'Step 1b Failed: Error processing and loading gene-level fold change data; no further computations performed'
        logger.error(message)
        email_message += message
        send_mail('IBRI CTox Computation: Error at Step 1b', email_message, from_email, [user.email])
        return
    logger.info('Step 1: gene-level fold change data processed and loaded')

    email_message += "Step 1b Completed: gene-fold change processed and loaded\n"

    # step 2 - map data for this measurement technology to rat entrez gene IDs
    logger.info('Step 2')
    fc_data = compute.map_fold_change_data(groupfc_file)
    if fc_data is None:
        message = 'Step 2 Failed: Error mapping fold change data to rat entrez gene IDs; no further computations performed'
        logger.error(message)
        email_message += message
        send_mail('IBRI CTox Computation: Error at Step 2', email_message, from_email, [user.email])
        return
    logger.info('Step 2: gene-level fold change data mapped to genes')

    email_message += "Step 2 Completed: gene-fold changes mapped to rat entrez gene IDs\n"
    new_exps = Experiment.objects.filter(id__in=list(fc_data.keys()))

    logger.info('Step 6')
    intensities_file = os.path.join(tmpdir, 'sample_intensities.pkl')
    try:
        with open(intensities_file, 'rb') as fp:
            intensities = pickle.load(fp)
    except FileNotFoundError:
        message = 'Required intensity file {} not produced by computeGFC.py; no further computations performed'.format(intensities_file)
        logger.error(message)
        email_message += message
        send_mail('IBRI CTox Computation: Error at Step 6a', email_message, from_email, [user.email])
        return

    # step 3 - score experiment data using WGCNA modules and load to database
    logger.info('Step 3')
    module_scores = compute.score_modules(fc_data)
    if module_scores is None:
        message = 'Step 3a Failed: Error scoring experiment results using WGCNA modules; no further computations performed'
        logger.error(message)
        email_message += message
        send_mail('IBRI CTox Computation: Error at Step 3a', email_message, from_email, [user.email])
        return
    logger.info('Step 3a: experiment scored using WGCNA models')

    email_message += "Step 3a Completed: experiment scored using WGCNA models\n"

    status = load_module_scores(module_scores)
    if status is None:
        message = 'Step 3b Failed: Error processing and load WGCNA module data; no further computations performed'
        logger.error(message)
        email_message += message
        send_mail('IBRI CTox Computation: Error at Step 3b', email_message, from_email, [user.email])
        return
    logger.info('Step 3b: experiment scored using WGCNA models loaded to database')

    email_message += "Step 3b Completed: Processed and loaded of WGCNA modules data\n"

    # step 4 - score experiment data using GSA
    logger.info('Step 4')
    gsa_scores = compute.score_gsa(fc_data)
    if gsa_scores is None:
        message = 'Step 4a Failed: Error scoring experiment results using GAS; no further computations performed'
        logger.error(message)
        email_message += message
        send_mail('IBRI CTox Computation: Error at Step 4a', email_message, from_email, [user.email])
        return
    logger.info('Step 4a: experiment scored using GSA')

    email_message += "Step 4a Completed: Experiments scored using GSA\n"

    status = load_gsa_scores(gsa_scores)
    if status is None:
        message = 'Step 4b Failed: Error processing and loading GSA data; no further computations performed'
        logger.error(message)
        email_message += message
        send_mail('IBRI CTox Computation: Error at Step 4b', email_message, from_email, [user.email])
        return
    logger.info('Step 4b: experiment scored using GSA and loaded to database')

    email_message += "Step 4b Completed: GSA results loaded to database\n"

    # step 5 - calculate near neighbors based on vector of module scores or GSA scores
    logger.info('Step 5: evaluating pairwise similarity vs. experiments using WGCNA, RegNet and PathNR')
    correl = compute.calc_exp_correl(new_exps, 'WGCNA')
    if correl is None:
        message = 'Step 5a Failed: Error calculating correlation to existing experiments using WGCNA; no further computations performed'
        logger.error(message)
        email_message += message
        send_mail('IBRI CTox Computation: Error at Step 5a', email_message, from_email, [user.email])
        return
    logger.info('Step 5a: experiment correlation calculated using WGCNA')

    email_message += "Step 5a Completed: Correlations to WGCNA modules calculated\n"

    status = load_correl_results(compute, correl, 'WGCNA')
    if status is None:
        message = 'Step 5b Failed: Error loading experiment correlation for WGCNA; no further computations performed'
        logger.error(message)
        email_message += message
        send_mail('IBRI CTox Computation: Error at Step 5b', email_message, from_email, [user.email])
        return
    logger.info('Step 5b: experiment correl using WGCNA loaded to database')

    email_message += "Step 5b Completed: Correlations to WGCNA processed and loaded\n"

    correl = compute.calc_exp_correl(new_exps, 'RegNet')
    if correl is None:
        message = 'Failed to calculate correlation to existing experiments using RegNet; no further computations performed'
        logger.error(message)
        email_message += message
        send_mail('IBRI CTox Computation: Error at Step 5b', email_message, from_email, [user.email])
        return
    logger.info('Step 5c: experiment correlation calculated using RegNet')

    email_message += "Step 5c Completed: Correlations to RegNet modules calculated\n"

    status = load_correl_results(compute, correl, 'RegNet')
    if status is None:
        message = 'Failed to load experiment correlation for RegNet; no further computations performed'
        logger.error(message)
        email_message += message
        send_mail('IBRI CTox Computation: Error at Step 5d', email_message, from_email, [user.email])
        return
    logger.info('Step 5d: experiment correl using RegNet loaded to database')

    email_message += "Step 5d Completed: Correlations to RegNet processed and loaded\n"

    correl = compute.calc_exp_correl(new_exps, 'PathNR')
    if correl is None:
        message = 'Failed to calculate correlation to existing experiments using PathNR; no further computations performed'
        logger.error(message)
        email_message += message
        send_mail('IBRI CTox Computation: Error at Step 5e', email_message, from_email, [user.email])
        return
    logger.info('Step 5e: experiment correlation calculated using PathNR')

    email_message += "Step 5e Completed: Correlations to PathNR gene sets calculated\n"

    status = load_correl_results(compute, correl, 'PathNR')
    if status is None:
        message = 'Failed to load experiment correlation for PathNR; no further computations performed'
        logger.error(message)
        email_message += message
        send_mail('IBRI CTox Computation: Error at Step 5f', email_message, from_email, [user.email])
        return
    logger.info('Step 5f: experiment correl using PathNR loaded to database')

    email_message += "Step 5f Completed: Correlations to PathNR processed and loaded\n"

    files = compute.make_BMD_files(new_exps, config_file, intensities, fc_data)
    if not files:
        message = 'No BMD input files prepared; no suitable multi-concentration experiments'
        logger.info(message)
        email_message += message
    else:
        bm2_file = compute.run_BMD(files)
        if bm2_file is None or not os.path.isfile(bm2_file):
            message = 'Failed to run BMD calculations on files {}; no further computations performed'.format(files)
            logger.error(message)
            email_message += message
            send_mail('IBRI CTox Computation: Error at Step 6b', email_message, from_email, [user.email])
            return

        status = load_bmd_results(new_exps, bm2_file)
        if status is None:
            message = 'Step 6c Failed: Error processing and load BMD results data; no further computations performed'
            logger.error(message)
            email_message += message
            send_mail('IBRI CTox Computation: Error at Step 6c', email_message, from_email, [user.email])
            return
        logger.info('Step 6c: BMD file reference loaded to database')

        logger.info('Step 6 Completed: BMD results generated')

    for exp in new_exps:
        exp.results_ready = True
        exp.save()

    message = 'All computations sucessfully completed.\nUploaded expression data is ready for analysis'
    logger.info(message)
    email_message += message
    send_mail('IBRI CTox Computation: Complete', email_message, from_email, [user.email])
    return email_message


def load_group_fold_change(compute, groupfc_file):
    """
    Action:  Reads fold change from groupfc_file,  If Results exist, they are deleted, otherwise they are created as an object.
    Returns: 1

    """
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
                logger.debug('No exp obj for experiment id %s', exp_id)
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

    if identifier_lookup_fail:
        n_fails = len(identifier_lookup_fail)
        ids = list(identifier_lookup_fail.keys())[0:10]
        id_str = ','.join(ids)
        logger.warning('A total of %s identifiers in file %s are not entrez gene IDs in database and ignored; the first 10 are: %s', n_fails, groupfc_file, id_str)
        if n_fails > int(rownum/2):
            logger.critical('More than 50percent of identifiers in file ( %s ) lack a corresponding identifier in database; Probable error ... exiting', n_fails)
            exit(0)

    if insert_count == 0:
        logger.error('Failed to load any records from file')
        return None

    logging.info('Inserted %s out of %s records from file %s', insert_count, rownum, groupfc_file)
    return 1


def load_measurement_tech_gene_map(file):
    """
    Action:  Loads measurement tech gene map from file.  Opens the file, for each row, set values,  then gets the tech object from these values. Creates object from values found.
    Returns: Insert Count

    """
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
    """
    Action:  Find Values based upon tech and tech detail, if nothing is found, the object is then created.
    Returns: Tech Object

    """
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
    """
    Action:  Inserts module scores into database as objects
    Returns: 1

    """
    logger.info('Loading computed module scores into database')

    insert_count_scores = 0

    # compile a list of all modules for which results will be loaded, and save in dict to keep
    # retrieving the same one
    load_modules = dict()
    for r in module_scores:
        load_modules[r['module']] = None

    for s in load_modules:
        try:
            geneset_obj = GeneSets.objects.get(name=s)
        except:
            logger.error('No gene set defined in database for %s; skipping results load', s)
            continue

        load_modules[s] = geneset_obj

    checked_exist = dict()
    for r in module_scores:

        if load_modules.get(r['module'], None) is None:
            # already warned above when failed to retrieve module by name
            continue

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


def load_gsa_scores(gsa_scores):
    """
    Action:  Inserts GSA Scores into database
    Returns: 1

    """
    logger.info('Loading computed GSA scores into database')

    insert_count_scores = 0

    # compile a list of all gene sets for which results will be loaded
    load_gene_sets = dict()
    for r in gsa_scores:
        load_gene_sets[r['geneset']] = None

    for s in load_gene_sets:
        try:
            geneset_obj = GeneSets.objects.get(name=s)
        except:
            logger.error('No gene set defined in database for %s; skipping results load', s)
            continue

        load_gene_sets[s] = geneset_obj

    checked_exist = dict()
    for r in gsa_scores:

        if load_gene_sets.get(r['geneset'], None) is None:
            # already warned above when failed to retrieve geneset by name
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

    return 1


def load_correl_results(compute, correl, source):
    """
    Action:  Inserts correlation results into database object
    Returns: 1

    """
    assert source in ['WGCNA', 'RegNet', 'PathNR']

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


def load_bmd_results(exps, bm2file):
    """
    Action:  Inserts bm2 results file into database
    Returns: 1

    """
    assert os.path.isfile(bm2file)

    bm2file_loc = os.path.join(settings.COMPUTATION['url_dir'], 'bm2_files')
    if not os.path.isdir(bm2file_loc):
        os.makedirs(bm2file_loc)

    # copy the file into persisted bm2 files folder
    exp_ids = [str(e.id) for e in exps]
    base = 'bmdresults_exps_' + '_'.join(exp_ids) + '.bm2'
    newfile = os.path.join(bm2file_loc, base)
    shutil.copy(bm2file, newfile)

    insert_count = 0

    for exp_obj in exps:
        BenchmarkDoseResult.objects.filter(experiment=exp_obj).delete()
        BenchmarkDoseResult.objects.create(
            experiment=exp_obj,
            bm2_file=base
        )
        insert_count += 1

    logging.info('Inserted %s experiment vs BM2 file result associations', insert_count)
    return 1
