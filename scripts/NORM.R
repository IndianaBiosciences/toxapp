#
# These packages need to already be available in R
# use setup.R to load in R before running if necessary
#
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
library(rat2302rnentrezgcdf)
#library(mouse4302mmentrezgcdf)

myFile <- "cell_files.txt"
if (!file.exists(myFile)) {
	stop(paste("File ", myFile, " does not exist"))
}
#########read the path of the Cel files

celList <- read.table(myFile)
celList
celList <- as.character(celList$V1)
    
affydata <- ReadAffy(filenames=celList, cdfname="Rat2302_rn_ENTREZG")
#affydata <- ReadAffy(filenames=celList, cdfname = "Mouse4302_Mm_ENTREZG")

geset <- rma(affydata)
write.exprs(geset, file="RMA.txt")
    



