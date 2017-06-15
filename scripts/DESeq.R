library("DESeq2")
library("ggplot2")
library("reshape2")
library("png")

#######################   DESeq.R
######################    Set FDR and Log2 fold change (LFC) cut-off thresholds here
padjcut=0.05
logfccut=0.5849625

setwd <- getwd()

#######################   PERFORMING DSEq2 ANALYSIS

##################	READ METADATA			###################

### File containing sample metadata information - same folder as this Rmarkdown
### Best practice: First column must be ID, followed by metadata columns
###                 Last column must/can be a "Group" variable - combines relevant metadata
###                 First row must be a header

sample_key_file <- "study_design.txt"
if (!file.exists(sample_key_file)) {
	stop(paste("Metadata file '", sample_key_file, "' does not exist in current directory", sep = "", collapse = NULL))
}
sample_key<-read.table(sample_key_file, sep="\t", header =T, quote="", stringsAsFactors=F)
head(sample_key)

######################		READ THE HTSeq Data

### File containing raw counts per gene - generated using HTseq
### Best practise: First column must be gene ID, followed by sample counts
###                 First row must be header

raw_counts_file<-"gene_counts.txt"
if (!file.exists(raw_counts_file)) {
	stop(paste("HTSeq Data file '", raw_counts_file, "' does not exist in current directory", sep = "", collapse = NULL))
}
raw.data<-read.table(raw_counts_file,sep="\t",header=T,quote="",stringsAsFactors = F)
count_data <- raw.data[ , -c(1) ]
head(count_data)
rownames( count_data ) <- raw.data[ , 1 ]  # gene names
dim(count_data)
count_data[1:5,1:5]

#########################     4.  PREPARING THE RAW COUNT DATA FOR DESeq2 ANALYSIS


#########################   This section filters out non-protein coding genes and removes genes that don't meet a certain read count cut_off
#########################   ```{r, eval=TRUE}
#########################   Select only protein coding genes for further analysis
# NOTE SELECTING TO PROTEIN_CODING WILL BE DONE IN UI

prot_count_data<-count_data
dim(prot_count_data)

########################   Select only those genes that meet the min_count cut-off

min_count_cutoff<-10
max_count<-apply(prot_count_data,1,max)
hist_max_count<-data.frame(log2(max_count))

#######################   Plotting a histogram to understand where the count_cutoff lies within max_count

ggplot(hist_max_count,aes(x=log2(max_count))) + geom_histogram(bins=100) + 
  geom_vline(xintercept = log2(min_count_cutoff),linetype="dashed") + 
  ggtitle("Histogram of Max counts per gene across all samples") + 
  theme(legend.title = element_blank(), 
        text = element_text(size=15,face="bold"))


#######################       5.   CREATING DIRECTORY FOR ALL FILTERED FILES AND DESeq2 OUTPUT

deseqout=paste(setwd, "Normalized", sep="/")
dir.create(deseqout)

filt_count_data<-prot_count_data[max_count >= min_count_cutoff,]
dim(filt_count_data)
head(filt_count_data)

write.table(filt_count_data, paste(deseqout,"allCountTable.filtered.txt", sep="/"),
	sep="\t", row.names=T, col.names=T, quote=F)

ggplot(data=melt(log2(filt_count_data)), aes(variable, value)) + geom_boxplot()
colnames(filt_count_data)


#####################   This correlation is only for the filtered protein coding

temp_cor_data<-cor(filt_count_data)
print(temp_cor_data)
dim(temp_cor_data)

write.table(temp_cor_data, paste(deseqout,"allCountTable.sample_corr_filtCounts.txt", sep="/"),
	sep="\t", row.names=T, col.names=T, quote=F)


####################    This correlation is for the rawCounts

temp_cor_rawdata<-cor(count_data)
dim(temp_cor_rawdata)

write.table(temp_cor_rawdata, paste(deseqout,"allCountTable.sample_corr_rawCounts.txt", sep="/"),
	sep="\t", row.names=T, col.names=T, quote=F)


#######################   6. PERFORMING DSEq2 ANALYSIS



#######################   DESeq analysis is carried out in this section. Note, it might take a long time to run if
#######################   there are a large number of samples

#######################   Creating directory for all DESeq2 output
#######################   deseqout=paste(setwd, "deseq_1.5_prot_noShrink_min10/", sep="/")
#######################   dir.create(deseqout)

#######################   R object to save deseq object for faster access later

deseqobj=paste(deseqout, "dds_prot_fullModel.rda", sep="/")

######################    Set FDR and Log2 fold change (LFC) cut-off thresholds here
padjcut=0.05
logfccut=0.5849625

######################   7. DESeq initialization


#####################     When the count data has NA We Need to Remove it (NOT GIVEN IN THE DOW SCRIPT)

print (apply(filt_count_data, 2, summary))
narows <- apply(filt_count_data, 1, function(x) any(is.na(x)))
countDataClean <- filt_count_data[ !narows, ]
dim(countDataClean)

####################    Now the data is clean without NAs and ready for DESeq2 #######################################   

####################   I am not sure about the design Matrix for the data (After running removing the NAs this part is working)

print(sample_key)
####################  The design matrix is the column identified using (sample_key$Group)

ddsMat=DESeqDataSetFromMatrix(countData=countDataClean,colData=sample_key,design=~Group)

###################   This statement I am not sure

dds = DESeq(ddsMat, minReplicatesForReplace = 3, betaPrior = F)
save(dds, file=deseqobj)


#####################   This section prepares required count information for downstream analysis, such as normalized expression values.

#####################  Writing size factor normalized count table

counts.nor=counts(dds, normalized=TRUE)
write.table(counts.nor,paste(deseqout,"allCountTable.normalized.txt",sep="/"),sep="\t",row.names=T,col.names=T,quote=F)

######################  In order to understand if one or some samples are behaving as outlier
######################  We try to get a sense of how many values are replaced by DESeq2
######################  A count table is also written that contains gene counts with replaced values

replaced=assays(dds)[["replaceCounts"]]
write.table(replaced, paste(deseqout,"allCountTable.replaced.txt",sep="/"), 
            sep="\t", row.names=T, col.names=T, quote=F);

#####################   To get a sense of how many such values are replaced, a list of all replaced values are written

original=counts(dds, normalized=F)
replacedEntries=which(original != replaced, arr.ind=T)
replacedDetail=data.frame(genes=row.names(replacedEntries),
                          samples=colnames(original)[replacedEntries[,"col"]],
                          original=apply(replacedEntries, 1,
                                         function(x){return(original[x[1],x[2]])}),
                          replaced=apply(replacedEntries, 1,
                                         function(x){return(replaced[x[1],x[2]])}))

write.table(replacedDetail, paste(deseqout,"replacedValues.txt",sep="/"), 
				sep="\t", quote=F, row.names=F)

######################  If the number of values replaced is HIGH, then check whether some samples are way off total replaced values
sum(original!=replaced)

####################  8. NORMALIZATION USING VARIANCE STABILIZATION TRANSFORMATION (VSD)

###################   This transforms the count data (normalized by size factors) to having constant variance.
###################   This is useful for looking at how the samples clusters or performs on PCA.

###################   ```{r,eval=TRUE}

vsd <- varianceStabilizingTransformation(dds)
dim(assay(vsd))
assay(vsd)[1:5,1:5]
ggplot(data=melt(as.data.frame(assay(vsd))), aes(variable, value)) + geom_boxplot()

write.table(assay(vsd), paste(deseqout,"allCountTable.vsd.txt",sep = "/"), 
			sep="\t",row.names=T,col.names=T,quote=F)

rld <- rlog(dds)
assay(rld)[1:5,1:5]
ggplot(data=melt(as.data.frame(assay(rld))), aes(variable, value)) + geom_boxplot()

write.table(assay(rld), paste(deseqout,"allCountTable.rld.txt",sep = "/"),
	sep="\t",row.names=T,col.names=T,quote=F)


#ggplot(data=melt(as.data.frame(assay(rld))), aes(variable, value)) + geom_boxplot()

dds <- DESeq(dds)
results(dds)

print(results(dds))

##########  Print the Log change for the whole data (As given in the manual)

write.table(results(dds), paste(deseqout,"allFDRP-values.txt", sep="/"),
		sep="\t",row.names=T,col.names=T,quote=F)

##############    Plot of FDR and P-value  To find the outliers sample

ExtraDir<-paste(setwd,"Normalized",sep="/")
dir.create(ExtraDir, showWarnings = FALSE)

plt<- ggplot(data=melt(as.data.frame(assay(rld))), aes(variable, value)) + geom_boxplot()
out_file<-paste(ExtraDir, 'FDR_p-value_logfoldchangedata.png', sep="/")
png(filename=out_file, width=2200, height=1080, res=300)
plot(plt, main="Boxplot_for_FDRp-value")
dev.off()

img<-readPNG(out_file)
grid::grid.raster(img)


####################  Heirarchical clustering is performed to understand correlations 
####################  across samples after VSD transformation

temp_all_data<-assay(rld)
temp_key<-sample_key
temp_dd <- as.dist((1 - cor(temp_all_data, method="spearman"))/2)
ward.hclust = hclust(temp_dd,method="ward.D")
hcd<-as.dendrogram(ward.hclust)

out_file <- paste(ExtraDir, 'geneexpression_hclustering_samples.png', sep="/")
png(filename=out_file,width=1920, height=1080, res=300)
plot(hcd, main="Clustering on Normalized gene expression") 
dev.off()

img<-readPNG(out_file)
grid::grid.raster(img)