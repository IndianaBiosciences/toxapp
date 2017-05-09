#
# These are the libraries needed by R to run the NORM.R script
#
source("http://bioconductor.org/biocLite.R")
biocLite()
biocLite('affy')
biocLite('gcrma')
biocLite('limma')
biocLite('statmod')

#
# need to install rat2302rnentrezgcdf
#
library(devtools)
install_url("http://mbni.org/customcdf/21.0.0/entrezg.download/rat2302rnentrezgcdf_21.0.0.tar.gz")
