# Copyright 2019 Indiana Biosciences Research Institute (IBRI)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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

    def test_tree_reduce_pca(self):

        treemap = TreeMap()
        clusters = treemap.reduce_tree_pca()
        with open('tests/test_results/clusters.txt', 'w') as f:
            for p in clusters:
                for i in range(len(clusters[p])):
                    row = '\t'.join([p, str(i), clusters[p][i], '\n'])
                    f.write(row)


if __name__ == '__main__':
    unittest.main()
