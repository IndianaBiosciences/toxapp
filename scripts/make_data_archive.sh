#!/usr/bin/env bash

tar -cf ./toxapp_data_archive.tar ./data/gene_info.txt
tar -rf ./toxapp_data_archive.tar ./tp/static/site_media/RG230-2_brainarray_identifer_map.txt
tar -rf ./toxapp_data_archive.tar ./data/experiments_DM_TG.txt
tar -rf ./toxapp_data_archive.tar ./data/groupFC
tar -rf ./toxapp_data_archive.tar ./data/toxicology_results_DM_TG.txt
tar -rf ./toxapp_data_archive.tar ./data/core_gene_sets.txt
tar -rf ./toxapp_data_archive.tar ./data/MSigDB_and_TF_annotation.txt
tar -rf ./toxapp_data_archive.tar ./data/rgd_vs_GO_expansion.txt
tar -rf ./toxapp_data_archive.tar ./data/WGCNA_modules.txt
tar -rf ./toxapp_data_archive.tar ./data/gene_identifier_stats.txt
tar -rf ./toxapp_data_archive.tar ./tests/test_data
tar -rf ./toxapp_data_archive.tar ./tests/test_results

export DTE=`date +'%Y-%m-%d_%H%M%S'`
export PGPASSWORD='dbadmin'
pg_dump -U dbadmin -d ibri -Fc  > ibri_db_$DTE.dump
tar -rf ./toxapp_data_archive.tar ./ibri_db_$DTE.dump
rm ./ibri_db_$DTE.dump

gzip toxapp_data_archive.tar
echo 'archive toxapp_data_archive.tar.gz' is ready
