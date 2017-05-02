
#This the script to generate the dictionary
#########Control Dictionary and Experiement Dictionary


#!C:\Users\mpradhan\AppData\Local\Programs\Python\Python36-32\python.exe
#utils.py

import os
import argparse
import csv
import logging
import sys
import builtins
import json
import sys
import numpy as np
from builtins import zip
from numpy import array



def read_input_file(infile):
    csv_reader = csv.reader(infile, delimiter = ",")
    array=[]
    key =[]
    var = "CTL"
    dict_control = {}
    dict_trt = {}
    var1 = "TRT"
    key1= []
    value1 = []

    for row in csv_reader:
        print (row)

        if row[0] == var:
            key = row[1]
            value = row[2]
            dict_control.setdefault(key, []).append(value)

        elif (row[0]==var1):
            key1 = row[1]
            value1 = row[2]
            dict_trt.setdefault(key1, []).append(value1)

    print(dict_control)
    print (dict_trt)

    #######Create and write the control dictionary for the whole data
    ########Create and write the treatment dictionary for the whole data

    f = dict_control.keys()
    with open ('controldict.csv','w') as csvfile:
        w=csv.DictWriter(csvfile,fieldnames=f)
        w.writeheader()
        w.writerow(dict_control)

    ff = dict_trt.keys()
    with open ('treatmentdict.csv','w') as csvfile:
        w=csv.DictWriter(csvfile,fieldnames=ff)
        w.writeheader()
        w.writerow(dict_trt)

###########make dictionary for the number of samples in the control dict for each key
#####make dictionary for the number of samples in the treatment for each key

    dict_control_count = {}
    for key, values in dict_control.items():
            len(values)
            print (key, len(values))
            dict_control_count.setdefault(key,[]).append(len(values))


    dict_treatment_count = {}
    for key, values in dict_trt.items():
            len(values)
            dict_treatment_count.setdefault(key,[]).append(len(values))


##############Write the above two count dictionary to a csv file

    f= dict_control_count.keys()
    with open ('countcontroldict.csv','w') as csvfile:
        w=csv.DictWriter(csvfile,fieldnames=f)
        w.writeheader()
        w.writerow(dict_control_count)

    ff= dict_treatment_count.keys()
    with open ('counttreatmentdict.csv','w') as csvfile:
        w=csv.DictWriter(csvfile,fieldnames=ff)
        w.writeheader()
        w.writerow(dict_treatment_count)

######################################Get the path for the CEL files
########Store the Path in 3 files (1) Control (2) Treatment (3) Both Control and Treatment

    xx="00"
    ext=".CEL"

    fname = "U:/python/TOX/ModuleBuilding_Temp/Temp_March1/treatment.txt"
    #print(fname)
    ff = open(fname, "a")

    fn = "U:/python/TOX/ModuleBuilding_Temp/Temp_March1/control.txt"
    #print(fn)
    fnn = open(fn, "a")

    ffnn = "U:/python/TOX/ModuleBuilding_Temp/Temp_March1/controltreatment.txt"
    #print(ffnn)
    ffnn = open(ffnn, "a")


    for k in dict_control:
        for kk in dict_trt:
            if k == kk:
                #print(k,kk)

                for elem in dict_trt[kk]:
                    #print (elem)
                    newelem=xx+elem
                    newname = newelem+ext
                    #print(newname)
                    for file in os.listdir("C:/Users/mpradhan/Documents/Toxicogenomis_Lilly_DAS/Data/CEL"):
                        if (newname == file):
                            nname = "C:/Users/mpradhan/Documents/Toxicogenomis_Lilly_DAS/Data/CEL/"+file
                            #print(nname)
                                #print ("YES  "+file)
                            ff.write(nname+'\n')
                            ffnn.write(nname+'\n')


    for k in dict_control:
        for kk in dict_trt:
            if k == kk:
                #print (k, kk)

                for elem in dict_control[kk]:
                    #print (elem)
                    newelem=xx+elem
                    newname = newelem+ext
                    #print(newname)
                    for file in os.listdir("C:/Users/mpradhan/Documents/Toxicogenomis_Lilly_DAS/Data/CEL"):
                        if (newname == file):
                            nname = "C:/Users/mpradhan/Documents/Toxicogenomis_Lilly_DAS/Data/CEL/"+file
                            #print(nname)
                                #print ("YES  "+file)
                            fnn.write(nname+'\n')
                            ffnn.write(nname+'\n')



    return




if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='dictionary.py',description='parameters to scale.')
    parser.add_argument('-i', '--infile', dest="infile", type=argparse.FileType('r'),
                        help='The input file to print.',
                        required=True)





    args = parser.parse_args()
    read_input_file(args.infile)
