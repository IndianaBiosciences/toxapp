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

#
# These are the libraries needed by R to run the processing
# should be installed through R -- Conda or others methods
#
#
#

source("http://bioconductor.org/biocLite.R")
biocLite()
biocLite('gcrma')
biocLite('statmod')
biocLite('DESeq2')
biocLite('affy')
biocLite('limma')
biocLite('piano')
biocLite('png')

#
# need to install rat2302rnentrezgcdf
#
install.packages("./data/rat2302rnentrezgcdf_21.0.0.tar.gz", repos=NULL)
install.packages("./data/hgu133plus2hsentrezgcdf_21.0.0.tar.gz", repos=NULL)
install.packages("./data/mouse4302mmentrezgcdf_21.0.0.tar.gz", repos=NULL)
