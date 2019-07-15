import pprint
import json
import subprocess
import logging
import os
import sys
import csv
import collections
import copy
import itertools
import numpy as np
import rpy2.robjects as robjects
import tempfile
import time
import statistics
from rpy2.robjects.packages import importr
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.stats.stats import pearsonr
from collections import defaultdict
from django.conf import settings
from tp.models import MeasurementTech, IdentifierVsGeneMap, Experiment, FoldChangeResult, GeneSets, ModuleScores,\
    GSAScores, Gene, ToxPhenotype, ExperimentVsToxPhenotype, BMDPathwayResult
import tp.utils

logger = logging.getLogger(__name__)


def cluster_expression_features(data, x_vals, y_vals):
    """
    Action: creates an array based on the size of x and y values. the data is then filled into the array.
    Perform hierarchical/agglomerative clustering based upon the data in a. Then the results from z are then plotted into a dendrogram. the values are then sorted, the first xvalue is set to r['x']
    Returns: Sorted x values, and the data

    """
    logger.debug('Starting clustering')
    # lay out the table with experiments on cols and genes/pathways/modules (x_vals) on rows
    a = np.zeros(shape=(len(x_vals), len(y_vals)))

    # fill in the 2D array
    for r in data:
        a[[r['x']], [r['y']]] = r['value']

    Z = linkage(a, 'ward')
    results = dendrogram(Z, no_plot=True, get_leaves=False)
    # results['ivl'] is the new order of x_vals
    remap = list(map(int, results['ivl']))
    sorted_x_vals = [x for _, x in sorted(zip(remap, x_vals))]
    for r in data:
        r['x'] = remap.index(r['x'])
        sorted_x_vals[r['x']] = r['feat']

    logger.debug('Clustering complete')
    return sorted_x_vals, data


class Vividict(dict):
    def __missing__(self, key):
        value = self[key] = type(self)()
        return value


class Computation:

    def __init__(self, tmpdir):

        self.tmpdir = tmpdir
        # not instantiating automatically -- programmer must do so based on which computations will be used ... avoid
        # loading everything and slowing down
        self.module_defs = None
        self.module_file = None
        self.gene_identifier_stats = None
        self.gene_identifier_stats_file = None
        self.gsa_gsc_obj = None
        self.rpy2_stats = None
        self.rpy2_base = None
        self._experiment_tech_map = dict()
        self._expid_obj_map = dict()
        self._expname_obj_map = dict()
        self._identifier_obj_map = dict()
        self._gene_obj_map = dict()


    def map_fold_change_from_exp(self, exp_obj):
        """
        Action: results is set to the experiments matching the given object. for each item in results, set rat_eg to the rat_entrez_gene.
        Then set fc_data at location of the experiment id and the rat_eg to the results log2_fc and the gene identifier.
        Returns: fc_data

        """
        assert isinstance(exp_obj, Experiment)
        results = FoldChangeResult.objects.filter(experiment=exp_obj)

        if not results:
            logger.error('No results loaded for experiment %s, aborting', exp_obj.id)
            return None

        # dictionary of log2 fc results keyed on experiment / gene identifier
        fc_data = collections.defaultdict(dict)

        for r in results:
            rat_eg = r.gene_identifier.gene.rat_entrez_gene
            fc_data[exp_obj.id][rat_eg] = {'log2_fc': float(r.log2_fc), 'identifier': r.gene_identifier.gene_identifier}

        return fc_data

    def get_exp_obj(self, exp_id):
        """ method to avoid repeatedly checking existence of object for exp_id """

        # record a None in map so that we don't repeatedly check for non-loaded exp; therefore use False as test here
        if self._expid_obj_map.get(exp_id, False) is False:

            try:
                logger.debug('Querying object for exp id %s', exp_id)
                exp_obj = Experiment.objects.get(pk=exp_id)
                self._expid_obj_map[exp_id] = exp_obj
            except:
                logger.error('Failed to retrieve meta data for exp id %s; must be loaded first', exp_id)
                self._expid_obj_map[exp_id] = None

        return self._expid_obj_map[exp_id]


    def get_exp_obj_from_name(self, exp_name):
        """ method to avoid repeatedly checking existence of object for exp name """

        # record a None in map so that we don't repeatedly check for non-loaded exp; therefore use False as test here
        if self._expname_obj_map.get(exp_name, False) is False:

            try:
                logger.debug('Querying object for exp name %s', exp_name)
                exp_obj = Experiment.objects.get(experiment_name=exp_name)
                self._expname_obj_map[exp_name] = exp_obj
            except:
                logger.error('Failed to retrieve meta data for exp id %s; must be loaded first', exp_name)
                self._expname_obj_map[exp_name] = None

        return self._expname_obj_map[exp_name]


    def get_identifier_obj(self, tech_obj, identifier):
        """ method to avoid repeatedly checking existence of object for measurement tech identifier """

        assert isinstance(tech_obj, MeasurementTech)
        barcode = str(tech_obj.id) + ":" + identifier
        # record a None in map so that we don't repeatedly check for non-loaded exp; therefore use False as test here
        if self._identifier_obj_map.get(barcode, False) is False:

            try:
                #logger.debug('Querying object for tech id:gene identifier %s', barcode)
                identifier_obj = IdentifierVsGeneMap.objects.get(gene_identifier=identifier, tech=tech_obj)
                self._identifier_obj_map[barcode] = identifier_obj
            except:
                # be quiet on these, potentially hundreds per experiment, calling method should provide a summary
                #logger.debug('Failed to retrieve information on identifier %s for measurement tech %s', identifier, tech_obj)
                self._identifier_obj_map[barcode] = None

        return self._identifier_obj_map[barcode]

    def get_gene_obj(self, rat_eg):
        """ method to avoid repeatedly checking existence of object for rat entrez gene """

        # record a None in map so that we don't repeatedly check for non-loaded exp; therefore use False as test here
        if self._gene_obj_map.get(rat_eg, False) is False:

            try:
                #logger.debug('Querying object for rat entrez gene id %s', rat_eg)
                gene_obj = Gene.objects.get(rat_entrez_gene=rat_eg)
                self._gene_obj_map[rat_eg] = gene_obj
            except:
                #logger.debug('Failed to retrieve meta data for rat entrez gene id %s; must be loaded first', rat_eg)
                self._gene_obj_map[rat_eg] = None

        return self._gene_obj_map[rat_eg]

    def get_experiment_tech_map(self, exp_id):

        """ wrapper class to avoid repeatedly checking measurement tech for a given object """

        if self._experiment_tech_map.get(exp_id, False) is False:

            exp_obj = self.get_exp_obj(exp_id)
            if exp_obj is None:
                self._experiment_tech_map[exp_id] = None
            else:
                self._experiment_tech_map[exp_id] = exp_obj.tech

        return self._experiment_tech_map[exp_id]

    def calc_fold_change(self, cfg_file):
        """ calculate group fold change from files in tmpdir and meta data received from webapp in config json file """

        tmpdir = self.tmpdir
        logger.debug('Starting fold change calculation in directory %s using config_file %s', tmpdir, cfg_file)

        script_dir = settings.COMPUTATION['script_dir']
        script = os.path.join(script_dir, "computeGFC.py")
        outfile = "groupFC.txt"
        script_cmd = "export PYTHONPATH={}; cd {}; {} {} -i {} -o {}".format(settings.BASE_DIR, tmpdir, sys.executable, script, cfg_file, outfile)
        file = os.path.join(tmpdir, outfile)
        logger.info("command %s ", script_cmd)
        output = subprocess.getoutput(script_cmd)
        logger.info('calc_fold_change: Done fold change calculation; results in %s', file)
        return file

    def init_modules(self):
        """ method that must be called before calculating module scores """

        module_file = os.path.join(settings.BASE_DIR, 'data/WGCNA_modules.txt')
        genestats_file = os.path.join(settings.BASE_DIR, 'data/gene_identifier_stats.txt')

        md = Vividict()
        req_attr_m = ['module', 'tissue', 'organism', 'pc1_stdev', 'rat_entrez_gene_id', 'loading', 'eigengene_correl']
        with open(module_file) as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:

                if any(row[i] == '' for i in req_attr_m):
                    logger.error('File %s contains undefined values for one or more required attributes %s on line %s', module_file, ",".join(req_attr_m), row)
                    return None

                system = ":".join([row['tissue'], row['organism']])
                md[system][row['module']]['genes'][int(row['rat_entrez_gene_id'])] = float(row['loading'])
                md[system][row['module']]['stdev'] = float(row['pc1_stdev'])

        #logger.debug('Read following module defs from file %s: %s', module_file, pprint.pformat(md, indent=4))

        setattr(self, 'module_defs', md)
        setattr(self, 'module_file', module_file)

        gs = Vividict()
        req_attr_g = ['tech', 'tech_detail', 'tissue', 'organism', 'source', 'identifier', 'mean_fc', 'stdev_fc']
        with open(genestats_file) as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:

                if any(row[i] == '' for i in req_attr_g ):
                    logger.error('File %s contains undefined values for one or more required attributes %s on line %s', genestats_file, ",".join(req_attr_g), row)
                    return None

                # if a gene doesn't have rat ortholog, skip for now as these are rat-centric modules
                if row['rat_entrez_gene_id'] == '':
                    continue

                system = ":".join([row['tissue'], row['organism'], row['tech'], row['tech_detail']])
                gs[system][int(row['rat_entrez_gene_id'])] = {'mean_fc': float(row['mean_fc']), 'stdev_fc': float(row['stdev_fc']), 'source': row['source'], 'identifier': row['identifier']}

        #logger.debug('Read following gene identifier stats from file %s: %s', genestats_file, pprint.pformat(gs, indent=4))

        setattr(self, 'gene_identifier_stats', gs)
        setattr(self, 'gene_identifier_stats_file', genestats_file)
        return 1

    def init_gsa(self, tech, gsa_file=None):
        """ method that must be called before running GSA;  requires gmt file that R requires and loads in R;
            gsa_file pameter used in testing to decouple gsa_file generation from R load """

        if not gsa_file:
            gsa_file = self.make_gsa_file(tech)

        # load packages and the gmt file
        importr('piano')
        gsc = robjects.r('loadGSC("{}")'.format(gsa_file))
        setattr(self, 'gsa_gsc_obj', gsc)
        return 1

    def make_gsa_file(self, tech_obj):
        """
        Action: Make sure there are atleast 1000 identifiers, create temp file, for each signature write each to gmt
        Returns:gmt name

        """
        assert isinstance(tech_obj, MeasurementTech)

        identifiers = IdentifierVsGeneMap.objects.filter(tech=tech_obj).all()
        if identifiers is None or len(identifiers) < 1000:
            logger.error('Failed to retrieve at least 1000 identifiers for measurement platform %s', tech_obj)
            return None

        # discard genes from gene sets not being measured
        keep_rat_genes = dict()
        for r in identifiers:
            keep_rat_genes[r.gene.rat_entrez_gene] = 1

        # prepare file suitable for R GSA calc
        # this needs to be generated at run time because each measurement tech will have a different subset of genes
        gmt = tempfile.NamedTemporaryFile(delete=False, suffix='.gmt', dir=self.tmpdir)

        logger.debug('Have temporary GSA file %s', gmt.name)
        sig_count = 0
        for s in GeneSets.objects.exclude(source='WGCNA').prefetch_related('members'):
            sig_count += 1

            rat_egs = list()
            # you can't use queryset filter without rerunning the query and defeating point of prefetch
            # therefore iterate through members old style
            rat_egs = list(filter(lambda x: keep_rat_genes.get(x, None) is not None, s.members.all().values_list('rat_entrez_gene',flat=True)))

            if len(rat_egs) < 3:
                if s.core_set:
                    logger.warning('Fewer than 3 genes retrieved for core gene set %s on this platform; skipping', s.name)
                continue

            elements = [s.name, 'no_link'] + [str(g) for g in rat_egs]
            row = '\t'.join(elements) + '\n'
            row_as_bytes = str.encode(row)
            gmt.write(row_as_bytes)
            if sig_count%1000 == 0:
                logger.debug('Done %s signatures', sig_count)

        gmt.close()
        return gmt.name

    def map_fold_change_data(self, fc_file, use_experiment_name=False):

        """ read the fold change data and map to rat entrez gene IDs starting from a file """

        # TODO - look into minor - this could be retired by using the map_fold_change_from_exp as we are effectively doing the same
        # mapping exercise twice - once when loading the FC data in tasks.py function, then once again here.
        # However this means that the Computation script could no longer run without loading the fold change data using
        # the function in tasks.  As it stands script can perform complete calculation without actually loading anything
        # to DB

        identifier_map = dict()
        last_tech = None
        # track identifiers that failed to convert to rat entrez
        failed_map = dict()
        success_map = dict()
        # dictionary of log2 fc results keyed on experiment / gene identifier
        fc_data = collections.defaultdict(dict)

        # read the fold change data
        logger.debug("reading data from %s", fc_file)
        if use_experiment_name:
            req_attr = ['experiment_name', 'gene_identifier', 'log2_fc']
        else:
            req_attr = ['experiment', 'gene_identifier', 'log2_fc']

        with open(fc_file) as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                if any(row[i] == '' for i in req_attr):
                    logger.error('File %s contains undefined values for one or more required attributes %s on line %s', fc_file, ",".join(req_attr), row)
                    return None

                if use_experiment_name:
                    exp_obj = self.get_exp_obj_from_name(row['experiment_name'])
                    if not exp_obj:
                        continue
                    exp_id = exp_obj.id
                else:
                    exp_id = int(row['experiment'])

                this_tech = self.get_experiment_tech_map(exp_id)

                if this_tech is None:
                    continue

                if last_tech is None or this_tech != last_tech:
                    # update the map of identifers to genes ... in case experiment contains multiple measurement platforms
                    identifiers = IdentifierVsGeneMap.objects.filter(tech=this_tech).all()
                    if identifiers is None or len(identifiers) < 1000:
                        logger.error('Failed to retrieve at least 1000 identifiers for measurement platform %s', this_tech)
                        return None

                    identifier_map = {} # empty the dict in case collision between ids on two measurement platforms
                    # map for converting measurement platform identifiers to rat entrez gene IDs
                    for r in identifiers:
                        identifier_map[r.gene_identifier] = r.gene.rat_entrez_gene

                last_tech = this_tech

                rat_entrez = identifier_map.get(row['gene_identifier'], None)

                if rat_entrez is None:
                    failed_map[row['gene_identifier']] = 1
                    continue
                else:
                    success_map[row['gene_identifier']] = 1

                if rat_entrez in fc_data.get(exp_id, {}):
                    logger.error('Data already defined for experiment %s and rat entrez gene %s; multiple gene identifers for same gene?', exp_id, rat_entrez)
                    continue

                fc_data[exp_id][rat_entrez] = {'log2_fc': float(row['log2_fc']), 'identifier': row['gene_identifier']}

        if failed_map:
            n_fails = len(failed_map)
            ids = list(failed_map.keys())[0:10]
            id_str = ",".join(ids)
            logger.warning('A total of %s identifiers in file %s are not mapped to entrez gene IDs and ignored; the first 10 are: %s', n_fails, fc_file, id_str)
            n_success = len(success_map)
            if n_fails > n_success:
                logger.critical('Number of failed mappings %s were greater than number of successful mappings: %s. Assuming wrong tech setup ... exiting', n_fails, n_success)
                return None

        #logger.debug('Have fold change data for file %s: %s', fc_file, pprint.pformat(fc_data))
        return fc_data

    def score_modules(self, fc_data):

        """ use data mapped to entrez gene for calculating module scores"""
        if self.module_defs is None or self.gene_identifier_stats is None:
            success = self.init_modules()
            if not success:
                logger.error('Failed to initiatize module calculation')
                return None

        md = self.module_defs
        gs = self.gene_identifier_stats
        warned_scaling = dict()

        module_scores = list()
        for exp_id in fc_data.keys():

            exp_obj = self.get_exp_obj(exp_id)
            if exp_obj is None:
                continue

            system = ":".join([exp_obj.tissue, exp_obj.organism])
            if md.get(system, None) is None:
                default_system = 'liver:rat'
                logger.warning('No module definitions for system %s; assuming %s', system, default_system)
                system = default_system

            systech = ":".join([exp_obj.tissue, exp_obj.organism, exp_obj.tech.tech, exp_obj.tech.tech_detail])
            if gs.get(systech, None) is None:
                default_systech = 'liver:rat:microarray:RG230-2'
                logger.warning('No gene identifier scaling information for system %s, assuming %s but important to '
                               'load for your system', systech, default_systech)
                systech = default_systech

            # scale log2fc using gene identifiers's log2fc variability
            scaled_fc = dict()

            for gene in fc_data[exp_id].keys():
                if gs[systech].get(gene, None) is None:
                    if warned_scaling.get(gene, None) is None:
                        #logger.debug('No scaling data for gene identifier %s for system %s; skipping', gene, systech)
                        warned_scaling[gene] = 1
                    continue

                stdev_fc = gs[systech][gene]['stdev_fc']
                fc_scaled = fc_data[exp_id][gene]['log2_fc']/stdev_fc
                scaled_fc[gene] = fc_scaled

            n_fails = len(warned_scaling)
            n_success = len(scaled_fc)

            if n_success < 1000:
                logging.error('Fewer than 1000 identifiers (%s) from fold change data were used for module scoring; likely mapping error', n_success)
                return None
            elif n_fails:
                ids = list(warned_scaling.keys())[0:10]
                id_str = ",".join(str(x) for x in ids)
                logger.warning('A total of %s genes with fold change results were not used for module scoring due to missing scaling factors; the first 10 are: %s', n_fails, id_str)

            for m in md[system].keys():
                modsum = 0
                warned_gene = dict()
                n_genes = 0

                for gene in md[system][m]['genes'].keys():
                    n_genes += 1
                    if scaled_fc.get(gene, None) is None:
                        warned_gene[gene] = 1
                        continue
                    modsum += scaled_fc[gene]*md[system][m]['genes'][gene]

                modsum /= md[system][m]['stdev']
                module_scores.append({'exp_id': exp_id, 'exp_obj': exp_obj, 'module': m, 'score': modsum})

                n_missing = len(warned_gene)
                ratio_missed = n_missing/n_genes
                if ratio_missed > 0.30:
                    pass
                    #logger.warning('Missing more than 30percent of genes (%s) for module %s of size %s; lower concern for small modules', n_missing, m, n_genes)

        #logger.debug('Have results from module scoring: %s', pprint.pformat(module_scores, indent=4))
        return module_scores

    def score_gsa(self, fc_data, last_tech=None, gsa_file=None):

        """ use data mapped to entrez gene for calculating module scores; optional gsa_file parameter
        used for decoupling gsa_file generation, R initialization and scoring in tests """

        # need to re-initiliaze gsa if measurement tech were to change during one set of experiment upload to
        # avoid having genes in R gsc object that are not defined in fold change data
        gsa_scores = list()

        for exp_id in fc_data.keys():

            exp_obj = self.get_exp_obj(exp_id)
            if exp_obj is None:
                continue

            this_tech = exp_obj.tech
            if last_tech is None or last_tech != this_tech:

                logger.debug('Initializing GSA for measurement tech %s', this_tech)
                success = self.init_gsa(this_tech, gsa_file=gsa_file)
                if not success:
                    logger.error('Failed to initiatize gsa calculation')
                    return None

            egs = list()
            fc = list()
            for eg in fc_data[exp_id].keys():
                egs.append(eg)
                fc.append(fc_data[exp_id][eg]['log2_fc'])

            R_fc = robjects.FloatVector(fc)
            R_fc.names = robjects.IntVector(egs)
            gsa = robjects.r('runGSA({}, gsc={}, geneSetStat="page",gsSizeLim=c(3,5000),signifMethod="nullDist", adjMethod="BH")'.format(R_fc.r_repr(), self.gsa_gsc_obj.r_repr()))
            # in general, do R_object.names to see what was captured from R

            # all these values are coming out as matrices - grab the first column only with [0]
            p_adj_down = list(gsa.rx('pAdjDistinctDirDn')[0])
            p_adj_up = list(gsa.rx('pAdjDistinctDirUp')[0])
            scores = list(gsa.rx('statDistinctDir')[0])
            names = list(robjects.r('names( {}$gsc )'.format(gsa.r_repr())))

            n_path = len(names)
            if n_path != len(p_adj_down) or n_path != len(p_adj_up) or n_path != len(scores):
                logger.error('Received different number of elements from GSA run in R .. something wrong')
                return None

            for i in range(0, n_path):

                sig = names[i]
                geneset = GeneSets.objects.get(name=sig)

                if geneset is None:
                    logger.error('Failed to find geneset %s in database; did R mangle name?', sig)
                    continue

                score = scores[i]
                # the p-value to use is the one corresponding to direction of change (induction/repression) conveyed by z-score
                p = p_adj_up[i] if score >=0 else p_adj_down[i]

                # only store non-significant results for the core liver-relevant set
                if p > 0.1 and not geneset.core_set:
                    continue

                # p-values of 0 with large z-score are float issues in R ... very small p-value
                if p == 0 and score and abs(score) >= 5:
                    p = 1e-17

                gsa_scores.append({'exp_id': exp_id,
                                   'exp_obj': exp_obj,
                                   'geneset': sig,
                                   'score': score,
                                   'p_bh': p,
                                  })

            last_tech = this_tech

        #logger.debug('Have results from GSA scoring: %s', pprint.pformat(gsa_scores, indent=4))
        return gsa_scores

    def make_score_vs_tox_association_table(self, geneset_obj, tox_obj, time=None):

        """ prepare a table to calculate the statistics (p-adj, coef, etc) per TXG-MAP manuscript for a geneset vs. a tox phenoype;
        This uses the assigment of experiments to outcomes from the ExperimentVsToxPhenotype model, so 'predictive'
        associations, like expression@1d vs. path @30 day must have the association loaded in the model;

        If time is specified, it is a predictive association; retrieve exps for the timepoint and associate
        with outcomes of type 'P' (predictive)
        """

        assert isinstance(geneset_obj, GeneSets)
        assert isinstance(tox_obj, ToxPhenotype)

        # get the experiments to use for the association
        if time:
            exp_vs_outcome = ExperimentVsToxPhenotype.objects.filter(tox=tox_obj, experiment__time=time)
        else:
            exp_vs_outcome = ExperimentVsToxPhenotype.objects.filter(tox=tox_obj)

        logger.debug('Obtained %s experiment vs. outcome objects', len(exp_vs_outcome))

        if not len(exp_vs_outcome) > 30:
            logger.error('Fewer than 30 vs tox outcomes for tox outcome %s and time %s; actual count is %s', tox_obj.name, time, len(exp_vs_outcome))
            return

        base_modules = GeneSets.objects.filter(source='WGCNA', repr_set=True)
        if not base_modules:
            raise LookupError('Did not retrieve base WGCNA modules for avgEG computation')


        if geneset_obj.source == 'WGCNA':
            scores = ModuleScores.objects.filter(module=geneset_obj)
        else:
            scores = GSAScores.objects.filter(geneset=geneset_obj)

        if not scores:
            raise LookupError('Did not get any scores for geneset id / name'.format(geneset_obj.id, geneset_obj.name))

        scoresdict = dict()
        for s in scores:
            scoresdict[s.experiment.id] = float(s.score)

        # create a dictionary of experiment id, outcome, then score for data frame creation in r
        table = list()
        for r in exp_vs_outcome:

            score = scoresdict.get(r.experiment.id, None)
            if score is None:
                logger.error('No score for experiment %s and geneset %s; skipping', r.experiment.experiment_name, geneset_obj.name)
                continue

            row = {'exp_id': r.experiment.id, 'outcome': r.outcome, 'score': score}

            # calculate the average module score
            base_scores = ModuleScores.objects.filter(experiment=r.experiment, module__in=base_modules).values_list('score',flat=True)
            if len(base_scores) < 200:
                raise LookupError('Obtained fewer than 200 base module ( actual {} ) scores for experiment {}'.format(len(base_scores), r.experiment.id))

            # convert queryset to a plain list of float
            base_scores = list(map(lambda x: float(x), base_scores))

            row['avg_EG'] = statistics.mean(base_scores)
            table.append(row)

        return table

    def run_score_vs_tox_association(self, table):

        """
        Takes a dictionary from make_score_vs_tox_association_table and performs the logistic regression analysis

        """

        if not self.rpy2_stats:
            self.rpy2_stats = importr('stats')

        if not self.rpy2_base:
            self.rpy2_base = importr('base')

        pos_scores = list()
        neg_scores = list()
        scores = list()
        outcomes = list()
        avg_EG = list()

        # convert the list of dictionaries to vectors for instantiation in R
        for row in table:
            if row['outcome']:
                pos_scores.append(row['score'])
            else:
                neg_scores.append(row['score'])
            scores.append(row['score'])
            outcomes.append(row['outcome'])
            avg_EG.append(row['avg_EG'])

        if len(pos_scores) < 5:
            logger.warning('Fewer than 5 positives in table; not performing analysis')
            return

        analysis = {'mean_pos': statistics.mean(pos_scores), 'mean_neg': statistics.mean(neg_scores),
                    'n_pos': len(pos_scores), 'n_neg': len(neg_scores)}
        analysis['effect_size'] = (analysis['mean_pos'] - analysis['mean_neg']) / statistics.stdev(scores)

        outcomes_R = robjects.BoolVector(outcomes)
        scores_R = robjects.FloatVector(scores)
        avg_EG_R = robjects.FloatVector(avg_EG)

        robjects.globalenv['outcomes'] = outcomes_R
        robjects.globalenv['scores'] = scores_R
        robjects.globalenv['avg_EG'] = avg_EG_R

        # the model using only the score as variable (e.g. pathway / module)
        single = self.rpy2_stats.glm('outcomes ~ scores', family='binomial')
        single_summary = self.rpy2_base.summary(single)
        # you need to know where the things we want are in the array; here 4.1584 and 3.41e-06
        # Coefficients:
        #            Estimate Std. Error z value Pr(>|z|)
        # (Intercept)  -2.0355     0.3352  -6.072 1.26e-09 ***
        # scores        4.1584     0.8954   4.644 3.41e-06 ***
        # ---

        coef_single = single_summary.rx2('coefficients')[1]
        analysis['p_single'] = single_summary.rx2('coefficients')[7]

        # the full model using avg_EG and score
        full = self.rpy2_stats.glm('outcomes ~ avg_EG + scores', family='binomial')
        analysis['coef'] = full.rx2('coefficients')[2]

        # the base model for add1 - only avg_EG_R as independent variable
        base_avgEG = self.rpy2_stats.glm('outcomes ~ avg_EG', family='binomial')
        robjects.globalenv['base_avgEG'] = base_avgEG
        add1 = robjects.r('add1(base_avgEG, scope = ~avg_EG + scores, test="Chisq")')
        analysis['p_adj'] = add1.rx2('Pr(>Chi)')[1]

        return analysis


    def calc_exp_correl(self, qry_exps, source):
        """
        Action: depending on source, set sets to the filtered geneset, sorts and calculates the correlation between exps
        Returns: correlated results

        """
        assert isinstance(qry_exps[0], Experiment)
        assert source in ['WGCNA', 'RegNet', 'PathNR']

        if source == 'PathNR':
            sets = GeneSets.objects.filter(source__in=['GO', 'MSigDB'], core_set=True, repr_set=True)
        else:
            sets = GeneSets.objects.filter(source=source, core_set=True)

        logger.debug('Performing similarity analysis on method %s with %s gene sets', source, len(sets))
        sets_ids = [x.id for x in sets]
        ref_scores = Vividict()

        if source == 'WGCNA':
            ref = ModuleScores.objects.filter(module__in=sets)
            for o in ref:
                ref_scores[o.experiment_id][o.module_id] = float(o.score)

        elif source == 'RegNet' or source == 'PathNR':
            ref = GSAScores.objects.filter(geneset__in=sets)
            for o in ref:
                ref_scores[o.experiment_id][o.geneset_id] = float(o.score)

        else:
            raise NotImplementedError

        if not ref_scores:
            logger.critical('Did not retrieve any scores of type %s; empty database?', source)
            return

        results = Vividict()

        for qry_exp in qry_exps:

            if ref_scores.get(qry_exp.id, None) is None:
                logger.error('Did not retrieve scores of type %s for experiment %s', source, qry_exp.experiment_name)
                return

            sorted_qry_scores = list()
            # sublist to use for this set of calculations in case some features are missing; can happen in cases where
            # uploaded experiment does not contain data for all genes
            this_sets_ids = list()
            for i in sets_ids:
                if ref_scores[qry_exp.id].get(i, None) is None:
                    logger.warning('Missing core feature %s of type %s in correlation calc of query experiment %s; removing feature', i, source, qry_exp.id)
                else:
                    this_sets_ids.append(i)
                    sorted_qry_scores.append(ref_scores[qry_exp.id][i])

            for ref_exp_id in ref_scores:

                n_zeroed = 0
                n = 0

                if qry_exp.id == ref_exp_id:
                    continue

                sorted_ref_scores = list()

                for i in this_sets_ids:
                    n += 1
                    if ref_scores[ref_exp_id].get(i, None) is None:
                        logger.debug('Missing core feature %s of type %s in correlation calc of experiment %s; setting to 0', i, source, ref_exp_id)
                        val = 0
                        n_zeroed += 1
                    else:
                        val = ref_scores[ref_exp_id][i]
                    sorted_ref_scores.append(val)

                # if more than 20% of the core gene sets are not defined for a given ref exps, skip
                if n_zeroed/n > 0.2:
                    logger.error('More than 20 percent of the core gene sets (%s genesets) for experiment %s dont have a stored value for method %s; something wrong', n_zeroed, ref_exp_id, source)
                    continue

                #logger.debug('Evaluating correl between query exp %s and ref exp %s', qry_exp.id, ref_exp_id)
                correl, pval = pearsonr(sorted_qry_scores, sorted_ref_scores)
                results[qry_exp.id][ref_exp_id] = correl

        return results

    def calc_geneset_correl(self, source1, source2):
        """
        Action: Calculates the correlation between genesets
        Returns: correlations

        """
        sources = [source1, source2]
        allscores = Vividict()

        tg_exps = Experiment.objects.filter(study__source='TG')
        tg_exp_ids = [x.id for x in tg_exps]

        for source in sources:

            assert source in ['WGCNA', 'RegNet', 'PathNR', 'EPA']

            if source == 'PathNR':
                sets = GeneSets.objects.filter(source__in=['GO', 'MSigDB'], core_set=True, repr_set=True)
            else:
                sets = GeneSets.objects.filter(source=source, core_set=True)

            logger.debug('Retrieving all TG scores for %s', source)

            if source == 'WGCNA':
                scores = ModuleScores.objects.filter(module__in=sets, experiment__in=tg_exps)
                for s in scores:
                    allscores[source][s.module_id][s.experiment_id] = float(s.score)
            elif source == 'RegNet' or source == 'PathNR' or source == 'EPA':
                scores = GSAScores.objects.filter(geneset__in=sets, experiment__in=tg_exps)
                for s in scores:
                    allscores[source][s.geneset_id][s.experiment_id] = float(s.score)
            else:
                raise NotImplementedError

        if not allscores:
            logger.critical('Did not retrieve any scores of type %s vs %s; empty database?', source1, source2)
            return

        results = Vividict()
        n_zeroed = 0

        for gs1 in allscores[source1]:
            gs1_scores = list()
            for exp_id in tg_exp_ids:
                s = allscores[source1][gs1].get(exp_id, None)
                if s is None:
                    logger.error('Did not retrieve scores for source and geneset %s and %s, zeroing', source1, gs1)
                    s = 0
                    n_zeroed += 1

                gs1_scores.append(s)

            for gs2 in allscores[source2]:
                gs2_scores = list()
                for exp_id in tg_exp_ids:
                    s = allscores[source2][gs2].get(exp_id, None)
                    if s is None:
                        logger.error('Did not retrieve scores for source and geneset %s and %s, zeroing', source2, gs2)
                        s = 0
                        n_zeroed += 1

                    gs2_scores.append(s)

                correl, pval = pearsonr(gs1_scores, gs2_scores)
                results[gs1][gs2] = correl

        return results

    def get_BMD_calcs(self, exp_objs):

        logger.info('Identifying BMD calcs for experiments %s', [e.id for e in exp_objs])

        # need to organize experiments by compound, time, tissue - etc. i.e. a strict dose response under
        # otherwise identical conditions

        # tabulate a list of meta data attributes that varies across the experiments
        varying_attr = collections.defaultdict(list)
        bmd_grps = collections.defaultdict(dict)
        bmd_calcs = collections.defaultdict(dict)

        for e in exp_objs:
            for attr in ['tech', 'time', 'tissue', 'organism', 'strain', 'gender', 'single_repeat_type', 'route', 'compound_name', 'dose_unit']:
                val = getattr(e, attr)
                if val not in varying_attr[attr]:
                    varying_attr[attr].append(val)

        # delete experiment attributes which are shared by all experiments - no need showing them to users
        # Don't delete compound as a singlet attribute.  We want to do a BMD calc for a set of experiments where
        # cpd is the same for all
        attrs = list(varying_attr.keys())
        for attr in attrs:
            if len(varying_attr[attr]) == 1 and attr != 'compound_name':
                del varying_attr[attr]
                continue

        # create a list of all unique combinations of varying attributes encountered in experiments set
        keys, values = zip(*varying_attr.items())
        for val in itertools.product(*values):
            combo = dict(zip(keys, val))
            logger.debug('Identifying experiments matching conditions %s', combo)
            these_exp_objs = filter(lambda item: all((getattr(item, k) == v for (k, v) in combo.items())), exp_objs)

            calc = dict()
            for e in these_exp_objs:
                logger.debug('Have exp %s which matches condition', e.id)
                conc = float(e.dose)
                if calc.get(conc, None) is not None:
                    raise NotImplemented('Did not anticipate multiple experiments having same concentration for a BMD condition; report to developer')
                calc[conc] = e.id

            # some combos of conditions have no experiments; e.g. repeat dose study vs. <= 1 day duration in TG data
            if not calc:
                continue
            if len(calc) < 3:
                logger.debug('Fewer then 3 doses for condition %s; no BMD calc', combo)
                continue

            cnd = ''
            for attr in combo:
                cnd += '-' if cnd else ''
                cnd += attr + '=' + str(combo[attr])

            bmd_calcs[cnd] = calc

        return bmd_calcs

    def make_BMD_files(self, exp_objs, config_file, sample_int, fc_data):

        logger.info('Preparing BMD input files for experiments %s', [e.id for e in exp_objs])

        bmd_calcs = self.get_BMD_calcs(exp_objs)
        # many user studies will not have multiple conc, hence BMD not possible
        if not bmd_calcs:
            return None

        with open(config_file) as infile:
            config = json.load(infile)

        # fc_data contains the mapping from original platform-specific identifier to rat entrez gene
        # BMD will be run on rat refseq to avoid having to select a BMD-supported platform
        identifier_map = Vividict()
        for exp_id in fc_data:
            for rat_entrez in fc_data[exp_id]:
                identifier_map[exp_id][fc_data[exp_id][rat_entrez]['identifier']] = rat_entrez

        sample2exp = dict()
        for e in config['experiments']:
            for s in e['sample']:
                sample2exp[s['sample_name']] = e['experiment']['exp_id']

        identifier2ensembl = dict()

        # take the sample intensities object and build a convertion table to rat entrez
        for sample_nm in sample_int['samples']:
            count = 0
            for identifier in sample_int['genes']:
                exp_id = sample2exp[sample_nm]
                # not all platform identifiers are convertable to rat entrez
                rat_eg = identifier_map[exp_id].get(identifier, None)
                if rat_eg is None:
                    continue

                gene_obj = self.get_gene_obj(rat_eg)
                # some rat entrez gene IDs don't have a ensembl rn6 ID avail
                if not gene_obj.ensembl_rn6:
                    continue

                if identifier2ensembl.get(identifier, None) is not None and identifier2ensembl[identifier] != gene_obj.ensembl_rn6:
                    raise NotImplemented('Did not anticipate possibility that identifier vs rat eg is not unique without considering sample')

                identifier2ensembl[identifier] = gene_obj.ensembl_rn6

        if not identifier2ensembl:
            raise ValueError('No mappings from gene to Ensembl obtained')

        # a user might be uploading experiments where not all of conditions required for
        # performing BMD are the same across all experiments, i.e. different time points
        # iterate through each set of experiments where the req'd conditions are the same
        filenames = list()
        for cond in bmd_calcs:
            conc2sample = collections.defaultdict(list)
            for conc, exp_id in bmd_calcs[cond].items():
                for e in config['experiments']:
                    if e['experiment']['exp_id'] == exp_id:
                        for s in e['sample']:
                            use_conc = float(conc) if s['sample_type'] == 'I' else 0
                            if not s['sample_name'] in conc2sample[use_conc]:
                                conc2sample[use_conc].append(s['sample_name'])

            if not conc2sample:
                raise LookupError('Did not match any of concentration/experiments in bmd_config to experiments')

            filename = os.path.join(self.tmpdir, 'bmd_input-' + cond + '.txt')
            with open(filename, 'w') as bmd_f:

                head1 = 'SampleID'
                head2 = 'Dose'
                firstrow = True
                genecount = -1  # need to make sure that platform identifiers not mappable to rat eg get incremented

                already_have = dict()
                warned_dups = dict()

                for gene in sample_int['genes']:

                    genecount += 1
                    refseq = identifier2ensembl.get(gene, None)
                    if refseq is None:
                        continue

                    if already_have.get(refseq, None) is not None:
                        if warned_dups.get(refseq, None) is None:
                            logger.warning('Multiple input genes map to the same rat ensemble gene %s; keeping first only', refseq)
                            warned_dups[refseq] = 1
                        continue

                    already_have[refseq] = 1

                    row = str(refseq)
                    for conc in sorted(conc2sample):
                        for sample_nm in sorted(conc2sample[conc]):
                            if firstrow:
                                head1 += '\t' + sample_nm
                                head2 += '\t' + str(conc)

                            # TODO - in gfffactors.py; expression values are stored as lists for array and dict for rna-seq; needs refactor
                            if config['file_type'] == 'RNAseq':
                                expression = sample_int['values'][sample_nm][gene]
                            else:
                                expression = sample_int['values'][sample_nm][genecount]

                            row += '\t' + str(expression)

                    if firstrow:
                        head1 += '\n'
                        head2 += '\n'
                        bmd_f.write(head1)
                        bmd_f.write(head2)
                        firstrow = False

                    row += '\n'
                    bmd_f.write(row)

            bmd_f.close()
            filenames.append(filename)

        return filenames

    def run_BMD(self, files, test_mode=False):

        config = tp.utils.parse_config_file()
        bmd_config_file_template = os.path.join(settings.BASE_DIR, config['DEFAULT']['bmd_config'])

        with open(bmd_config_file_template) as infile:
            bmd_config_ref = json.load(infile)

        # update the master configuration to point to appropriate locations for BMD defined category analysis
        r = bmd_config_ref['categoryAnalysisConfigs'][2]
        r['probeFilePath'] = os.path.join(settings.BASE_DIR, config['DEFAULT']['bmd_defined_analysis_probes'])
        r['categoryFilePath'] = os.path.join(settings.BASE_DIR, config['DEFAULT']['bmd_defined_analysis_categories'])
        assert os.path.isfile(r['probeFilePath'])
        assert os.path.isfile(r['categoryFilePath'])

        bmd_config = copy.deepcopy(bmd_config_ref)
        bmd_config['bm2FileName'] = os.path.join(self.tmpdir, 'bmd_results.bm2')
        bmd_config['expressionDataConfigs'] = []
        bmd_config['preFilterConfigs'] = []
        bmd_config['bmdsConfigs'] = []
        bmd_config['categoryAnalysisConfigs'] = []

        for f in files:
            base = os.path.basename(f)
            no_ext = os.path.splitext(base)[0]
            no_ext = no_ext.replace('bmd_input-', '')  # drop the file prefix

            input_stub = copy.deepcopy(bmd_config_ref['expressionDataConfigs'][0])
            prefilter_stub = copy.deepcopy(bmd_config_ref['preFilterConfigs'][0])
            bmds_stub = copy.deepcopy(bmd_config_ref['bmdsConfigs'][0])
            # eliminate all but the first two model fitting types to speed things up in test mode
            if test_mode:
                bmds_stub['modelConfigs'] = bmds_stub['modelConfigs'][:1]

            go_stub = copy.deepcopy(bmd_config_ref['categoryAnalysisConfigs'][0])
            path_stub = copy.deepcopy(bmd_config_ref['categoryAnalysisConfigs'][1])
            defined_cat_stub = copy.deepcopy(bmd_config_ref['categoryAnalysisConfigs'][2])

            # populate the expressionDataConfigs section
            input_stub['inputFileName'] = f
            input_stub['outputName'] = no_ext
            bmd_config['expressionDataConfigs'].append(input_stub)

            # populate the expressionDataConfigs section
            # NOTE - currently does not support multiple filtering strategies
            analysis_type = prefilter_stub['@type']
            prefilter_stub['inputName'] = no_ext
            prefilter_stub['outputName'] = no_ext + '_' + analysis_type
            bmd_config['preFilterConfigs'].append(prefilter_stub)

            # populate the bmdsConfigs section
            bmds_stub['inputCategory'] = analysis_type
            bmds_stub['inputName'] = no_ext + '_' + analysis_type
            bmds_stub['outputName'] = no_ext + '_' + analysis_type + '_bmds'
            bmd_config['bmdsConfigs'].append(bmds_stub)

            # populate the categoryAnalysisConfigs section - GO and pathway
            go_stub['inputName'] = no_ext + '_' + analysis_type + '_bmds'
            go_stub['outputName'] = no_ext + '_' + analysis_type + '_bmds_GOuniversal'
            path_stub['inputName'] = no_ext + '_' + analysis_type + '_bmds'
            path_stub['outputName'] = no_ext + '_' + analysis_type + '_bmds_REACTOME'
            defined_cat_stub['inputName'] = no_ext + '_' + analysis_type + '_bmds'
            defined_cat_stub['outputName'] = no_ext + '_' + analysis_type + '_bmds_modules'
            bmd_config['categoryAnalysisConfigs'].append(go_stub)
            bmd_config['categoryAnalysisConfigs'].append(path_stub)
            bmd_config['categoryAnalysisConfigs'].append(defined_cat_stub)

        bmd_config_file = os.path.join(self.tmpdir, 'toxapp_bmd_input_file.json')
        with open(bmd_config_file, 'w') as outfile:
            json.dump(bmd_config, outfile)

        # run the BMD analysis - slow
        runcmd = config['DEFAULT']['bmd_exec'] + ' analyze --config-file=' + bmd_config_file
        logger.debug('Running BMD as %s', runcmd)
        output = subprocess.getoutput(runcmd)
        logger.debug('Have BMD output %s', output)

        if not os.path.isfile(bmd_config['bm2FileName']):
            logger.error('Expected file %s not produced by BMD run from command %s; output is %s', bmd_config['bm2FileName'], runcmd, output)

        # export the categorical results in tab-delim format
        export_file = os.path.join(self.tmpdir, '{}.txt'.format(hash(time.time())))
        logger.debug('Have temporary BMD export file %s', export_file)
        exportcmd = config['DEFAULT']['bmd_exec'] + ' export --analysis-group categorical --input-bm2 ' +\
            bmd_config['bm2FileName'] + ' --output-file-name ' + export_file
        logger.debug('Exporting BMD results as %s', exportcmd)
        output = subprocess.getoutput(exportcmd)
        logger.debug('Have BMD export output %s', output)

        if not os.path.isfile(export_file) or os.path.getsize(export_file) < 1000000:
            logger.error('Expected file %s not produced by BMD export; output is %s',export_file, output)

        return bmd_config['bm2FileName'], export_file

    def parse_BMD_results(self, export_file):

        assert os.path.isfile(export_file)

        # create lookup from the verbose names (which are in the BMD results file) to model field names
        req_attr = dict()
        results = list()
        for f in BMDPathwayResult._meta.get_fields():
            if f.name in ['id', 'experiment']:
                continue
            elif f.name == 'analysis':  # no great way to force mapping to Foreign Key
                req_attr['Analysis'] = 'analysis'
            else:
                req_attr[f.verbose_name] = f.name

        with open(export_file) as f:
            next(f)  # the first line is blank in bmd export file
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:

                # BMD express can return zero values, and when plotting on log scale these cause problems
                if row['BMD Median'] == '0':
                    row['BMD Median'] = '0.001'

                if row['BMDL Median'] == '0':
                    row['BMDL Median'] = '0.001'

                if row['Genes That Passed All Filters'] == '0':
                    continue

                for i in req_attr:
                    if row[i] == '':
                        logger.error('File %s contains undefined values for attribute %s on line %s',
                                     export_file, i, row)
                        return None

                result = dict()
                for verbose_field in req_attr:
                    model_field_name = req_attr[verbose_field]
                    result[model_field_name] = row[verbose_field]

                results.append(result)

        return results

