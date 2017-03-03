import os.path
import argparse
import csv
import pprint
from Bio.Affy import CelFile
import rpy2.robjects as robjects
from rpy2.robjects.packages import importr

pp = pprint.PrettyPrinter(indent=4)

#
# Function to read an Affy CEL file from R-Bioconductor
#
def readCEL(infile):

    data = CelFile.read(infile)
    pp.pprint(data)


def read_input_file(infile):

    contents = csv.reader(infile, delimiter = ",")

    for row in contents:
        print (row[0])
###########################Get path of each sampleID folder
        newpath = path+row[0]
        print(newpath)

        actualpath = os.listdir(newpath)

        filename = newpath+"/control.txt"
        print(filename)

        f = open(os.path.join(newpath, "control.txt"))

        for line in f:
            print(line)

    return


#
# main
#
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='script to process CEL files.')
    parser.add_argument('-i', '--infile', dest="infile", type=argparse.FileType('r'),
                        help='The input file to process to find the CEL files.', required=True)

    args = parser.parse_args()
    pp.pprint(args)
    readCEL(args.infile)
