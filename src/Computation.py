from tp.models import GeneIdentiferMap


import pprint
import json
import shutil
import logging
import os
import csv


logger = logging.getLogger(__name__)

class Computation:

    def calc_fold_change(self, tmpdir, config):

        logger.info('Starting fold change calculation in directory %s using config %s', tmpdir, config)
        file = tmpdir + '/groupFC.txt'
        logger.info('Done fold change calculation; results in %s', file)
        return file

    def load_gene_identifier_to_rat_entrez_map(self, tech_detail):
        """ load the map which converts array or RNAseq identifers to rat entrez genes """


