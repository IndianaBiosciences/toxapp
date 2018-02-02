from tp.models import MeasurementTech, IdentifierVsGeneMap, Experiment, FoldChangeResult, GeneSets, ModuleScores,\
    GSAScores, Gene, GeneSetMember
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
        self.gsa_gsc_obj = None
        self._experiment_tech_map = dict()
        self._expid_obj_map = dict()
        self._identifier_obj_map = dict()
        self._gene_obj_map = dict()

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
        script_cmd = "cd "+tmpdir+'; '+sys.executable+' '+script+" -i "+cfg_file+" -o "+outfile
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
        gmt = NamedTemporaryFile(delete=False, suffix='.gmt', dir=self.tmpdir)
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
                    logger.error('File %s contains undefined values for one or more required attributes %s on line %s', fc_file, ",".join(req_attr), row)
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
