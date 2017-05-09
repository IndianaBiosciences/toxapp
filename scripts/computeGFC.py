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

import os
import argparse
import pprint
import subprocess
import csv
import json
import math
import logging

logger = logging.getLogger(__name__)

def compute_fold_factors(infile, cfgfile, outfile, celdir, sdir, verbose):
    """ Compute the fold factors

    Parameters
    ---------------
    infile : file
        definition of the experiments, samples, and sample type in csv format
    cfgfile : file
        definition of the experiments, samples, and sample type in json format
    outfile : file
        output file with the results
    sdir : str
        the directory location for the R scripts
    celdir : str
        the directory of the CEL files [default "."]
    verbose : boolean
        display additional information as file progresses
"""
    # set up pretty printer for verbose
    pp = pprint.PrettyPrinter(indent=4)

    #
    # Config the directory is accessible
    #
    if os.path.exists(celdir):
        logger.debug("defined celdir exists")
    else:
        logger.critical("Unable to locate defined Cell directory: " + celdir)

    # generate the location to place the configuration
    experiments = dict()

    if verbose:
        print("\nReading in experiments definition file\n")

    if cfgfile:
        logger.info("reading configuration from json file: %s", cfgfile)
        if os.path.isfile(cfgfile):
            with open(cfgfile) as myfile:
                config = json.load(myfile)
                for e in config:
                    e_id = e['experiment']['exp_id']
                    experiments[e_id] = {'CTL': [], 'TRT': []}
                    for s in e['sample']:
                        stype = 'CTL'
                        if s['sample_type'] == 'I':
                            stype = 'TRT'
                        experiments[e_id][stype].append(s['sample_name'])
        else:
            logger.critical("Unable to locate defined input json file " + cfgfile)
            exit(0)
        pp.pprint(experiments)

    elif infile:
        samples = []
        fields = []  # sample_type, experiment_name, sample_file
        if os.path.isfile(infile):
            rowcount = 0
            logger.debug("Reading infile:" + infile)
            with open(infile, newline='') as csvfile:
                configreader = csv.reader(csvfile, delimiter=",")
                for row in configreader:
                    if verbose:
                        print(row)
                    if rowcount == 0:
                        fields = row
                        message = "Fields: "
                        for f in fields:
                            message += " " + f
                        logger.debug(message)
                    else:
                        data = {}
                        for index in range(len(fields)):
                            data[fields[index]] = row[index]
                        samples.append(data)
                    rowcount += 1
                logger.info("Read " + str(rowcount - 1) + " lines from infile")
        else:
            logger.critical("Unable to locate defined input file " + cfgfile)
            exit(0)
    else:
        logger.critical("Do not appear to have either csv or json file")
        exit(0)

    if verbose:
        pp.pprint("--- EXPERIMENTS ---")
        pp.pprint(experiments)
        pp.pprint("--- END OF EXPTS ---")

    # check that all files are present
    if verbose:
        print("\nChecking that all the information is defined and files are accessible\n")

    cell_files = []
    for e in experiments.keys():
        for t in experiments[e].keys():
            for s in experiments[e][t]:
                sfile = os.path.join(celdir, s + ".CEL")
                logger.debug("Checking existence for sample: " + sfile)
                if os.path.isfile(sfile):
                    cell_files.append(sfile)
                else:
                    logger.critical("Unable to locate CEL file for exp %s and file %s ", e, sfile)
                    exit(0)

    # create the "cell_files.txt" file to be used with NORM.range    #
    clistfile = "cell_files.txt"
    with open(clistfile, 'w', newline='') as txtfile:
        for f in cell_files:
            txtfile.write(f + "\n")
    txtfile.close()

    logger.info("Everything appears to be fine with the input file and CEL sample files")
    logger.info("A total of " + str(len(experiments.keys())) + " experiments defined in infile")

    #TODO - need to correct to modern brain array probesets as per conversation with Jeff. Here is short R snippet.
    #[5/5/17, 3:03:37 PM] Jeff Sutherland:
    # library(affy)
    # library("rat2302rnentrezgcdf")
    # Data <- ReadAffy(cdfname = "Rat2302_Rn_ENTREZG")
    # eset <- rma(Data)
    # write.exprs(eset, file="mydata_RMA_brainarray.txt")
    #

    # everything appears to be in order
    # prepare for R code to do the normalization and create the RMA.txt file
    if verbose:
        print("\nNormalizing the sample expression results\n")

    r_norm_script = os.path.join(sdir, "NORM.R")
    r_cmd = "R --vanilla <" + r_norm_script
    logger.info("Normalizing data using cmd:" + r_cmd)
    output = subprocess.getoutput(r_cmd)

    if verbose:
        pp.pprint(output)


    # check to make sure everything worked okay
    #
    # Place this in the following structure
    # {
    #   sample_id_1: [ values list in order of RMA_probes_list ]
    #   sample_id_2: [ values list in order of RMA_probes_list ]
    #   ....
    #  }
    rma_file = "RMA.txt"
    rma_samples_list = []
    rma_probes_list = []
    rma_values = {}
    if os.path.isfile(rma_file):
        logger.debug("Reading RMA File: " + rma_file)
        with open(rma_file, newline='') as csvfile:
            rowcount = 0
            rma_reader = csv.reader(csvfile, delimiter="\t")
            for row in rma_reader:
                if rowcount == 0:
                    row.pop(0)  # remove probe id
                    pp.pprint(row)
                    for s in row:
                         rma_samples_list.append(s.replace(".CEL", ""))
                    logger.debug("Read " + str(len(rma_samples_list)) + " samples")
                else:
                    rma_probes_list.append(row.pop(0))
                    col = 0
                    for v in row:
                        sample = rma_samples_list[col]
                        if sample not in rma_values.keys():
                            rma_values[sample] = []
                        rma_values[sample].append(v)
                        col += 1
                rowcount += 1
            logger.info("Read " + str(rowcount - 1) + " lines from RMA file")
    else:
        logger.critical("Normalizing cell file information failed using R script: " + r_norm_script)
        exit(0)

    # Compute the means for each of the experiments and each of the controls/treatments
    if verbose:
        print("\nComputing means across all the experiments\n")
    for e in experiments.keys():
        logger.debug("Computing the means for experiment " + str(e))
        if verbose:
            pp.pprint(experiments[e])
        for t in experiments[e].keys():
            samples_list = experiments[e][t]
            mean_title = str(e) + "_" + t + "_mean"
            if verbose:
                pp.pprint(t)
                pp.pprint(mean_title)
                pp.pprint(samples_list)
            means = []
            for i in range(0, len(rma_probes_list)):
                r_sum = 0
                n = 0
                for sample in samples_list:
                    v = rma_values[sample][i]
                    r_sum += float(v)
                    n += 1
                if n > 0:
                    means.append(r_sum / n)
                else:
                    logger.critical("Demoninator is zero. Cannot compute mean for " + e + " "
                                    + t + " " + rma_probes_list[i])
                    exit(0)
            rma_values[mean_title] = means
    logger.info("Finished computing the means for the TRT and CTL groups")

    #
    # Create the fold change files for running LIMMA
    # Store values into dictionary for final results
    #
    fold_changes = {}
    directory = "Experiments"  # Need to be matched with LIMMA R script
    for e in experiments.keys():
        if not os.path.exists(directory):
            os.makedirs(directory)
        fcfile = os.path.join(directory, str(e) + "_foldchange.csv")
        if verbose:
            print("Writing foldchange file for experiment " + str(e) + " as " + fcfile)
        logger.info("Writing foldchange file for experiment " + str(e) + " as " + fcfile)
        with open(fcfile, 'w', newline='') as csvfile:
            fc_data = {}
            fc_writer = csv.writer(csvfile, delimiter=',')
            # write header
            fields = ['probeIDs']
            ctls = experiments[e]['CTL']
            trts = experiments[e]['TRT']
            for i in range(0, len(ctls)):
                fields.append("CTL" + str(i))
            fields.append("mean_Control")
            for i in range(0, len(trts)):
                fields.append("TRT" + str(i))
            fields.append("mean_Treatment")
            fields.append("FoldChange")
            fc_writer.writerow(fields)

            # write out the rows
            ctl_mean = str(e) + "_CTL_mean"
            trt_mean = str(e) + "_TRT_mean"
            for n in range(0, len(rma_probes_list)):
                probe_id = rma_probes_list[n]
                element = {"probeID": probe_id, "mean_Control": rma_values[ctl_mean][n]}
                row_data = [rma_probes_list[n]]
                element['n_ctl'] = len(ctls)
                for i in range(0, len(ctls)):
                    row_data.append(rma_values[ctls[i]][n])
                row_data.append(rma_values[ctl_mean][n])
                element['n_trt'] = len(trts)
                for i in range(0, len(trts)):
                    row_data.append(rma_values[trts[i]][n])
                row_data.append(rma_values[trt_mean][n])
                fc = float(rma_values[trt_mean][n]) - float(rma_values[ctl_mean][n])
                element["FoldChange"] = fc
                row_data.append(fc)
                fc_writer.writerow(row_data)
                fc_data[probe_id] = element
            fold_changes[e] = fc_data
        csvfile.close()

    #
    # Everything appears to be in order
    # Prepare for R code to do the Limma and create the [e]_limmaoutput.csv file
    # in the Experiments directory
    #
    if verbose:
        print("\nRunning script Limma to compute results\n")

    r_limma_script = os.path.join(sdir, "Limma.R")
    r_cmd = "R --vanilla <" + r_limma_script
    logger.info("Running Limma model using cmd:" + r_cmd)
    output = subprocess.getoutput(r_cmd)

    if verbose:
        pp.pprint(output)

    #
    # Check that the appropriate files exist and then read contents
    #
    limma_results = {}
    for e in experiments.keys():
        ofile = os.path.join(directory, str(e) + "_limma.csv")
        logger.info("Reading data from file: %s", ofile)
        if os.path.isfile(ofile):
            with open(ofile, newline='') as ocsvfile:
                limma_reader = csv.reader(ocsvfile, delimiter=",")
                l_data = {}
                nrow = 0
                for row in limma_reader:
                    if nrow == 0:
                        fields = row
                    else:
                        probe_id = row[0]
                        element = {}
                        for i in range(0, len(fields)):
                            element[fields[i]] = row[i]
                        l_data[probe_id] = element
                    nrow += 1
                limma_results[e] = l_data
            ocsvfile.close()
        else:
            logger.critical("Unable to find the expected file " + ofile +
                            " R script failed using cmd: " + r_limma_script)
            exit(0)
    #
    # Add in the mean_Control and Foldchange
    #

    with open(outfile, 'w', newline='') as csvfile:
        out_writer = csv.writer(csvfile, delimiter='\t')
        header = ["experiment", "gene_identifier", "log2_fc", "n_trt", "n_ctl",
                  "expression_ctl0", "p", "p_bh", "B"]
        out_writer.writerow(header)
        for e in sorted(experiments.keys()):
            for probe_id in sorted(limma_results[e].keys()):
                row_data = [e, probe_id]
                row_data.append(limma_results[e][probe_id]['logFC'])
                for p in ['n_trt', 'n_ctl']:
                    row_data.append(fold_changes[e][probe_id][p])
                for p in ["AveExpr", "P.Value", "adj.P.Val", "B"]:
                    val = limma_results[e][probe_id][p]
 #                   if (p == "P.Value" or p == "adj.P.Val"):
 #                       val = math.log10(float(val))
                    row_data.append(val)
                out_writer.writerow(row_data)
    csvfile.close()
    logger.info("Finished writing of output to specified output file :" + outfile)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='computGFPCpy',
                                     description='Generate the gene fold factors for Collaborative Tox Platform')
    parser.add_argument('-i', '--infile', dest="infile", type=str,
                        help='The input csv file defining the experiment, sample files, and type of sample (CTL|TRT).')
    parser.add_argument('-c', '--cfgfile', dest="cfgfile", type=str,
                        help='The input json file defining the experiment, sample files, and type of sample (C|I).',)
    parser.add_argument('-o', '--outfile', dest="outfile", type=str,
                        help='The output csv file containing the processed data.',
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
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARN)

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
    if args.cfgfile:
        logger.debug("--cfgfile %s", args.cfgfile)
    logger.debug("--outfile: %s", args.outfile)
    if args.logfile:
        logger.debug("--logfile: %s", args.logfile.name)
    logger.debug("--directory: %s", args.dir)
    logger.debug("--script_dir: %s", args.sdir)
    logger.debug("--verbose: %s", args.verbose)

    if (not (args.infile or args.cfgfile)):
        logger.critical("either --infile or --cfgfile needs to be set")
        exit()

    logger.info("Current Path: %s", os.getcwd())

    # call main function
    compute_fold_factors(args.infile, args.cfgfile, args.outfile, args.dir, args.sdir, args.verbose)

    logger.info("END")
