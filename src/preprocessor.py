import csv
import re
import os


def preprocess(file):
    newrowslist = []
    seenrowslist = []
    x=0


    #open file and removve rows that have an invalid number of columns, have invalid format ie (ensambleid1 | ensambleid2), and add duplicates to the seenrows list
    with open(file, newline='\n') as csvfile:
        seen = []
        reader = csv.reader(csvfile, delimiter='\t')
        for row in reader:
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
            rowr.append(round(float(cc)))

        newdata.append(rowr)
    name = str(file)+".processed.txt"
    file2 = open(name, 'w', newline='')
    writer = csv.writer(file2, delimiter='\t')
    writer.writerows(newdata)
    file2.close()
    num_lines = sum(1 for line in open(file))
    num_lines2 = sum(1 for line in open(name))

    print(str(num_lines-num_lines2) + " Duplicates found")
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
    print(str(blanks)+ ' low values found out of ' + str(num_lines2))
    return(name)


