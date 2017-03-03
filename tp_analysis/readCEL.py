import os.path
import pprint
import rpy2.rojects.packages import importr

pp = pprint.PrettyPrinter(indent=4)

#
# Function to read an Affy CEL file from R-Bioconductor
#
def readCEL(infile):

    if (not os.path.isfile(infile)):
        print("Unable to locate file \"" + infile + "\"", file=sys.stderr)
        return 0
    #
    # Bioconductor and affy must already be downloaded and available
    # in the appropriate R installation being used by this project
    # see scripts/create_environ.sh to do this with anaconda
    #
#    affy = importr('affy')



