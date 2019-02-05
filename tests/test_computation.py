import os
import logging
import unittest
import tempfile
import time
import shutil
import filecmp
import pickle
import pprint

from django.core.wsgi import get_wsgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "toxapp.settings")
application = get_wsgi_application()

from django.conf import settings
from src.computation import Computation
from tp.models import Study, Experiment, Gene, MeasurementTech, IdentifierVsGeneMap

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

        # some functions expect the experiment's meta data to be in the DB.  Use experiment -1, study -1 and
        # create if necessary

        study_data = {
            'study_name': 'study created by test_computation.py script',
            'source': 'NA',
        }
        study_obj, _ = Study.objects.get_or_create(id=-1, defaults=study_data)

        try:
            tech_obj = MeasurementTech.objects.get(tech_detail='RG230-2')
        except MeasurementTech.DoesNotExist:
            logger.fatal('Could not retrieve measurement tech RG230-2; defined yet?')
            exit(1)

        exp_data = {
            'id': -1,
            'experiment_name': 'test experiment created by test_computation.py script',
            'tech': tech_obj,
            'study': study_obj,
            'compound_name': 'gemfibrozil',
            'dose': 1,
            'dose_unit': 'mg/kg',
            'time': 4,
            'tissue': 'liver',
            'organism': 'rat',
            'strain': 'Sprague Dawley',
            'gender': 'M',
            'single_repeat_type': 'repeat',
            'route': 'gavage'
        }
        exp_obj, _ = Experiment.objects.get_or_create(id=-1, defaults=exp_data)
        logger.debug('Done setup')

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_get_exp_obj(self):
        self.assertIsInstance(self.compute.get_exp_obj(-1), Experiment)

    def test_get_gene_obj(self):
        self.assertIsInstance(self.compute.get_gene_obj(24153), Gene)

    def test_get_experiment_tech_map(self):
        self.assertIsInstance(self.compute.get_experiment_tech_map(8376), MeasurementTech)

    def test_get_identifier_obj(self):
        techobj = MeasurementTech.objects.get(tech_detail='RG230-2')
        self.assertIsInstance(self.compute.get_identifier_obj(techobj, '100036765_at'), IdentifierVsGeneMap)

    def test_calc_fold_change(self):
        fc_file = self.compute.calc_fold_change('computation_data.json')
        logger.debug('Have file of fold change results %s', fc_file)
        expected_file = os.path.join(settings.BASE_DIR, 'tests/test_results/groupFC-expected.txt')
        #self.assertTrue(filecmp.cmp(fc_file, expected_file, shallow=False))
        self.assertGreater(os.path.getsize(fc_file), 1000000)

    def test_map_fold_change_from_exp(self):
        fc_file = os.path.join(settings.BASE_DIR, 'tests/test_results/groupFC-expected.txt')
        fc_data = self.compute.map_fold_change_data(fc_file)
        # If we got results for >1000 genes we're probably fine. Could replace actual object comparison below
        self.assertTrue(isinstance(fc_data, dict))
        self.assertGreater(len(fc_data[-1]), 1000)

        # TODO - well, Jeff thought the pickling would be fine - but there are small floating point diffs, even on the same
        # machine over time.  So comparison at object level would require additional coding to round diffs before
        # set to True to write-out an object for saving; revisit later and see if a general function that travels the
        # object from top to bottom and rounds would work

        saveobj = False
        if saveobj:
            with open(os.path.join(settings.BASE_DIR, 'tests/test_results/mappedFC-expected.pkl'), 'wb') as fp:
                pickle.dump(fc_data, fp, pickle.HIGHEST_PROTOCOL)

        #with open(os.path.join(settings.BASE_DIR, 'tests/test_results/mappedFC-expected.pkl'), 'rb') as fp:
        #    expected_fc = pickle.load(fp)
        #self.assertDictEqual(fc_data, expected_fc)

    def test_init_modules(self):
        self.assertTrue(self.compute.init_modules())

    def test_score_modules(self):
        with open(os.path.join(settings.BASE_DIR, 'tests/test_results/mappedFC-expected.pkl'), 'rb') as fp:
            fc_data = pickle.load(fp)

        module_scores = self.compute.score_modules(fc_data)
        self.assertTrue(isinstance(module_scores, list))
        self.assertGreater(len(module_scores), 400)

        saveobj = False
        if saveobj:
            with open(os.path.join(settings.BASE_DIR, 'tests/test_results/module_scores-expected.pkl'), 'wb') as fp:
                pickle.dump(module_scores, fp, pickle.HIGHEST_PROTOCOL)

        #with open(os.path.join(settings.BASE_DIR, 'tests/test_results/module_scores-expected.pkl'), 'rb') as fp:
        #    expected_scores = pickle.load(fp)
        #self.assertListEqual(module_scores, expected_scores)

    def test_make_gsa_file(self):
        techobj = MeasurementTech.objects.get(tech_detail='RG230-2')
        file = self.compute.make_gsa_file(techobj)
        expected_file = os.path.join(settings.BASE_DIR, 'tests/test_results/expected.gmt')

        savefile = False
        if savefile and file:
            shutil.copy(file, expected_file)

        #self.assertTrue(filecmp.cmp(file, expected_file, shallow=False))
        self.assertGreater(os.path.getsize(file), 10000000)

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
        self.assertTrue(isinstance(gsa_scores, list))
        self.assertGreater(len(gsa_scores), 4000)

        saveobj = False
        if saveobj:
            with open(os.path.join(settings.BASE_DIR, 'tests/test_results/gsa_scores-expected.pkl'), 'wb') as fp:
                pickle.dump(gsa_scores, fp, pickle.HIGHEST_PROTOCOL)

        #with open(os.path.join(settings.BASE_DIR, 'tests/test_results/gsa_scores-expected.pkl'), 'rb') as fp:
        #    expected_scores = pickle.load(fp)
        #self.assertListEqual(gsa_scores, expected_scores)

    def test_calc_exp_correl(self):

        qry_exps = Experiment.objects.filter(id__in=[8376])

        correl_results = dict()
        correl_results['WGCNA'] = self.compute.calc_exp_correl(qry_exps, 'WGCNA')
        correl_results['RegNet'] = self.compute.calc_exp_correl(qry_exps, 'RegNet')
        correl_results['PathNR'] = self.compute.calc_exp_correl(qry_exps, 'PathNR')

        #logger.debug('Have the following correls: %s', pprint.pformat(correl_results))
        self.assertTrue(isinstance(correl_results['WGCNA'][8376], dict))
        self.assertGreater(len(correl_results['WGCNA'][8376]), 1000)
        self.assertTrue(isinstance(correl_results['RegNet'][8376], dict))
        self.assertGreater(len(correl_results['RegNet'][8376]), 1000)
        self.assertTrue(isinstance(correl_results['PathNR'][8376], dict))
        self.assertGreater(len(correl_results['PathNR'][8376]), 1000)
        saveobj = False
        if saveobj:
            with open(os.path.join(settings.BASE_DIR, 'tests/test_results/correl-expected.pkl'), 'wb') as fp:
                pickle.dump(correl_results, fp, pickle.HIGHEST_PROTOCOL)

        #with open(os.path.join(settings.BASE_DIR, 'tests/test_results/correl-expected.pkl'), 'rb') as fp:
        #    expected_scores = pickle.load(fp)
        #self.assertDictEqual(correl_results, expected_scores)

    def test_get_BMD_calcs(self):

        # using TG-GATES 1d omeprazole, 3 doses - 100, 300, 1000mg/kg correspond to exps 58322, 58323, 58321
        # and 4d omeprazole, same 3 doses 55274, 55275, 55273
        exp_objs = Experiment.objects.filter(id__in=[58322, 58323, 58321, 55274, 55275, 55273])
        bmd_calcs = self.compute.get_BMD_calcs(exp_objs)
        saveobj = False
        if saveobj:
            with open(os.path.join(settings.BASE_DIR, 'tests/test_results/bmdconfig-expected.pkl'), 'wb') as fp:
                pickle.dump(bmd_calcs, fp, pickle.HIGHEST_PROTOCOL)

        with open(os.path.join(settings.BASE_DIR, 'tests/test_results/bmdconfig-expected.pkl'), 'rb') as fp:
            expected_bmd_calcs = pickle.load(fp)
        self.assertDictEqual(bmd_calcs, expected_bmd_calcs)

    def test_make_BMD_files(self):

        # using TG-GATES 1d omeprazole, 3 doses - 100, 300, 1000mg/kg correspond to exps 58322, 58323, 58321
        exp_objs = Experiment.objects.filter(id__in=[58322, 58323, 58321, 55274, 55275, 55273])

        config_file = os.path.join(self.tmp_dir, 'omeprazole_1d_4d_computation_data.json')
        with open(os.path.join(self.tmp_dir, 'omeprazole_1d_4d_sample_intensities.pkl'), 'rb') as fp:
            sample_int = pickle.load(fp)

        fc_file = os.path.join(settings.BASE_DIR, 'tests/test_data/omeprazole_1d_4d_groupFC.txt')
        fc_data = self.compute.map_fold_change_data(fc_file)

        bmd_files = self.compute.make_BMD_files(exp_objs, config_file, sample_int, fc_data)
        ref_files = []

        savefile = False
        for f in bmd_files:
            base = os.path.basename(f)
            ref_file = os.path.join(settings.BASE_DIR, 'tests/test_results', base)

            if savefile:
                shutil.copy(f, ref_file)
                ref_files.append(ref_file)

            self.assertTrue(filecmp.cmp(f, ref_file, shallow=False))

        if savefile:
            with open(os.path.join(settings.BASE_DIR, 'tests/test_results/bmdfiles-expected.pkl'), 'wb') as fp:
                pickle.dump(ref_files, fp, pickle.HIGHEST_PROTOCOL)

    def test_run_BMD(self):

        with open(os.path.join(settings.BASE_DIR, 'tests/test_results/bmdfiles-expected.pkl'), 'rb') as fp:
            bmd_files = pickle.load(fp)

        bm2_file, export_file = self.compute.run_BMD(bmd_files)
        ref_bm2_file = os.path.join(settings.BASE_DIR, 'tests/test_results/bmd_results.bm2')
        ref_export_file = os.path.join(settings.BASE_DIR, 'tests/test_results/bmd_export.txt')

        savefile = False
        if savefile:
            shutil.copy(bm2_file, ref_bm2_file)
            shutil.copy(export_file, ref_export_file)

        logger.info('Have BMD bm2 file of size %s', os.path.getsize(bm2_file))
        self.assertGreater(os.path.getsize(bm2_file), 9000000)

        logger.info('Have BMD export file of size %s', os.path.getsize(export_file))
        self.assertGreater(os.path.getsize(export_file), 1000000)

    def test_parse_BMD_results(self):

        ref_export_file = os.path.join(settings.BASE_DIR, 'tests/test_results/bmd_export.txt')
        bmd_results = self.compute.parse_BMD_results(ref_export_file)

        saveobj = False
        if saveobj:
            with open(os.path.join(settings.BASE_DIR, 'tests/test_results/bmd_export-expected.pkl'), 'wb') as fp:
                pickle.dump(bmd_results, fp, pickle.HIGHEST_PROTOCOL)

        with open(os.path.join(settings.BASE_DIR, 'tests/test_results/bmd_export-expected.pkl'), 'rb') as fp:
            expected_bmd_results = pickle.load(fp)

        self.assertListEqual(bmd_results, expected_bmd_results)


if __name__ == '__main__':
    unittest.main()
