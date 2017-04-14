from tp.models import MeasurementTech


import pprint
import json
import shutil
import logging
import os
import csv


logger = logging.getLogger(__name__)

class Computation:

    def calc_fold_change(self, tmpdir, config):
        """ calculate group fold change from files in tmpdir and meta data received from webapp in config json file """

        #TODO - this is where Dan/Meeta plug in group fold change calc
        logger.info('Starting fold change calculation in directory %s using config %s', tmpdir, config)
        file = tmpdir + '/groupFC.txt'
        logger.info('Done fold change calculation; results in %s', file)
        return file
