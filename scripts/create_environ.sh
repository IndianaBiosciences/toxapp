#!/bin/bash
#
# Set up the environment for python and R
#
#
if [ -e "$HOME/anaconda3" ]
then
	echo "Anaconda3 already available at $HOME/anaconda"
else	
	echo "installing Anaconda3"
	if [ uname == "Linux" ]
  	then
  	    bash /opt/installs/Anaconda3-4.3.0-Linux-x86_64.sh
  	else
  	    bash /opt/installs/Anaconda3-4.3.0-MacOSX-x86_64.sh
  	fi
fi

#
# Set up location of conda and add R and python modules
#
if [ -x $HOME/anaconda3/bin/conda ]
then
	echo "checking and installing R, rpy2, numpy"
	$HOME/anaconda3/bin/conda config --add channels bioconda
	$HOME/anaconda3/bin/conda install bioconductor-affy bioconductor-limma
	$HOME/anaconda3/bin/conda install -c r rpy2 numpy psycopg2
else
	echo "unable to locate conda"
	exit 1
fi

#
# From R -- install the necessary bioconductor packages
#
R --no-save << EOD
source("http://bioconductor.org/biocLite.R")
biocLite( lib="~/anaconda3/lib/R/lib")
biocLite('affy', lib="~/anaconda3/lib/R/lib")
biocLite('gcrma', lib="~/anaconda3/lib/R/lib")
biocLite('limma', lib="~/anaconda3/lib/R/lib")
biocLite('statmod', lib="~/anaconda3/lib/R/lib")
EOD

