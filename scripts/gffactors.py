"""
GroupFoldFactors.py
------------
Author: Daniel H Robertson
Informatics: Meeta Pradhan

Part of the Collaborative Toxicogenomics Platfom

Computes the gene fold factors from a set of CEL or RNAseq files that are both
defined as controls and interventions for samples collected in various experiments.

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

import unittest
import sys
import os
import shutil
import pprint
import subprocess
import csv
import json
import logging

logger = logging.getLogger('computeGFC.gffactors')

# set up pretty printer for verbose
pp = pprint.PrettyPrinter(indent=4)


def read_exp_file(infile):
    """ Read the experiment file either csv, txt, or json

    :param infile:
    :return: experiments
    """
    f_ext = os.path.splitext(infile)[1]
    experiments = dict()
    if f_ext == ".csv":
        experiments = read_exp_file_csv(infile)
    elif f_ext == ".json":
        experiments = read_exp_file_json(infile)
    else:
        logger.critical("unknown ext %s from file %s. Quitting", f_ext, infile)
    return experiments


def read_exp_file_json(infile):
    """ Read the experiment file in csv format

    Parameters
    -----------------
    infile  : input file

    return data structure containing the configuration
    """
    experiments = dict()
    logger.info("reading configuration from json file: %s", infile)
    if os.path.isfile(infile):
        with open(infile) as myfile:
            config = json.load(myfile)
            exps   = config['experiments']
            for e in exps:
                e_id = str(e['experiment']['exp_id'])
                experiments[e_id] = {'CTL': [], 'TRT': []}
                for s in e['sample']:
                    stype = 'CTL'
                    if s['sample_type'] == 'I':
                        stype = 'TRT'
                    experiments[e_id][stype].append(s['sample_name'])
    else:
        logger.critical("Unable to locate defined input json file " + infile)
        exit(0)
    return experiments


def read_exp_file_csv(infile):
    """ Read the experiment file in csv format

    Parameters
    -----------------
    infile : input file

    return data structure containing the configuration
    """
    experiments = dict()
    if os.path.isfile(infile):
        rowcount = 0
        logger.debug("Reading infile:" + infile)
        with open(infile, newline='') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=",")
            for row in csvreader:
                if rowcount != 0:  # skip header
                    e_id = str(row[1])
                    if not experiments.get(e_id):
                        experiments[e_id] = {'CTL': [], 'TRT': []}
                    experiments[e_id][row[0]].append(row[2])
                rowcount += 1
            logger.info("Read " + str(rowcount - 1) + " lines from infile")
    else:
        logger.critical("Unable to locate defined input file " + infile)
        exit(0)
    return experiments


def create_cel_list(cfile, celdir, experiments):
    """ Create the cell list from the experiments data structure

    Parameters
    --------------
    cfile:       file to write
    celdir:      directory location of cel files
    experiments: experiments data structure

    return number of files
    """
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

    # create the cell list files

    with open(cfile, 'w', newline='') as txtfile:
        for f in cell_files:
            txtfile.write(f + "\n")
    txtfile.close()

    return len(cell_files)


def normalize_cel_expression(celdir, sdir, experiments):
    """ Normalize the expression from the cell files

    Parameters
    --------------
    celdir : directory with cell files
    sdir : directory containing the scripts
    experiments: experiments data structure
    """
    clistfile = "cell_files.txt"
    if os.path.exists(clistfile):
        os.remove(clistfile)
    create_cel_list(clistfile, celdir, experiments)

    logger.info("Everything appears to be fine with the input file and CEL sample files")
    logger.info("A total of " + str(len(experiments.keys())) + " experiments defined in infile")

    # everything appears to be in order
    # prepare for R code to do the normalization and create the RMA.txt file
    r_norm_script = os.path.join(sdir, "NORM.R")
    r_cmd = "R --vanilla <" + r_norm_script
    logger.info("Normalizing data using cmd:" + r_cmd)
    output = subprocess.getoutput(r_cmd)
    logger.debug(pp.pformat(output))

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
    for e in experiments.keys():
        logger.debug("Computing the means for experiment " + str(e))
        for t in experiments[e].keys():
            samples_list = experiments[e][t]
            mean_title = str(e) + "_" + t + "_mean"
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

    rma = {'samples': rma_samples_list,
           'probes': rma_probes_list,
           'values': rma_values}

    # cleanup files
    for f in [clistfile, rma_file]:
        if os.path.exists(f):
            os.remove(f)

    return rma


def compute_limma_results(sdir, experiments, rma):
    rma_values = rma['values']
    rma_probes_list = rma['probes']
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
    r_limma_script = os.path.join(sdir, "Limma.R")
    r_cmd = "R --vanilla <" + r_limma_script
    logger.info("Running Limma model using cmd:" + r_cmd)
    output = subprocess.getoutput(r_cmd)
    logger.debug(pp.pformat(output))

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
    shutil.rmtree(directory)
    results = {'values': limma_results, 'fold_changes': fold_changes}

    return results


def write_results(outfile, experiments, results):
    #
    # Add in the mean_Control and Foldchange
    #
    limma_results = results['values']
    fold_changes = results['fold_changes']
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
                    row_data.append(val)
                out_writer.writerow(row_data)
    csvfile.close()
    logger.info("Finished writing of output to specified output file :" + outfile)


def compute_fold_factors(infile, outfile, celdir, sdir):
    """ Compute the fold factors

    Parameters
    ---------------
    infile : file
        definition of the experiments, samples, and sample type in csv or json format
    outfile : file
        output file with the results
    sdir : str
        the directory location for the R scripts
    celdir : str
        the directory of the CEL files [default "."]
"""

    # confirm the directory is accessible
    if os.path.exists(celdir):
        logger.debug("defined celdir exists")
    else:
        logger.critical("Unable to locate defined Cell directory: " + celdir)

    # read the data files
    experiments = dict()
    if infile:
        experiments = read_exp_file(infile)
    else:
        logger.critical("Does not appear to have either csv or json file")
        exit(0)

    rma = normalize_cel_expression(celdir, sdir, experiments)
    results = compute_limma_results(sdir, experiments, rma)
    write_results(outfile, experiments, results)


class MyTests(unittest.TestCase):
    def test_read_file(self):
        experiments_1 = read_exp_file('exps.csv')
        self.assertEqual(len(experiments_1.keys()), 4)
        self.assertEqual(experiments_1['53648']['CTL'][0], '15day_c1')

        experiments_2 = read_exp_file('exps.json')
        self.assertEqual(len(experiments_2.keys()), 4)
        self.assertEqual(experiments_2['53650']['TRT'][2], '29day_h3')

    def test_create_cel_list(self):
        experiments = read_exp_file('exps.csv')
        cfile = "cel_files.txt"
        if os.path.isfile(cfile):
            os.remove(cfile)
        nfiles = create_cel_list(cfile, 'UI_Test1', experiments)
        self.assertTrue(os.path.isfile(cfile))
        self.assertEqual(nfiles, 24)
        if os.path.isfile(cfile):
            os.remove(cfile)

    def test_lilly_workflow(self):
        experiments = read_exp_file('exps.csv')
        rma = normalize_cel_expression('UI_Test1', ".", experiments)
        self.assertEqual(len(rma['probes']), 14132)
        self.assertEqual(len(rma['samples']), 24)
        self.assertEqual(len(rma['values']), 32)

        results = compute_limma_results('.', experiments, rma)
        limma_results = results['values']
        self.assertAlmostEqual(float(limma_results['53652']['266730_at']['logFC']), float(1.01053640))
        self.assertAlmostEqual(float(limma_results['53650']['83781_at']['P.Value']), float(0.00000995))
        self.assertAlmostEqual(float(limma_results['53654']['311569_at']['AveExpr']), float(9.3916645))

        ofile = "output.txt"
        if os.path.isfile(ofile):
            os.remove(ofile)
        write_results(ofile, experiments, results)
        self.assertTrue(os.path.isfile(ofile))
        if os.path.isfile(ofile):
            os.remove(ofile)

if __name__ == "__main__":

    logger = logging.getLogger()
    logger.level = logging.WARN
    stream_handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(stream_handler)

    unittest.main()