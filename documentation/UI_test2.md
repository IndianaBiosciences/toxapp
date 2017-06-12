#### TCP Test Set

# Generate Gene Fold Factors

## Data Source

This test set comes Dow AgroSciences.

[TODO: Need to find reference to data and confirm field values ]

Species: Rat
Tissue: Liver
Compound: Myclobutanil

Experimental Time Points and CEL files:

|              | Acetone        | Clo            | PB             |
|--------------|:--------------:|:--------------:|:--------------:|
| Control      | 2377_cont_diet | 2377_cont_diet | 2377_cont_diet |
| Control      | 2378_cont_diet | 2378_cont_diet | 2378_cont_diet | 
| Control      | 2379_cont_diet | 2379_cont_diet | 2379_cont_diet | 
| Control      | 2380_cont_diet | 2380_cont_diet | 2380_cont_diet | 
| Control      | 2381_cont_diet | 2381_cont_diet | 2381_cont_diet | 
| Intervention | 2382_acet_diet | 2427_Clo       | 2432_PB        |
| Intervention | 2383_acet_diet | 2428_Clo       | 2433_PB        |
| Intervention | 2384_acet_diet | 2429_Clo       | 2434_PB        |
| Intervention | 2385_acet_diet | 2430_Clo       | 2435_PB        |
| Intervention | 2386_acet_diet | 2431_Clo       | 2436_PB        |


## Running The Test Case

1. Generate a new study using the following data (or similar)

| Parameter Name       | Suggested Value                         |
|----------------------|-----------------------------------------|
| **Study name**       | TG-Gates Cholesterol Study CPD 142      |
| **Study info**       | 4 H doses and controls at 4 time points |
| **Source**           | TG-Gates                                |

Select [Save and add/edit experiments]

2. Generate in succession, 4 experiments relating to the 4 different dose
endpoints with the data similar to below. 

[Note: use **[Save and add another]** toreduce data entry between experiments]

For the first experiment the file "GPL3240.txt" needs to be updated to allow selection of "microarray-RG230A"

| Parameter Name      | Exp 1 Values       | Exp 2 Values       | Exp 3 Values       | Exp 4 Values       |
|---------------------|--------------------|--------------------|--------------------|--------------------|
| **Tech**            | microarray-RG230A  | microarray-RG230A  | microarray-RG230A  | microarray-RG230A  |
| **Compound Name**   | Cholesterol        | Cholesterol        | Cholesterol        | Cholesterol        |
| **Dose**            | 500                | 500                | 500                | 500                |
| **Dose Unit**       | mg/kg              | mg/kg              | mg/kg              | mg/kg              |
| **Time**            | 4                  | 8                  | 15                 | 29                 |
| **Tissue**          | liver              | liver              | liver              | liver              |
| **Organism**        | rat                | rat                | rat                | rat                |
| **Strain**          | Sprague-Dawley     | Sprague-Dawley     | Sprague-Dawley     | Sprague-Dawley     |
| **Gender**          | male               | male               | male               | male               |
| **Repeat Type**     | single-dose        | single-dose        | single-dose        | single-dose        |
| **Route**           | diet               | diet               | diet               | diet               |
| **Experiment name** | take default value | take default value | take default value | take default value |
[Note]

Select [Save and Upload Samples]

3. Confirm that the 4 experiments are available for data upload. The checkbox list should include the 4 experiments 
that were created in step 2 above related to the study created in step 1. 
Click on [Save and upload samples] to proceed to the next step.

4. The study and the experiments will be listed above. Click on the "Multiple" tab. Click [Choose Files] button and 
upload the 24 CEL files by clicking the [Upload Files]

5. Confirm the list of the 24 files and click [Save] to continue to the next step.

6. Confirm again that all the 24 samples area available and selected. Click [Save and done with samples] to move 
to the next step

7. Next iterate through the each of the 4 experiments and assist (highlight) the appropriate controls 
and interventions for each of the experiments.

8. Confirm that the sample files are associated with the correct experiment and have the appropriate I/C (intervention
or control) designation. Click [Confirm] to move to the next step to perform the calculations to generate
the group fold factors

9. 