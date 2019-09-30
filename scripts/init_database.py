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
import pprint
import gzip
import time
import subprocess
import collections
import tp.utils
from tempfile import gettempdir, NamedTemporaryFile
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "toxapp.settings")
application = get_wsgi_application()

from django.conf import settings
from tp.models import MeasurementTech, IdentifierVsGeneMap, Gene, Study, Experiment, ToxicologyResult, GeneSets,\
    GeneSetMember, GeneSetTox, ToxPhenotype, ExperimentVsToxPhenotype
from tp.tasks import load_measurement_tech_gene_map, load_module_scores, load_gsa_scores, load_correl_results
from src.computation import Computation

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def setup_gene_table():
    """
    Action: opens gene file, searches for cols with required cols, it makes sure eachs row has a value,
    then for each column in rows, it replaces each blank value with a None type, then it creates the oject in the database
    Returns: none
    :rtype: object

    """

    gf = os.path.join(settings.BASE_DIR, config['DEFAULT']['gene_file'])
    logger.info('Loading orthology gene table from file %s', gf)
    required_cols = ['rat_entrez_gene', 'rat_gene_symbol']
    createcount = 0
    updatecount = 0
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

            # lookup the exp obj; update if exists create otherwise
            gene = Gene.objects.filter(rat_entrez_gene=row['rat_entrez_gene'])
            if gene:
                gene.update(**row)
                updatecount += 1
            else:
                Gene.objects.create(**row)
                createcount += 1

    logging.info('Number of genes created: %s; number updated: %s', createcount, updatecount)


def setup_measurement_tech():
    """
    Action: reads the measurement tech and measurement detail files, if there is no object or mapping for these, it creates that object
    Returns: measurement object

    """
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
    """
    Action: opens the exoeriments file, looks up the study name, deletes attributes, sets study, results_ready,and tech.
     It looks up the object, if it exists, it is updated, if it doesnt, it is created.
    Returns: created experiments

    """
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


def load_tox_results():
    """
    Action: Opens the tox_results file, and removes any existing toxicology results objects.
    Each experiment in the file that has a value, create that results object.
    Returns: none

    """
    tf = os.path.join(settings.BASE_DIR, config['DEFAULT']['tox_results_file'])
    logger.info('Loading toxicology results from file %s', tf)
    createcount = 0
    rowcount = 0
    # delete existing data if any
    ToxicologyResult.objects.all().delete()

    with open(tf) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            rowcount += 1

            exp_obj = compute.get_exp_obj(row['experiment'])
            if exp_obj is None:
                continue

            row['experiment'] = exp_obj
            ToxicologyResult.objects.create(**row)
            createcount += 1

    logging.info('Number of Toxicology results created: %s; number read in file %s', createcount, rowcount)


def load_experiments_vs_outcomes():
    """
    Action: Opens experiments vs. tox outcome file, deletes existing, and populates model from file.
    Returns: none

    """
    tf = os.path.join(settings.BASE_DIR, config['DEFAULT']['experiments_vs_outcomes'])
    logger.info('Loading experiment vs. tox outcomes from file %s', tf)
    createcount = 0
    rowcount = 0
    # delete existing data if any
    ExperimentVsToxPhenotype.objects.all().delete()

    with open(tf) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            rowcount += 1

            exp_obj = compute.get_exp_obj(row['experiment'])
            if exp_obj is None:
                continue

            rec = dict()
            rec['experiment'] = exp_obj

            # confirm that the experiment ID matches exp name in file
            if exp_obj.experiment_name != row['experiment_name']:
                raise LookupError('Experiment with id {} has different name in file {} vs. db {}'.format(exp_obj.id, row['experiment_name'], exp_obj.experiment_name))

            phenotype, _ = ToxPhenotype.objects.get_or_create(name=row['tox'])
            rec['tox'] = phenotype
            rec['outcome'] = row['outcome']
            rec['type'] = row['type']
            ExperimentVsToxPhenotype.objects.create(**rec)
            createcount += 1

    logging.info('Number of experiment vs. tox phenotype results created: %s; number read in file %s', createcount, rowcount)


def load_geneset_vs_tox_associations():
    """
    Action: Opens tox_association_file, removes all preexisting data objects.
    Sets phenotype to the object in row tox, if there is a geneset it too gets set.
    Then the genesettox object is created.
    Returns: none

    """
    tf = os.path.join(settings.BASE_DIR, config['DEFAULT']['tox_association_file'])
    logger.info('Loading geneset vs toxicology results from file %s', tf)
    createcount = 0
    rowcount = 0
    # delete existing data if any
    GeneSetTox.objects.all().delete()

    with open(tf) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            rowcount += 1

            phenotype, _ = ToxPhenotype.objects.get_or_create(name=row['tox'])
            row['tox'] = phenotype

            try:
                geneset = GeneSets.objects.get(name=row['geneset'])
            except GeneSets.DoesNotExist:
                logger.warning('Geneset %s does not exist in database; skipping', row['geneset'])
                continue

            row['geneset'] = geneset

            GeneSetTox.objects.create(**row)
            createcount += 1

    logging.info('Number of geneset vs tox results created: %s; number read in file %s', createcount, rowcount)


def load_genesets():
    """
    Action: Opens core_gene_sets file, sets gsa info with the same name to the current row.
    Opens the WGCNA Modules, if a row has missing data, an error is raised, each row coulmn is then set to the values in loading.
    Then we read the rgd vs go file. if values are blank, an exception is raised. then the geneset id is set to 1. Then if the row doesnt exist in gsa_info at that row is set to the values.
    Then MSigDB signature vs. gene pairs file is read. IF the subcategory is RegNet it is changed from MSigDB to RegNet. then the value in the current gsa_genes is set to 1.
    If there is no value in row['sig_name'] then it is generated. if n_genes < 3 or n_genes > 5000 then we drop those sigs. We then update or create the object.
    Then we create GeneSetMember objects.
    Returns: none
    Notes: Can this be broken up for readability?
    """
    cf = os.path.join(settings.BASE_DIR, config['DEFAULT']['core_gene_sets'])
    logger.info('Loading core gene sets from file %s', cf)
    gsa_info = collections.defaultdict(dict)
    gsa_genes = collections.defaultdict(dict)

    with open(cf) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            nm = row['name']
            if gsa_info.get(nm, None) is not None:
                logger.fatal('Conflicting names in %s; gene set names must be unique', cf)
                raise RuntimeError()

            gsa_info[nm] = row

    # read module members - overlaps partially with init_modules in Computation class but we need the gene members
    # in the database for drill down of visualizations
    module_file = os.path.join(settings.BASE_DIR, 'data/WGCNA_modules.txt')
    req_attr_m = ['module', 'rat_entrez_gene_id', 'loading']
    with open(module_file) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:

            if any(row[i] == '' for i in req_attr_m):
                logger.fatal('File %s contains undefined values for one or more required attributes %s on line %s',
                             module_file, ",".join(req_attr_m), row)
                raise RuntimeError()

            if not row['module'] in gsa_info:
                logger.warning('Module %s is not defined in core_sets; unexpected and skipping', row['module'])
                continue

            gsa_genes[row['module']][int(row['rat_entrez_gene_id'])] = float(row['loading'])

    # read GO vs. gene pairs from flat file
    go_file = os.path.join(settings.BASE_DIR, 'data/rgd_vs_GO_expansion.txt')
    req_attr_go = ['entrez_gene_id', 'GO_id', 'GO_name', 'GO_type']
    with open(go_file) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:

            if any(row[i] == '' for i in req_attr_go):
                logger.fatal('File %s contains undefined values for one or more required attributes %s on line %s', go_file,
                             ",".join(req_attr_go), row)
                raise RuntimeError()

            gsa_genes[row['GO_id']][int(row['entrez_gene_id'])] = 1

            if not row['GO_id'] in gsa_info:
                gsa_info[row['GO_id']] = {'name': row['GO_id'], 'desc': row['GO_name'], 'type': row['GO_type'],
                                          'core_set': False, 'source': 'GO'}

    # read MSigDB signature vs. gene pairs from flat file
    msigdb_file = os.path.join(settings.BASE_DIR, 'data/MSigDB_and_TF_annotation.txt')
    req_attr_msigdb = ['sig_name', 'rat_entrez_gene', 'sub_category', 'description']
    with open(msigdb_file) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:

            if any(row[i] == '' for i in req_attr_msigdb):
                logger.fatal('File %s contains undefined values for one or more required attributes %s on line %s',
                             msigdb_file, ",".join(req_attr_msigdb), row)
                raise RuntimeError()

            source = 'MSigDB'
            # DAS RegNet networks included in this file - use a separate source for these, not MSigDB
            if row['sub_category'] == 'RegNet':
                source = 'RegNet'

            gsa_genes[row['sig_name']][int(row['rat_entrez_gene'])] = 1
            if not row['sig_name'] in gsa_info:
                gsa_info[row['sig_name']] = {'name': row['sig_name'], 'desc': row['description'], 'type': row['sub_category'],
                                             'core_set': False, 'source': source}

    # eliminate gene sets too small / too large
    sigs_to_drop = list()
    for sig in gsa_info.keys():
        if gsa_info[sig]['core_set']:
            continue  # don't remove a core set ... shouldn't be any anyway that are too small/big

        n_genes = len(list(filter(lambda x: compute.get_gene_obj(x) is not None, gsa_genes[sig])))
        if n_genes < 3 or n_genes > 5000:
            sigs_to_drop.append(sig)
            continue

    logger.debug('Eliminated %s gene sets based on size constraint', len(sigs_to_drop))
    for s in sigs_to_drop:
        gsa_info.pop(s)
        gsa_genes.pop(s)

    updatecount = 0
    createcount = 0

    for sig in gsa_info:

        if sig not in gsa_genes:
            logger.error('No genes defined for signature %s; deleting geneset', sig)
            continue

        row = gsa_info[sig]

        # replace empty values with None - DB expects Null
        for k in row:
            row[k] = None if row[k] == '' else row[k]
            if row[k] == 'TRUE':
                row[k] = True
            if row[k] == 'FALSE':
                row[k] = False

        geneset = GeneSets.objects.filter(name=row['name']).first()
        if geneset:
            for (key, value) in row.items():
                setattr(geneset, key, value)
            geneset.save()
            updatecount += 1
        else:
            geneset = GeneSets.objects.create(**row)
            createcount += 1

        # delete any existing genes for the signature
        geneset.members.clear()

        genes_skipped = 0
        genes_loaded = 0

        for rat_eg in gsa_genes[sig]:
            gene = compute.get_gene_obj(rat_eg)
            # geneobj will be None for genes not loaded in the gene model, warn on total skipped only
            if not gene:
                genes_skipped += 1
                continue
            weight = gsa_genes[sig][rat_eg]
            GeneSetMember.objects.create(geneset=geneset, gene=gene, weight=weight)
            genes_loaded += 1

        try:
            faction_loaded = genes_loaded/(genes_loaded+genes_skipped)
        except:
            logger.error('Attempting division by zero; no genes in sig %s', sig)
            continue

        if genes_loaded == 0:
            logger.error('No genes were added to geneset %s; deleting it', sig)
            geneset.delete()
            continue
        elif faction_loaded < 0.7:
            logger.warning('Fewer than 70 percent of genes in signature %s were in gene model and loaded: %s skipped and %s loaded',\
                           sig, genes_skipped, genes_loaded)
        elif genes_skipped > 0:
            logger.debug('Somes genes in signature %s are not in the gene model and skipped: %s skipped and %s loaded',\
                           sig, genes_skipped, genes_loaded)
        else:
            logger.debug('Number of genes loaded for signature %s: %s', sig, genes_loaded)

    logging.info('Number of core gene sets created: %s, number updated: %s', createcount, updatecount)


def load_fold_change_data():
    """
    Action: we read the files in groupfc_file_location. For each file, we read each row and get each experiment object and identifier object if they exist.
     Then we append them to the row.and write the file to output.
    Returns: none

    """
    pgbin = config['DEFAULT']['pgloader_exec']
    if not os.path.isfile(pgbin):
        logger.fatal('Configured file for pgloader not accessible %s', pgbin)
        exit(1)

    fc_loc = os.path.join(settings.BASE_DIR, config['DEFAULT']['groupfc_file_location'])
    logger.info('Loading group fold change data from dir %s', fc_loc)

    pgloader_conf = os.path.join(settings.BASE_DIR, config['DEFAULT']['pgloader_groupfc_conf'])
    cmd = pgbin + ' ' + pgloader_conf
    outf = NamedTemporaryFile(delete=False, suffix='.txt', dir=tmpdir)
    logger.info('Temporary file for loading fold change data is %s', outf.name)
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
    """
    Action: find out if computing initial gsa from tech object and set it to success.
    For each experiment in each created one, compute the map_fold_change data from experiment. we then compute module scores, gsa scores and status if they exist.
    The values are then saved.
    Returns: none

    """
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
        gsa_scores = compute.score_gsa(fc_data, last_tech=tech_obj)
        if gsa_scores is None:
            failed_scoring['GSA_calc'].append(exp.experiment_name)
            continue
        else:
            status = load_gsa_scores(gsa_scores)
            if status is None:
                failed_scoring['GSA_load'].append(exp.experiment_name)
                continue

        # set the status as ready
        exp.results_ready = True
        exp.save()

    if failed_scoring:
        logger.warning('The following experiments were not successfully scored: %s', pprint.pformat(failed_scoring))


if __name__ == '__main__':
    """
    Action: See commments
    Returns: none

    """

    config = tp.utils.parse_config_file()
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

    # step 4) load the toxicology results file
    load_tox_results()

    # step 4b) load experiment vs outcome data; new in may 2019
    load_experiments_vs_outcomes()

    # step 5) load definition of core gene sets
    load_genesets()

    # step 6) load the toxicology results file
    load_geneset_vs_tox_associations()

    # step 7) load the fold change data
    load_fold_change_data()

    # step 8 - iterate through newly added experiments and perform module / GSA scoring
    # commented out - temp for resuming loads
    #created_exp_list = Experiment.objects.all()
    #tech_obj = created_exp_list[0].tech
    score_experiments(created_exp_list)

    # step 9 - load the pairwise experiment similarities
    correlw = compute.calc_exp_correl(created_exp_list, 'WGCNA')
    load_correl_results(compute, correlw, 'WGCNA')

    correla = compute.calc_exp_correl(created_exp_list, 'RegNet')
    load_correl_results(compute, correla, 'RegNet')

    correlp = compute.calc_exp_correl(created_exp_list, 'PathNR')
    load_correl_results(compute, correlp, 'PathNR')
