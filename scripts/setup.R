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
