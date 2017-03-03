source("http://bioconductor.org/biocLite.R")
#biocLite()
#biocLite('affy')
#biocLite('gcrma')
#biocLite('limma')
#biocLite('statmod')

library(affy)
library(gcrma)
library(limma)

wd <-getwd()

#setwd("home/mpradhan/TOX/data")
#getwd()

#########open the folder 

dt <- read.table("sampleID.txt")

dim(dt)
nrow(dt)

fileName <- "sampleID.txt"
conn <- file(fileName,open="r")
linn <-readLines(conn)
print (linn)

data_dir <- paste(wd, "data", "/")

for (i in 1:length(linn) ) {
    print (linn[i])
  
    var<- linn[i]
    
    newdir = paste(data_dir, var, sep='/')
    print(newdir)
    
    setwd(newdir)
    celList <- read.table("CandT.txt")  
    celList <- as.character(celList$V1)

    print (data)
###########Let us work on each folder separately.
########The first three file data is of three CTR1, CTR2, CTR3
###########The next three are TRT1, TRT2, TRT3
    
    affydata=ReadAffy(filenames=celList)
    
    pd <- phenoData(affydata)
    print(pd)
    
    esetmas5 = mas5(affydata)
    gexp = exprs(esetmas5)
    
    colnames(gexp)
    
    #print (colnames(gexp))
    
    colnames(gexp) = c("CTR1", "CTR2", "CTR3", "TRT1", "TRT2", "TRT3")

    
        
##############    Normalize the data using justRMA
    
    t2=date()
    geset <- justRMA(filenames=celList, celfile.path = NULL)
    
    dff <- exprs(geset)
    print(dff)
   
####################################### 
    
    
    
    

    write.table(dff, file="RMA.txt", quote=F, sep="\t")
    
}


