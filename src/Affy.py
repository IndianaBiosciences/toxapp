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

import os.path
import pprint
from rpy2.robjects.packages import importr

pp = pprint.PrettyPrinter(indent=4)

class Affy:
    #
    # Function to read an Affy CEL file from R-Bioconductor
    #
    def readCEL(self, infile):
        if (not os.path.isfile(infile)):
            print("Unable to locate file \"" + infile + "\"", file=sys.stderr)
            return 0
            #
            # Bioconductor and affy must already be downloaded and available
            # in the appropriate R installation being used by this project
            # see scripts/create_environ.sh to do this with anaconda
            #

        affy = importr('affy')
