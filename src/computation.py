from tp.models import MeasurementTech, IdentifierVsGeneMap, Experiment, FoldChangeResult, GeneSets, ModuleScores, GSAScores
from django.conf import settings
from tempfile import NamedTemporaryFile
from scipy.stats.stats import pearsonr

import pprint
import shutil
import json
import subprocess
import logging
import os
import sys
import csv
import collections
import rpy2.robjects as robjects
from rpy2.robjects.packages import importr

logger = logging.getLogger(__name__)


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
        self.gsa_info = None
        self.gsa_file = None
        self.gsa_gsc_obj = None
        self._experiment_tech_map = dict()
        self._expid_obj_map = dict()
        self._identifier_obj_map = dict()

    def map_fold_change_from_exp(self, exp_obj):

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
        script_cmd = "cd "+tmpdir+'; '+sys.executable+' '+script+" -i "+cfg_file+" -o "+outfile
        file = os.path.join(tmpdir, outfile)
        logger.info("command %s ", script_cmd)
        output = subprocess.getoutput(script_cmd)
#        TODO remove once meeta script running
#        file = self.tmpdir + '/groupFC.txt'
#        src = settings.BASE_DIR + '/data/sample_fc_data_DM_gemfibrozil_1d_7d_100mg_700_mg.txt'
#        shutil.copyfile(src, file)

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
                    logger.error('File %s contains undefined values for one or more required attributes %s', module_file, ",".join(req_attr_m))
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
                    logger.error('File %s contains undefined values for one or more required attributes %s', genestats_file, ",".join(req_attr_g))
                    return None

                system = ":".join([row['tissue'], row['organism'], row['tech'], row['tech_detail']])
                gs[system][row['identifier']] = {'mean_fc': float(row['mean_fc']), 'stdev_fc': float(row['stdev_fc']), 'source': row['source']}

        #logger.debug('Read following gene identifier stats from file %s: %s', genestats_file, pprint.pformat(gs, indent=4))

        setattr(self, 'gene_identifier_stats', gs)
        setattr(self, 'gene_identifier_stats_file', genestats_file)
        return 1

    def init_gsa(self, tech_obj):
        """ method that must be called before running GSA """

        assert isinstance(tech_obj, MeasurementTech)

        identifiers = IdentifierVsGeneMap.objects.filter(tech=tech_obj).all()
        if identifiers is None or len(identifiers) < 1000:
            logger.error('Failed to retrieve at least 1000 identifiers for measurement platform %s', tech_obj)
            return None

        # discard genes from gene sets not being measured
        keep_rat_genes = dict()
        for r in identifiers:
            keep_rat_genes[r.gene.rat_entrez_gene] = 1

        gsa_info = collections.defaultdict(dict)
        gsa_genes = collections.defaultdict(dict)

        # read in a list of core gene sets to be reported to database no matter the score
        core_gene_sets = dict()
        core_list = os.path.join(settings.BASE_DIR, 'data/core_gene_sets.txt')
        req_attr_core = ['id', 'name']
        with open(core_list) as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:

                if any(row[i] == '' for i in req_attr_core):
                    logger.error('File %s contains undefined values for one or more required attributes %s', core_list, ",".join(req_attr_core))
                    return None

                core_gene_sets[row['id']] = 1

        # read GO vs. gene pairs from flat file
        go_file = os.path.join(settings.BASE_DIR, 'data/rgd_vs_GO_expansion.txt')
        req_attr_go = ['entrez_gene_id', 'GO_id', 'GO_name', 'GO_type']
        with open(go_file) as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:

                if any(row[i] == '' for i in req_attr_go):
                    logger.error('File %s contains undefined values for one or more required attributes %s', go_file, ",".join(req_attr_go))
                    return None

                rat_entrez_gene = int(row['entrez_gene_id'])
                if keep_rat_genes.get(rat_entrez_gene, None) is None:
                    continue

                gsa_genes[row['GO_id']][row['entrez_gene_id']] = 1

                if not row['GO_id'] in gsa_info:
                    core_set = True if core_gene_sets.get(row['GO_id'], None) is not None else False
                    gsa_info[row['GO_id']] = {'desc': row['GO_name'], 'type': row['GO_type'],
                                              'core_set': core_set, 'source': 'GO'}

        # read MSigDB signature vs. gene pairs from flat file
        msigdb_file = os.path.join(settings.BASE_DIR, 'data/MSigDB_and_TF_annotation.txt')
        req_attr_msigdb = ['sig_name', 'rat_entrez_gene', 'sub_category', 'description']
        with open(msigdb_file) as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:

                if any(row[i] == '' for i in req_attr_msigdb):
                    logger.error('File %s contains undefined values for one or more required attributes %s', msigdb_file, ",".join(req_attr_msigdb))
                    return None

                rat_entrez_gene = int(row['rat_entrez_gene'])
                if keep_rat_genes.get(rat_entrez_gene, None) is None:
                    continue

                source = 'MSigDB'
                # DAS RegNet networks included in this file - use a separate source for these, not MSigDB
                if row['sub_category'] == 'RegNet':
                    source = 'RegNet'

                gsa_genes[row['sig_name']][rat_entrez_gene] = 1
                if not row['sig_name'] in gsa_info:
                    core_set = True if core_gene_sets.get(row['sig_name'], None) is not None else False
                    gsa_info[row['sig_name']] = {'desc': row['description'], 'type': row['sub_category'],
                                                 'core_set': core_set, 'source': source}

        # eliminate gene sets too small / too large
        sigs_to_drop = list()
        for sig in gsa_info.keys():
            n_genes = len(gsa_genes[sig])
            if n_genes < 3 or n_genes > 5000:
                sigs_to_drop.append(sig)
                continue

        logger.debug('Eliminated %s gene sets based on size constraint', len(sigs_to_drop))
        for s in sigs_to_drop:
            gsa_info.pop(s)

        #logger.debug('Read following gene set info from files %s and %s: %s', go_file, msigdb_file, pprint.pformat(gsa_info, indent=4))
        setattr(self, 'gsa_info', gsa_info)

        # prepare file suitable for R GSA calc
        gmt = NamedTemporaryFile(delete=False, suffix='.gmt', dir=self.tmpdir)
        logger.debug('Have temporary GSA file %s', gmt.name)
        sig_count = 0
        for sig in gsa_info.keys():
            sig_count += 1
            elements = [sig, 'no_link'] + [str(g) for g in gsa_genes[sig].keys()]
            row = '\t'.join(elements) + '\n'
            row_as_bytes = str.encode(row)
            gmt.write(row_as_bytes)

            # if sig_count > 100 and logger.isEnabledFor(logging.DEBUG):
            #     logger.warning('Limited to 100 gene sets in DEBUG mode')
            #     break

        gmt.close()

        # on windows the \Users ends up being recognized as escape \U ... R on Win reads unix paths
        altname = gmt.name.replace('\\', '/')
        setattr(self, 'gsa_file', altname)

        # load packages and the gmt file
        importr('piano')
        gsc = robjects.r('loadGSC("{}")'.format(self.gsa_file))
        setattr(self, 'gsa_gsc_obj', gsc)

        return 1

    def map_fold_change_data(self, fc_file):

        """ read the fold change data and map to rat entrez gene IDs starting from a file """

        # TODO - this could be retired by using the map_fold_change_from_exp as we are effectively doing the same
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
        req_attr = ['experiment', 'gene_identifier', 'log2_fc']
        with open(fc_file) as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                if any(row[i] == '' for i in req_attr):
                    logger.error('File %s contains undefined values for one or more required attributes %s', fc_file, ",".join(req_attr))
                    return None

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
                identifier = fc_data[exp_id][gene]['identifier']
                if gs[systech].get(identifier, None) is None:
                    if warned_scaling.get(identifier, None) is None:
                        logger.warning('No scaling data for gene identifier %s for system %s; skipping', identifier, systech)
                        warned_scaling[identifier] = 1
                    continue

                stdev_fc = gs[systech][identifier]['stdev_fc']
                fc_scaled = fc_data[exp_id][gene]['log2_fc']/stdev_fc
                scaled_fc[gene] = fc_scaled

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

    def score_gsa(self, fc_data, last_tech=None):

        """ use data mapped to entrez gene for calculating module scores"""

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
                success = self.init_gsa(this_tech)
                if not success:
                    logger.error('Failed to initiatize module calculation')
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
                if self.gsa_info.get(sig, None) is None:
                    logger.error('No info on gene set %s; did R mangle name?', sig)
                    continue

                score = scores[i]
                # the p-value to use is the one corresponding to direction of change (induction/repression) conveyed by z-score
                p = p_adj_up[i] if score >=0 else p_adj_down[i]

                # only store non-significant results for the core liver-relevant set
                if p > 0.1 and not self.gsa_info[sig]['core_set']:
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

    def calc_exp_correl(self, qry_exps, source):

        assert isinstance(qry_exps[0], Experiment)
        assert source in ['WGCNA', 'RegNet']

        sets = GeneSets.objects.filter(source=source, core_set=True)
        logger.debug('Performing similarity analysis on method %s with %s gene sets', source, len(sets))
        sets_ids = [x.id for x in sets]
        ref_scores = Vividict()

        if source == 'WGCNA':
            ref = ModuleScores.objects.filter(module__in=sets)
            for o in ref:
                ref_scores[o.experiment_id][o.module_id] = float(o.score)

        elif source == 'RegNet':
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
                    logger.warning('Missing core feature %s in correlation calc of query experiment %s; removing feature', i, qry_exp.id)
                else:
                    this_sets_ids.append(i)
                    sorted_qry_scores.append(ref_scores[qry_exp.id][i])

            for ref_exp_id in ref_scores:

                if qry_exp.id == ref_exp_id:
                    continue

                sorted_ref_scores = list()

                for i in this_sets_ids:
                    val = None
                    if ref_scores[ref_exp_id].get(i, None) is None:
                        logger.warning('Missing core feature %s in correlation calc of experiment %s; setting to 0', i, ref_exp_id)
                        val = 0
                    else:
                        val = ref_scores[ref_exp_id][i]
                    sorted_ref_scores.append(val)

                #logger.debug('Evaluating correl between query exp %s and ref exp %s', qry_exp.id, ref_exp_id)
                correl, pval = pearsonr(sorted_qry_scores, sorted_ref_scores)
                results[qry_exp.id][ref_exp_id] = correl

        return results
