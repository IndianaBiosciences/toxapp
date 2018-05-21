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
import configparser

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "toxapp.settings")
application = get_wsgi_application()

from src.treemap import TreeMap
from tp.models import GSAScores

logger = logging.getLogger(__name__)


class TestTreeMap(unittest.TestCase):

    def test_parse_files(self):

        treemap = TreeMap(testmode=True)

        saveobj = False
        if saveobj:
            with open(os.path.join(settings.BASE_DIR, 'tests/test_results/treemap-expected.pkl'), 'wb') as fp:
                pickle.dump(treemap.nodes, fp, pickle.HIGHEST_PROTOCOL)

        with open(os.path.join(settings.BASE_DIR, 'tests/test_results/treemap-expected.pkl'), 'rb') as fp:
            expected_tree = pickle.load(fp)
        self.assertDictEqual(treemap.nodes, expected_tree)

    def test_color_by_score(self):

        treemap = TreeMap()

        # use DM LPS as test case, 3 and 5 mg doses
        scores = GSAScores.objects.filter(experiment__id__in=[9064, 9108], geneset__core_set=True)
        colored_treemap = treemap.color_by_score(scores)
        self.assertGreater(len(colored_treemap), 100)
        self.assertGreater(colored_treemap['geneset_id_5106']['colorValue'], 6)

    def test_tree_reduce(self):

        treemap = TreeMap()
        scores = GSAScores.objects.filter(experiment__id__in=[9064, 9108], geneset__core_set=True)
        colored_treemap = treemap.color_by_score(scores)
        clusters = treemap.reduce_tree(colored_treemap)

        saveobj = False
        if saveobj:
            with open(os.path.join(settings.BASE_DIR, 'tests/test_results/treemap-clusters.pkl'), 'wb') as fp:
                pickle.dump(clusters, fp, pickle.HIGHEST_PROTOCOL)

        with open(os.path.join(settings.BASE_DIR, 'tests/test_results/treemap-clusters.pkl'), 'rb') as fp:
            expected_clusters = pickle.load(fp)
        self.assertDictEqual(clusters, expected_clusters)


if __name__ == '__main__':
    unittest.main()
