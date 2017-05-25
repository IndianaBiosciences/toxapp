#
# These are the libraries needed by R to run the processing
# should be installed through R -- Conda or others methods
#
#
#

source("http://bioconductor.org/biocLite.R")
biocLite()
biocLite('affy')
biocLite('gcrma')
biocLite('limma')
biocLite('statmod')
biocLite('piano')

#
# need to install rat2302rnentrezgcdf
#
install.packages("devtools")
library("devtools")
install_url("http://mbni.org/customcdf/21.0.0/entrezg.download/rat2302rnentrezgcdf_21.0.0.tar.gz", quiet=FALSE)
