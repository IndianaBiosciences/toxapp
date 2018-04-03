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
install.packages("devtools", repos='http://cran.us.r-project.org')
library("devtools")
install_url("http://mbni.org/customcdf/21.0.0/entrezg.download/rat2302rnentrezgcdf_21.0.0.tar.gz", quiet=FALSE)
install_url("http://mbni.org/customcdf/21.0.0/entrezg.download/hgu133plus2hsentrezgcdf_21.0.0.tar.gz", quiet=FALSE)
install_url("http://mbni.org/customcdf/21.0.0/entrezg.download/mouse4302mmentrezgcdf_21.0.0.tar.gz", quiet=FALSE)
