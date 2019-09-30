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
from django.conf import settings
import pprint
import logging
import configparser
logger = logging.getLogger(__name__)


def get_user_qc_urls(username):
    """ read the users url directory and return the dictionary of experiments
        with QC pdf files of the format Rplots_*.pdf

    Parameters
    -----------------
    username  : requests username

    return dictionary of the experiment id and the url
    """
    exp_with_qc = dict()
    logger.info("generating the experiments with QC for: %s", username)

    udir = os.path.join(settings.COMPUTATION['url_dir'], username)
    if os.path.isdir(udir):
        files = os.listdir(udir)
        for file in files:
            if file.startswith('Rplot'):
                base = os.path.splitext(file)[0]
                exp_id = int(base.split('_')[1])
                exp_with_qc[exp_id] = "/docs/" + username +"/" + file

    print(pprint.pformat(exp_with_qc))
    return exp_with_qc


def parse_config_file():

    config_file = os.path.join(settings.BASE_DIR, 'data/toxapp.cfg')
    if not os.path.isfile(config_file):
        logger.critical('Configuration file %s not readable', config_file)
        exit(1)

    config = configparser.ConfigParser()
    config.read(config_file)
    return config

