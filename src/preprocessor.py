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

import csv
import re
import logging
import os

logger = logging.getLogger(__name__)


def preprocess(file):
    newrowslist = []
    seenrowslist = []
    x=0
    empty = 0



    decimals = 0
    #open file and removve rows that have an invalid number of columns, have invalid format ie (ensambleid1 | ensambleid2), and add duplicates to the seenrows list
    with open(file, newline='\n') as csvfile:
        seen = []

        reader = csv.reader(csvfile, delimiter='\t')
        for row in reader:
            if (row[0] == ""):
                row[0] = "Ensembl ID"
            row = list(filter(None, row))



            if(x==0):
                rowcount = len(row)
                x=1
            if(len(row)==rowcount):
                if(row[0].find("Dose")>=0):
                    continue
                if(row[0].find("|")>0):
                    row[0]=re.sub(r"\|.*","",row[0])
                if row[0] in seen:
                    seenrowslist.append(row)

                    continue


                seen.append(row[0])
                newrowslist.append(row)

    #combine duplicate rows values
    for row2 in newrowslist:
        for x in seenrowslist:
            if(x[0]==row2[0]):
                counter = 0
                vals = []
                for a in row2:
                    if counter == 0:
                        vals.append(a)
                        counter = counter + 1
                        continue
                    vals.append(str(int(a)+int(x[counter])))
                    counter = counter + 1
                ind = newrowslist.index(row2)
                #print(vals)
                newrowslist[ind]= vals
                break
    newdata = []
    testvar = 0
    #check for decimals and round
    for rr in newrowslist:
        if(testvar==0):
            newdata.append(rr)
            testvar=1
            continue
        rowr = []
        trt = 0
        for cc in rr:
            if(trt == 0):
                trt=1
                rowr.append(cc)
                continue
            #print(rr)
            if(cc.find(".")>0):
                decimals = decimals+1
            else: empty = empty+1
            rowr.append(round(float(cc)))

        newdata.append(rowr)
    name = str(file).replace(".txt","")+"processed.txt"
    file2 = open(name, 'w', newline='')
    writer = csv.writer(file2, delimiter='\t')
    writer.writerows(newdata)
    file2.close()
    num_lines = sum(1 for line in open(file))
    num_lines2 = sum(1 for line in open(name))

    logger.debug(str(num_lines-num_lines2) + " Duplicates found")
    blanks = 0
    rowskip = 0
    for row3 in newdata:


        if(rowskip == 0):
            rowskip = 1
            continue
        sumnum = 0
        skiper = 0
        for z in row3:



            if(skiper == 0):
                skiper = 1
            else:

                sumnum = int(sumnum) + int(z)


        if sumnum <=rowcount*2:
            blanks += 1
    decimals = decimals/empty
    logger.debug(str(blanks)+ ' low values found out of ' + str(num_lines2))
    os.remove(file)
    os.rename(name, str(name).replace("processed.txt",".txt"))
    return([str(name).replace("processed.txt",".txt"),decimals])


