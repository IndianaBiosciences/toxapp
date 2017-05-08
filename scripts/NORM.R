#
# These packages need to already be available in R
# use setup.R to load in R before running if necessary
#
packages <- c("affy", "rat2302rnentrezgcdf" )

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


myFile <- "cell_files.txt"
if (!file.exists(myFile)) {
	stop(paste("File ", myFile, " does not exist"))
}
#########read the path of the Cel files

celList <- read.table(myFile)
celList
celList <- as.character(celList$V1)
    
affydata=ReadAffy(filenames=celList, cdfname="Rat2302_rn_ENTREZG")
    
esetmas5 = mas5(affydata)
gexp = exprs(esetmas5)
    
t2=date()
geset <- justRMA(filenames=celList, celfile.path = NULL)
    
dff <- exprs(geset)

write.table(dff, file="RMA.txt", quote=F, sep="\t")
    



