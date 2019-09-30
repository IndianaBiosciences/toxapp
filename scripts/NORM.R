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
# These packages need to already be available in R
# use setup.R to load in R before running if necessary
#

args <- commandArgs(trailingOnly=TRUE)

if (length(args) != 1) {
    stop("Need to supply array type as parameter", call. = FALSE)
}

atype <- args[1]

packages <- c("affy")

#
# Core Functions
#
# Function to check whether package is installed
is.installed <- function(mypkg) {
	is.element(mypkg, installed.packages()[,1])
}

#
# Check that packages are installed
#
for (package in packages) {
	if (!is.installed(package)) {
		stop(paste(package, " is not installed")) 
	}
}

#
# Load packages quietly
#
suppressMessages(library(affy))

cdfname = ""

if (atype == 'RG230-2') {
    library(rat2302rnentrezgcdf)
    cdfname <- "Rat2302_rn_ENTREZG"
} else if (atype == 'MG430-2') {
    library(mouse4302mmentrezgcdf)
    cdfname <- "Mouse4302_Mm_ENTREZG"
} else {
    library(hgu133plus2hsentrezgcdf)
    cdfname <- "Hgu133plus2_Hs_ENTREZG"
}


myFile <- "cell_files.txt"
if (!file.exists(myFile)) {
	stop(paste("File ", myFile, " does not exist"))
}
#########read the path of the Cel files

celList <- read.table(myFile)
celList
celList <- as.character(celList$V1)
    

affydata <- ReadAffy(filenames=celList, cdfname=cdfname)

geset <- rma(affydata)
write.exprs(geset, file="RMA.txt")
