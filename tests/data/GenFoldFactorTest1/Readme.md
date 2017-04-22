#### TCP Test Set

# Generate Gene Fold Factors

## Data Source

This test set comes from Open TG-GATEs [ cpd 142 ]

[TODO: Need to find reference to data and confirm field values ]

http://toxico.nibiohn.go.jp/open-tggates/english/common/screen4/compound?compound_id=00161&design_name=Rat230_2&organ_id=ORGA0010&test_type=in+vivo

Species: Rat
Tissue: Liver
Compound: 1% cholesterol + 0.25% sodium cholate

Experimental Time Points and CEL files:

|           |  4-day      | 8-day     | 15-day     | 29-day     |
|-----------|:-----------:|:---------:|:----------:|:----------:|
| Control   | 4day_c1.CEL | 8d_c1.CEL | 15d_c1.CEL | 29d_c1.CEL |
| Control   | 4day_c2.CEL | 8d_c2.CEL | 15d_c2.CEL | 29d_c2.CEL |
| Control   | 4day_c3.CEL | 8d_c3.CEL | 15d_c3.CEL | 29d_c3.CEL |
| High Dose | 4day_h1.CEL | 8d_h1.CEL | 15d_h1.CEL | 29d_h1.CEL |
| High Dose | 4day_h2.CEL | 8d_h2.CEL | 15d_h2.CEL | 29d_h2.CEL |
| High Dose | 4day_h3.CEL | 8d_h3.CEL | 15d_h3.CEL | 29d_h3.CEL |

These have been renamed for this test case for clarity from original file names 
in TG-Gates as to allow easier identification of which samples goes with which 
experiement and whether they are controls of interventions. The original file 
names are detailed in the table below

|           |  4-day       | 8-day        | 15-day       | 29-day       |
|-----------|:------------:|:------------:|:------------:|:------------:|
| Control   | 003017905028 | 003017906004 | 003017906010 | 003017906016 |
| Control   | 003017905029 | 003017906005 | 003017906011 | 003017906018 |
| Control   | 003017905030 | 003017906006 | 003017906012 | 003017906029 |
| High Dose | 003017906001 | 003017906007 | 003017906013 | 003017906019 |
| High Dose | 003017906002 | 003017906008 | 003017906014 | 003017906020 |
| High Dose | 003017906003 | 003017906009 | 003017906015 | 003017906021 |

## Running The Test Case

1. Generate in succession, 4 experiments relating to the 4 different dose
endpoints with the data similar to below. 

[Note: use **[Save and add another]** toreduce data entry between experiments]

For the first experiment the file "tech_info.txt" needs to be updated to allow selection of "microarray-RG230-2"

| Parameter Name      | Exp 1 Values       | Exp 2 Values       | Exp 2 Values       | Exp 2 Values       |
|---------------------|--------------------|--------------------|--------------------|--------------------|
| **Experiment Name** | GGF Test 4d        | GGF Test 8d        | GGF Test 15d       | GFF Test 29d       |
| **Tech**            | microarray-RG230-2 | microarray-RG230-2 | microarray-RG230-2 | microarray-RG230-2 |
| **Study ID**        | 142                | 142                | 142                | 142                |
| **Compound Name**   | Na Cholate         | Na Cholate         | Na Cholate         | Na Cholate         |
| **Dose**            | 500                | 500                | 500                | 500                |
| **Dose Unit**       | mg/kg              | mg/kg              | mg/kg              | mg/kg              |
| **Time**            | 4                  | 4                  | 4                  | 4                  |
| **Tissue**          | liver              | liver              | liver              | liver              |
| **Organism**        | rat                | rat                | rat                | rat                |
| **Strain**          | N/A                | N/A                | N/A                | N/A                |
| **Gender**          | mixed              | mixed              | mixed              | mixed              |
| **Repeat Type**     | single-dose        | single-dose        | single-dose        | single-dose        |
| **Route**           | diet               | diet               | diet               | diet               |
| **Source**          | TG-GATEs           | TG-GATEs           | TG-GATEs           | TG-GATEs           |
| **Data Created**    | Auto Fill          | Auto Fill          | Auto Fill          | Auto Fill          |
| **Permission**      | Any Value          | Any Value          | Any Value          | Any Value          |

2. Confirm that the experiments are available for data upload. The checkbox list should include the 4 experiments 
that were created in step 1. Click on [Save and Continue] to proceed to step 3.

3. The experiments will be listed above. Click on the "Multiple" tab. Click [Choose Files] button and 
upload the 24 CEL files by clicking the [Upload Files]

4. Confirm the list of the 24 files and click [Save] to continue.

5. Next iterate through the each of the 4 experiments and assist (highlight) the appropriate controls and interventions
for each of the experiments.

6. Confirm that the sample files are associated with the correct experiment and have the appropriate I/C (intervention
or control) designation.

