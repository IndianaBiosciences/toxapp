Information on running the scripts to create group fold change values starting
from a list of CEL files and the context related to experiments and the types
of interventions: treatment or control

Scripts:
    computeGFC.py -- main python scripts to do all the processing and execute
                     the appropriate R scripts
    NORM.R        -- R script to normalize the gene expression values across 
                     all the samples
    Limma.R       -- R script to [Meeta add short description here]
    setup.R       -- R script to make sure all the appropriate Bioconductor
                     packages are loaded

How to run:
    computGFPCpy [-h] -i INFILE -o OUTFILE [-d DIR] -l LOGFILE [-v]

    Generate the gene fold factors for Collaborative Tox Platform

    optional arguments:
      -h, --help        show this help message and exit
      -i INFILE, --infile INFILE
                        The input csv file defining the experiment, sample
                        files, and type of sample (CTL|TRT).
      -o OUTFILE, --outfile OUTFILE
                        The output csv file containing the processed data.
      -d DIR, --directory DIR
                        The directory for location of the CEL files. 
                        Default is current directory.
      -l LOGFILE, --logfile LOGFILE
                        The output file of logfile.
      -v, --verbose     Print verbose output during processing

Example:

    python computeGFC.py -i exps.csv -o output.csv -l gfc.log -d CEL -v

    Necessary Input Files:
        exps.csv     - file defining the experiments and the association of 
                       the samples to experiments and whether they are 
                       CTL (control) or TRT (treatment)
        CEL/*.CEL    - directory of the CEL files that are referenced in
                       the exps.csv file

    Output Files:
        output.csv        - the final output for all the experiments/samples
        gfc.log           - log file

    Temporary Files:
        cell_files.txt       - input file for NORM.R
        RMA.txt              - output file for NORM.R
        Experiments          - subdirectory for files for Limma.R
        [Exp]_foldchange.csv - input files per experiment in Experiments 
                               directory for the Limma.R
        [Exp]_limma.csv      - output in Experiments directory for Limma.R