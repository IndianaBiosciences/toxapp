"""
computeGFC.py
------------
Author: Daniel H Robertson
Informatics: Meeta Pradhan

Part of the Collaborative Toxicogenomics Platfom


Computes the gene fold factors from a set of CEL files that are both defined as 
controls and interventions for samples collected in various experiments.

Required files: 
    infile - CSV file containting the definition of experiments and samples with
             designation of what is an intervention want what is the control.
             TRT - Intervention/Treatment
             CTL - Control

    Format, csv (header required):
        SAMPLE_TYPE, EXPERIMENT_ID, SAMPLE_ID
        CTL, XXXXX, FILENAME1
        TRT, XXXXX, FILENAME2

    CEL Files - the CEL files referenced in the infile must be accessible in either
                the current directory from which this script is run "." (default) or
                as specified by the -directory option to the script.
                These files are expected to be [SAMPLE_ID].CEL

"""

import gffactors
import logging
import argparse
import pprint
import os


logger = logging.getLogger('computeGFC')

# set up pretty printer for verbose
pp = pprint.PrettyPrinter(indent=4)


parser = argparse.ArgumentParser(prog='computGFPCpy',
                                 description='Generate the gene fold factors for Collaborative Tox Platform')
parser.add_argument('-i', '--infile', dest="infile", type=str,
                    help='The input csv or json file defining the experiment, sample files, and type of sample.')
parser.add_argument('-o', '--outfile', dest="outfile", type=str,
                    help='The output tab-delimited file containing the processed data.',
                    required=True)
parser.add_argument('-d', '--directory', dest="dir", type=str, default=".",
                    help='The directory for location of the CEL files. Default is current directory.')
parser.add_argument('-s', '--script_dir', dest="sdir", type=str, default=".",
                    help='The directory for location of the R script files. Default is current directory.')
parser.add_argument('-l', '--logfile', dest='logfile', type=argparse.FileType('wb', 0),
                    help='The output file of logfile.')
parser.add_argument('-v', '--verbose', help='Print verbose output during processing', action="store_true")

args = parser.parse_args()

#TODO - Connect to correct logger

# set log level
logger.setLevel(logging.WARN)
if args.verbose:
    logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.WARN)
if args.verbose:
    ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

# create file handler and set level to debug
if args.logfile:
    fh = logging.FileHandler(args.logfile.name, 'a')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

logger.info("BEGIN")
if args.infile:
    logger.debug("--infile %s", args.infile)
logger.debug("--outfile: %s", args.outfile)
if args.logfile:
    logger.debug("--logfile: %s", args.logfile.name)
logger.debug("--directory: %s", args.dir)
logger.debug("--script_dir: %s", args.sdir)


if (not (args.infile or args.cfgfile)):
    logger.critical("either --infile or needs to be set")
    exit()

logger.info("Current Path: %s", os.getcwd())

# call main function
gffactors.compute_fold_factors(args.infile, args.outfile, args.dir, args.sdir)

logger.info("END")
