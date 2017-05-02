## Run with Rscript

## Setup and Parse Arguments to script
suppressPackageStartupMessages(library("argparse"))

# create parser object
parser <- ArgumentParser()

# specify our desired options

# by default ArgumentParser will add an help option
parser$add_argument("-v", "--verbose", action="store_true", default=TRUE,
    help="Print extra output [default]")

parser$add_argument("-q", "--quietly", action="store_false",
    dest="verbose", help="Print little output")

parser$add_argument("inputfile", nargs="+",
 help="input file with reference to CEL data files")

parser$add_argument("outputfile", nargs="+",
 help="file to write the normalized fold factors")


# get command line options, if help option encountered print help and exit,
# otherwise if options not found on command line then set defaults,
args <- parser$parse_args()

# setinput file
iFile <- args$inputfile

if (file.exists(iFile)) {
    if (args$verbose) {
        write(paste(iFile, " exists\n", sep=""), stderr())
    }
} else {
    write(paste("\nERROR: input file \"", iFile, "\" does not exist\n", sep=""), stderr())
    quit(save="no", status=1)
}

# set output file
oFile <- args$outputfile

# print some progress messages to stderr if "quietly" wasn't requested
if (args$verbose) {
    write("\nGenerating addition status messages (set -q or -quietly to suppress)\n", stderr())
    args
}

# if directory set -- use this directory or set to where it was launched
if ( is.null(args$directory) ) {
    dir <- getwd()
} else {
    dir <- args$directory
}

if (args$verbose) {
    write(paste("\n working from directory \"",dir,"\"\n"), sep="", stderr())
}

## Start main part of script

## The Bioconductor packages affy, gcrma, limma, statmod must
## have been already loaded with the create_environment.sh script
## that set up the right create_environment

if (args$verbose) {
    library(affy)
    library(gcrma)
    library(limma)
} else {
    suppressPackageStartupMessages(library(affy))
    suppressPackageStartupMessages(library(gcrma))
    suppressPackageStartupMessages(library(limma))
}

#########read the path of the Cel files

if (args$verbose) {
    write(paste("Reading list of data files from ", iFile, "\n", sep=""), stderr())
}

# Read the cell files list
celList <- read.table(iFile)
if (args$verbose) {
    celList
}

celList <-as.character(celList$V1)
if (args$verbose) {
    celList
}

# Read the CEL Files from list
if (args$verbose) {
    write("Reading celList with ReadAffy")
}
affydata=ReadAffy(filenames=celList)


esetmas5 = mas5(affydata)
gexp = exprs(esetmas5)

t2=date()
geset <- justRMA(filenames=celList, celfile.path = NULL)

dff <- exprs(geset)

if (args$verbose) {
    write(paste("Writing output to ", oFile, "\n", sep=""), stderr())
}
write.table(dff, file=oFile, quote=F, sep="\t")
