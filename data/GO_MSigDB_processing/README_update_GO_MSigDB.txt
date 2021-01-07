All these steps are detailed in 10.1371/journal.pcbi.1004847

Updating GO expansion.  This traces out gene vs. GO term annotations to include parent GO terms.

1) Update uniprot mappings

ftp://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/idmapping/by_organism/RAT_10116_idmapping.dat.gz

2) download RGD info

GENES_RAT.txt

3) update go-basic.obo

curl http://current.geneontology.org/ontology/go-basic.obo > go-basic.obo

4) update gene mappings to GO

http://current.geneontology.org/annotations/rgd.gaf.gz

5) expand GO

After unzipping files above, run
./parse_go_associations.pl > rgd_vs_GO_expansion_with_entrez_gene_01072021.txt


Updating MSigDB

1) Download

http://www.gsea-msigdb.org/gsea/msigdb/download_file.jsp?filePath=/msigdb/release/7.2/msigdb_v7.2_files_to_download_locally.zip

The file needed is the overall xml file msigdb_v7.2.xml

2) Download from NCBI the files
https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_info.gz
https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_history.gz

gunzip the files

3) Download human to rat orthology information
ftp://ftp.rgd.mcw.edu/pub/data_release/RGD_ORTHOLOGS.txt


./parseMSigDBXML.pl msigdb_v7.2_files_to_download_locally/msigdb_v7.2.xml
produces two files MSigDB_descriptions.txt and MSigDB_genes.txt

MSigDB_genes.txt gets used to update the Ctox data file MSigDB_and_TF_annotation.txt








because rgd provdes some comma-sep human orthologs, need to clean up
perl -ne 'chomp; @s = split /\t/; @h = split /,/, $s[2]; print "$s[0]\t$s[1]\t$_\n" for (@h);' new.txt > RGD_orthologs_unpivot.txt

---------------
