#!/usr/bin/env bash

tar -cf ./toxapp_data_archive.tar ./data/gene_info.txt
tar -rf ./toxapp_data_archive.tar ./data/MSigDB_and_TF_annotation.txt
tar -rf ./toxapp_data_archive.tar ./data/WGCNA_modules.txt
tar -rf ./toxapp_data_archive.tar ./data/compilation_all_gene_sets.txt
tar -rf ./toxapp_data_archive.tar ./data/core_gene_sets.txt
tar -rf ./toxapp_data_archive.tar ./data/experiments_DM_TG.txt
tar -rf ./toxapp_data_archive.tar ./data/gene_identifier_stats.txt
tar -rf ./toxapp_data_archive.tar ./data/geneset_vs_tox_association.txt
tar -rf ./toxapp_data_archive.tar ./data/groupFC
tar -rf ./toxapp_data_archive.tar ./data/node_positions_including_pseudonodes.xlsx
tar -rf ./toxapp_data_archive.tar ./data/rgd_vs_GO_expansion.txt
tar -rf ./toxapp_data_archive.tar ./data/sample_fc_data_DM_gemfibrozil_1d_7d_100mg_700_mg.txt
tar -rf ./toxapp_data_archive.tar ./data/toxapp.cfg
tar -rf ./toxapp_data_archive.tar ./data/toxapp_genesets.gmt
tar -rf ./toxapp_data_archive.tar ./data/toxicology_results_DM_TG.txt
tar -rf ./toxapp_data_archive.tar ./data/BMD_defined_analysis_categories.txt
tar -rf ./toxapp_data_archive.tar ./data/BMD_defined_analysis_probes.txt
tar -rf ./toxapp_data_archive.tar ./data/hgu133plus2hsentrezgcdf_21.0.0.tar.gz
tar -rf ./toxapp_data_archive.tar ./data/mouse4302mmentrezgcdf_21.0.0.tar.gz
tar -rf ./toxapp_data_archive.tar ./data/rat2302rnentrezgcdf_21.0.0.tar.gz
tar -rf ./toxapp_data_archive.tar ./data/moe430ammentrezgcdf_23.0.0.tar.gz
tar -rf ./toxapp_data_archive.tar ./data/mogene11stmmentrezgcdf_23.0.0.tar.gz
tar -rf ./toxapp_data_archive.tar ./data/rae230arnentrezgcdf_23.0.0.tar.gz
tar -rf ./toxapp_data_archive.tar ./data/rat2302rnentrezgcdf_23.0.0.tar.gz
tar -rf ./toxapp_data_archive.tar ./data/rgu34arnentrezgcdf_23.0.0.tar.gz
tar -rf ./toxapp_data_archive.tar ./data/HGU133-2_brainarray_identifier_map.txt
tar -rf ./toxapp_data_archive.tar ./data/MG430-2_brainarray_identifier_map.txt
tar -rf ./toxapp_data_archive.tar ./data/MOE430A_brainarray_identifier_map.txt
tar -rf ./toxapp_data_archive.tar ./data/Mmus_GRCm38_identifier_map.txt
tar -rf ./toxapp_data_archive.tar ./data/MoGene-1.1-ST_brainarray_identifier_map.txt
tar -rf ./toxapp_data_archive.tar ./data/RAE230A_brainarray_identifier_map.txt
tar -rf ./toxapp_data_archive.tar ./data/RG230-2_brainarray_identifier_map.txt
tar -rf ./toxapp_data_archive.tar ./data/RGU34A_brainarray_identifier_map.txt
tar -rf ./toxapp_data_archive.tar ./data/Rnor_6.0_identifier_map.txt
tar -rf ./toxapp_data_archive.tar ./tp/static/site_media/RG230-2_brainarray_identifier_map.txt
tar -rf ./toxapp_data_archive.tar ./tests/test_data
tar -rf ./toxapp_data_archive.tar ./tests/test_results


export DTE=`date +'%Y-%m-%d_%H%M%S'`
export PGPASSWORD='dbadmin'
pg_dump -h 127.0.0.1 -U dbadmin -d ibri -Fc  > ibri_db_$DTE.dump
tar -rf ./toxapp_data_archive.tar ./ibri_db_$DTE.dump
rm ./ibri_db_$DTE.dump

gzip toxapp_data_archive.tar
echo 'archive toxapp_data_archive.tar.gz' is ready
