from tp.models import MeasurementTech, IdentifierVsGeneMap
from django.conf import settings
from tempfile import NamedTemporaryFile
from pandas import DataFrame, read_csv

import pprint
import shutil
import logging
import os
import csv
import collections
import pandas as pd


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
                md[system][row['module']]['genes'][row['rat_entrez_gene_id']] = row['loading']
                md[system][row['module']]['stdev'] = row['pc1_stdev']

        logger.debug('Read following module defs from file %s: %s', module_file, pprint.pformat(md, indent=4))

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
                gs[system][row['identifier']] = {'mean_fc':row['mean_fc'], 'stdev_fc':row['stdev_fc'], 'source':row['source']}

        logger.debug('Read following gene identifier stats from file %s: %s', genestats_file, pprint.pformat(gs, indent=4))

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


        logger.debug('Have following rat entrez genes to keep: %s', keep_rat_genes)
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

                if keep_rat_genes.get(row['rat_entrez_gene'], None) is None:
                    continue

                gsa_genes[row['sig_name']][row['rat_entrez_gene']] = 1
                if not row['sig_name'] in gsa_info:
                    gsa_info[row['sig_name']] = {'name': row['sig_name'], 'type': row['sub_category'], 'desc': row['description']}

        # eliminate gene sets too small / too large
        sigs_to_drop = []
        for sig in gsa_info.keys():
            n_genes = len(gsa_genes[sig])
            if n_genes < 3 or n_genes > 5000:
                sigs_to_drop.append(sig)

        logger.debug('Eliminated %s gene sets based on size constraint', len(sigs_to_drop))
        for s in sigs_to_drop:
            gsa_info.pop(s)

        logger.debug('Read following gene set info from files %s and %s: %s', go_file, msigdb_file, pprint.pformat(gsa_info, indent=4))
        setattr(self, 'gsa_info', gsa_info)

        # prepare file suitable for R GSA calc
        gmt = NamedTemporaryFile(delete=False, suffix='.gmt', dir=self.tmpdir)
        #gmt = NamedTemporaryFile(delete=False, suffix='.gmt') # works on windows
        logger.debug('Have temporary GSA file %s', gmt.name)
        for sig in gsa_info.keys():
            elements = [sig, 'no_link'] + list(gsa_genes[sig].keys())
            row = '\t'.join(elements) + '\n'
            row_as_bytes = str.encode(row)
            gmt.write(row_as_bytes)
        gmt.close()

        setattr(self, 'gsa_file', gmt.name)
        return 1
