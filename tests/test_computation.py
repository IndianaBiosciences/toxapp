import os
from django.core.wsgi import get_wsgi_application
from django.conf import settings
import logging
import unittest
import tempfile
import time
import shutil
import filecmp
import pickle
import pprint

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "toxapp.settings")
application = get_wsgi_application()

from src.computation import Computation
from tp.models import Experiment, Gene, MeasurementTech, IdentifierVsGeneMap

logger = logging.getLogger(__name__)


class TestComputation(unittest.TestCase):

    def setUp(self):
        tmpdir = os.path.join(tempfile.gettempdir(), '{}'.format(hash(time.time())))
        sourcedir = os.path.join(settings.BASE_DIR, 'tests/test_data/')
        if not os.path.exists(sourcedir):
            logging.error('Test data directory %s is not readable', sourcedir)
            exit(1)

        shutil.copytree(sourcedir, tmpdir)
        logger.debug('temp directory is %s', tmpdir)
        self.tmp_dir = tmpdir
        self.compute = Computation(tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_get_exp_obj(self):
        self.assertIsInstance(self.compute.get_exp_obj(23), Experiment)

    def test_get_gene_obj(self):
        self.assertIsInstance(self.compute.get_gene_obj(24153), Gene)

    def test_get_experiment_tech_map(self):
        self.assertIsInstance(self.compute.get_experiment_tech_map(23), MeasurementTech)

    def test_get_identifier_obj(self):
        techobj = MeasurementTech.objects.get(tech_detail='RG230-2')
        self.assertIsInstance(self.compute.get_identifier_obj(techobj, '100036765_at'), IdentifierVsGeneMap)

    def test_calc_fold_change(self):
        fc_file = self.compute.calc_fold_change('computation_data.json')
        logger.debug('Have file of fold change results %s', fc_file)
        expected_file = os.path.join(settings.BASE_DIR, 'tests/test_results/groupFC-expected.txt')
        self.assertTrue(filecmp.cmp(fc_file, expected_file, shallow=False))

    def test_map_fold_change_from_exp(self):
        fc_file = os.path.join(settings.BASE_DIR, 'tests/test_results/groupFC-expected.txt')
        fc_data = self.compute.map_fold_change_data(fc_file)
        # If we got results for >1000 genes we're probably fine. Could replace actual object comparison below
        #self.assertTrue(isinstance(fc_data, dict) and len(fc_data[23]) > 1000)

        # set to True to write-out an object for saving
        saveobj = False
        if saveobj:
            with open(os.path.join(settings.BASE_DIR, 'tests/test_results/mappedFC-expected.pkl'), 'wb') as fp:
                pickle.dump(fc_data, fp, pickle.HIGHEST_PROTOCOL)

        with open(os.path.join(settings.BASE_DIR, 'tests/test_results/mappedFC-expected.pkl'), 'rb') as fp:
            expected_fc = pickle.load(fp)
        self.assertDictEqual(fc_data, expected_fc)

    def test_init_modules(self):
        self.assertTrue(self.compute.init_modules())

    def test_score_modules(self):
        with open(os.path.join(settings.BASE_DIR, 'tests/test_results/mappedFC-expected.pkl'), 'rb') as fp:
            fc_data = pickle.load(fp)

        module_scores = self.compute.score_modules(fc_data)

        saveobj = False
        if saveobj:
            with open(os.path.join(settings.BASE_DIR, 'tests/test_results/module_scores-expected.pkl'), 'wb') as fp:
                pickle.dump(module_scores, fp, pickle.HIGHEST_PROTOCOL)

        with open(os.path.join(settings.BASE_DIR, 'tests/test_results/module_scores-expected.pkl'), 'rb') as fp:
            expected_scores = pickle.load(fp)
        self.assertListEqual(module_scores, expected_scores)

    def test_make_gsa_file(self):
        techobj = MeasurementTech.objects.get(tech_detail='RG230-2')
        file = self.compute.make_gsa_file(techobj)
        expected_file = os.path.join(settings.BASE_DIR, 'tests/test_results/expected.gmt')

        savefile = False
        if savefile and file:
            shutil.copy(file, expected_file)

        self.assertTrue(filecmp.cmp(file, expected_file, shallow=False))

    def test_init_gsa(self):
        gsa_file = os.path.join(settings.BASE_DIR, 'tests/test_results/expected.gmt')
        techobj = MeasurementTech.objects.get(tech_detail='RG230-2')
        self.assertTrue(self.compute.init_gsa(techobj, gsa_file=gsa_file))

    def test_score_gsa(self):
        with open(os.path.join(settings.BASE_DIR, 'tests/test_results/mappedFC-expected.pkl'), 'rb') as fp:
            fc_data = pickle.load(fp)

        gsa_file = os.path.join(settings.BASE_DIR, 'tests/test_results/expected.gmt')
        techobj = MeasurementTech.objects.get(tech_detail='RG230-2')
        gsa_scores = self.compute.score_gsa(fc_data, gsa_file=gsa_file)

        saveobj = False
        if saveobj:
            with open(os.path.join(settings.BASE_DIR, 'tests/test_results/gsa_scores-expected.pkl'), 'wb') as fp:
                pickle.dump(gsa_scores, fp, pickle.HIGHEST_PROTOCOL)

        with open(os.path.join(settings.BASE_DIR, 'tests/test_results/gsa_scores-expected.pkl'), 'rb') as fp:
            expected_scores = pickle.load(fp)
        self.assertListEqual(gsa_scores, expected_scores)

    def test_calc_exp_correl(self):

        qry_exps = Experiment.objects.filter(id__in=[8376])

        correl_results = dict()
        correl_results['WGCNA'] = self.compute.calc_exp_correl(qry_exps, 'WGCNA')
        correl_results['RegNet'] = self.compute.calc_exp_correl(qry_exps, 'RegNet')

        logger.debug('Have the following correls: %s', pprint.pformat(correl_results))

        saveobj = False
        if saveobj:
            with open(os.path.join(settings.BASE_DIR, 'tests/test_results/correl-expected.pkl'), 'wb') as fp:
                pickle.dump(correl_results, fp, pickle.HIGHEST_PROTOCOL)

        with open(os.path.join(settings.BASE_DIR, 'tests/test_results/correl-expected.pkl'), 'rb') as fp:
            expected_scores = pickle.load(fp)
        self.assertDictEqual(correl_results, expected_scores)


if __name__ == '__main__':
    unittest.main()
