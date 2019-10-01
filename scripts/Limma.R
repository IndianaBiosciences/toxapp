# Copyright 2019 Indiana Biosciences Research Institute (IBRI)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#
# These packages need to already be available in R
# use setup.R to load in R before running if necessary
#
packages <- c("affy", "gcrma", "limma", "statmod" )

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
suppressMessages(library(gcrma))
suppressMessages(library(limma))

dat.files <- list.files(path="Experiments", pattern = "foldchange.csv", full.names = T)
dat.files

length(dat.files)

for (i in 1:length(dat.files)) { 
  
  df <- read.csv(dat.files[i], header = TRUE) 
  filename <- (dat.files[i])
  #print(filename)
  
  #print(df)
#######Begin design and contrast######
  
########## Find  number of control 
  df1 <- df[, grep("CTL+", colnames(df))]
  numofcontrol <- ncol(df1)
  print(paste("Number of Controls: ", numofcontrol))

########## Find number of treatment
  
  df2 <- df[, grep("TRT+", colnames(df))]
  numoftreatment <- ncol(df2)
  print(paste("Number of Treatments: ", numoftreatment))
  
####### Use only the control and treatment data for Limma with probeIDS
####### Need to use ProbeIDs else it becomes difficult to pass it
  
  print(colnames(df))
  dff <- df[,-grep(("mean_Control|FoldChange|mean_Treatment"), colnames(df))]
  dfx <- data.frame(dff, row.names=dff$probeIDs)
  print(dim(dfx))
  
#######For the design matrix and contrast matrix
######
  
  controlvector = c()  
  for (i in 1:numofcontrol){
    var = 1
    controlvector[i] <- var    
  }
  
  treatmentvector = c()  
  for (i in 1:numoftreatment){
    var = 2
    treatmentvector[i] <- var    
  }
  vector <- c(controlvector, treatmentvector)

############Vector for design matrix is ready
#########now design the matrix
  
  design <- model.matrix(~ -1+factor(vector))
  #print(design)
 
  colnames(design) <- c("Control", "Group")
  #print(colnames(design))
  
  contrast.matrix <- makeContrasts(Group-Control, levels = design)
  #print(contrast.matrix)
  
##############NOW LIMMA
  y <- ncol(dfx)
  rrow <- nrow(dfx)
  
  fit <-lmFit(dfx[,2:y],design)
  fit2 <- contrasts.fit(fit,contrast.matrix)
  fit2 <- eBayes(fit2)
  colnames(fit2)
  
  df2 <- topTable(fit2, n=rrow)
  
# Extract Experiment ID from the File Name
  exp_file <- basename(filename)
  exp_name <- strsplit(exp_file, "_")[[1]][1]

  df3 <- rownames(df2)
  df4 <- cbind(df3,df2)

  colnames(df4)[1]<- "probeIDs"
  
  out_file <- paste(exp_name, "_limma.csv", sep = "")
  
  write.table(df4, file=file.path("Experiments",out_file), row.names=F, col.names=T, sep=",")

}