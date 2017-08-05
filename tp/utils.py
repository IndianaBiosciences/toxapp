import os
from django.conf import settings
import pprint
import logging

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
            base = file.split('.')[0]
            exp_id = int(base.split('_')[1])
            exp_with_qc[exp_id] = "/docs/" + username +"/" + file

    print(pprint.pformat(exp_with_qc))
    return exp_with_qc
