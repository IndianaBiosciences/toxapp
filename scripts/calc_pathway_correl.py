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
import logging
import csv
import configparser
import pprint
import gzip
import time
import subprocess
import collections
from tempfile import gettempdir, NamedTemporaryFile
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "toxapp.settings")
application = get_wsgi_application()

from src.computation import Computation

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if __name__ == '__main__':

    print('PathNR_geneset_ID', 'WGCNA_geneset_ID', 'correl', sep='\t')
    compute = Computation(None)
    results = compute.calc_geneset_correl('EPA', 'WGCNA')
    for gs1 in results:
        for gs2 in results[gs1]:
            print(gs1, gs2, results[gs1][gs2], sep='\t')
