from tp.models import MeasurementTech, IdentifierVsGeneMap, Experiment
from django.conf import settings
from tempfile import NamedTemporaryFile

import pprint
import shutil
import logging
import os
import csv
import collections


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

    def calc_fold_change(self, config):
        """ calculate group fold change from files in tmpdir and meta data received from webapp in config json file """

        #TODO - this is where Dan/Meeta plug in group fold change calc
        logger.info('Starting fold change calculation in directory %s using config %s', self.tmpdir, config)
        file = self.tmpdir + '/groupFC.txt'

        # TODO remove once meeta script running
        src = settings.BASE_DIR + '/data/sample_fc_data_DM_gemfibrozil_1d_7d_100mg_700_mg.txt'
        shutil.copyfile(src, file)

        logger.info('Done fold change calculation; results in %s', file)
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

                if any(row[i] == '' for i in req_attr_m ):
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
                gs[system][row['identifier']] = {'mean_fc':float(row['mean_fc']), 'stdev_fc':float(row['stdev_fc']), 'source':row['source']}

        #logger.debug('Read following gene identifier stats from file %s: %s', genestats_file, pprint.pformat(gs, indent=4))

        setattr(self, 'gene_identifier_stats', gs)
        setattr(self, 'gene_identifier_stats_file', genestats_file)
        return 1

    def init_gsa(self, tech, tech_detail):
        """ method that must be called before running GSA """

        tech_obj = MeasurementTech.objects.filter(tech=tech, tech_detail=tech_detail).first()
        if tech_obj is None:
            logger.error('Did not retrieve existing measurement tech for %s and %s', tech, tech_detail)
            return None

        identifiers = IdentifierVsGeneMap.objects.filter(tech=tech_obj).all()
        if identifiers is None or len(identifiers) < 1000:
            logger.error('Failed to retrieve at least 1000 identifiers for measurement platform %s-%s', tech, tech_detail)
            return None

        # discard genes from gene sets not being measured
        keep_rat_genes = dict()
        for r in identifiers:
            keep_rat_genes[r.rat_entrez_gene] = 1

        gsa_info = collections.defaultdict(dict)
        gsa_genes = collections.defaultdict(dict)

        # read GO vs. gene pairs from flat file
        go_file = os.path.join(settings.BASE_DIR, 'data/rgd_vs_GO_expansion.txt')
        req_attr_go = ['entrez_gene_id', 'GO_id', 'GO_name', 'GO_type']
        with open(go_file) as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:

                if any(row[i] == '' for i in req_attr_go ):
                    logger.error('File %s contains undefined values for one or more required attributes %s', go_file, ",".join(req_attr_go))
                    return None

                if keep_rat_genes.get(row['entrez_gene_id'], None) is None:
                    continue

                gsa_genes[row['GO_id']][row['entrez_gene_id']] = 1
                if not row['GO_id'] in gsa_info:
                    gsa_info[row['GO_id']] = {'name': row['GO_name'], 'type': row['GO_type']}

        # read MSigDB signature vs. gene pairs from flat file
        msigdb_file = os.path.join(settings.BASE_DIR, 'data/MSigDB_and_TF_annotation.txt')
        req_attr_msigdb = ['sig_name', 'rat_entrez_gene', 'sub_category', 'description']
        with open(msigdb_file) as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:

                if any(row[i] == '' for i in req_attr_msigdb ):
                    logger.error('File %s contains undefined values for one or more required attributes %s', msigdb_file, ",".join(req_attr_msigdb))
                    return None

                rat_entrez_gene = int(row['rat_entrez_gene'])
                if keep_rat_genes.get(rat_entrez_gene, None) is None:
                    continue

                gsa_genes[row['sig_name']][rat_entrez_gene] = 1
                if not row['sig_name'] in gsa_info:
                    gsa_info[row['sig_name']] = {'name': row['sig_name'], 'type': row['sub_category'], 'desc': row['description']}

        # eliminate gene sets too small / too large
        sigs_to_drop = list()
        for sig in gsa_info.keys():
            n_genes = len(gsa_genes[sig])
            if n_genes < 3 or n_genes > 5000:
                sigs_to_drop.append(sig)

        logger.debug('Eliminated %s gene sets based on size constraint', len(sigs_to_drop))
        for s in sigs_to_drop:
            gsa_info.pop(s)

        #logger.debug('Read following gene set info from files %s and %s: %s', go_file, msigdb_file, pprint.pformat(gsa_info, indent=4))
        setattr(self, 'gsa_info', gsa_info)

        # prepare file suitable for R GSA calc
        gmt = NamedTemporaryFile(delete=False, suffix='.gmt', dir=self.tmpdir)
        logger.debug('Have temporary GSA file %s', gmt.name)
        for sig in gsa_info.keys():
            elements = [sig, 'no_link'] + [str(g) for g in gsa_genes[sig].keys()]
            row = '\t'.join(elements) + '\n'
            row_as_bytes = str.encode(row)
            gmt.write(row_as_bytes)
        gmt.close()

        setattr(self, 'gsa_file', gmt.name)
        return 1

    def map_fold_change_data(self, tech, tech_detail, fc_file):

        """ read the fold change data and map to rat entrez gene IDs"""

        tech_obj = MeasurementTech.objects.filter(tech=tech, tech_detail=tech_detail).first()
        if tech_obj is None:
            logger.error('Did not retrieve existing measurement tech for %s and %s', tech, tech_detail)
            return None

        identifiers = IdentifierVsGeneMap.objects.filter(tech=tech_obj).all()
        if identifiers is None or len(identifiers) < 1000:
            logger.error('Failed to retrieve at least 1000 identifiers for measurement platform %s-%s', tech, tech_detail)
            return None

        # map for converting measurement platform identifiers to rat entrez gene IDs
        identifier_map = dict()
        for r in identifiers:
            identifier_map[r.gene_identifier] = r.rat_entrez_gene

        # track identifiers that failed to convert to rat entrez
        failed_map = dict()

        # dictionary of log2 fc results keyed on experiment / gene identifier
        fc_data = collections.defaultdict(dict)

        # read the fold change data
        req_attr = ['experiment', 'gene_identifier', 'log2_fc']
        with open(fc_file) as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:

                if any(row[i] == '' for i in req_attr ):
                    logger.error('File %s contains undefined values for one or more required attributes %s', fc_file, ",".join(req_attr))
                    return None

                rat_entrez = identifier_map.get(row['gene_identifier'], None)
                exp = int(row['experiment'])

                if rat_entrez is None:
                    failed_map[row['gene_identifier']] = 1
                    continue

                if rat_entrez in fc_data.get(exp, {}):
                    logger.error('Data already defined for experiment %s and rat entrez gene %s; multiple gene identifers for same gene?', exp, rat_entrez)
                    continue

                fc_data[exp][rat_entrez] = {'log2_fc': float(row['log2_fc']), 'identifier': row['gene_identifier']}

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

            try:
                exp_obj = Experiment.objects.get(pk=exp_id)
            except:
                logger.error('Failed to retrieve meta data for exp id %s; must be loaded first', exp_id)
                pass

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
                    if warned_scaling[identifier] is None:
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
                module_scores.append({'exp_id':exp_id, 'exp_obj':exp_obj, 'module':m, 'score':modsum})

                n_missing = len(warned_gene)
                ratio_missed = n_missing/n_genes
                if ratio_missed > 0.30:
                    logger.warning('Missing more than 30percent of genes (%s) for module %s of size %s; lower concern for small modules', n_missing, m, n_genes)

        logger.debug('Have results from module scoring: %s', pprint.pformat(module_scores, indent=4))
        return module_scores

