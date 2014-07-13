# -*- coding: utf-8 -*-
"""
Spyder Editor

Built by Winthrop Gillis 7.11.2014
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import glob, datetime, os, shutil, zipfile

#This script runs in the current directory. It runs through all the files 
#in the current directory, and reads in files that end in the .txt
#extension. This script expects that all the files are in the format
#created by the nanoZ for testing impedances. It will then parse the data,
#generate a separate figure of impedances for each array, and a figure of
#average impedance for each channel, and a total average impedance. It will 
#generate a .csv file that includes all of this data, so that it can be 
#analyzed in a larger dataset in the future.
#
#Using any file other than ones generated by the nanoZ may cause unwanted
#side-effects.
#
#-----------
#TO USE:
#    1. Put the files you want parsed into the same folder that this script
#       is in
#    2. Run this script
#    3. The files that you put in the same folder have been moved to a new
#       folder named for the week the impedances were checked
#    4. There will be a folder within that new week folder that contains
#       all the figures for each array, including an average impedance,
#       average connectivity, and standard deviation. In addition, there 
#       will be a formatted .csv file that contains all the data from the 
#       .txt files and the new data collected
#

OUTPUT_FOLDER = 'processedData'
today = datetime.datetime.today()
monday = today - datetime.timedelta(today.weekday())
friday = monday + datetime.timedelta(4)
weekFolder = monday.date().isoformat() + ' to ' + friday.date().isoformat()

cwd = os.path.dirname(os.path.realpath(__file__))
OUTPUT_FOLDER = os.path.join(cwd, OUTPUT_FOLDER)

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

imagePath = os.path.join(OUTPUT_FOLDER, weekFolder)

if not os.path.exists(imagePath):
    os.makedirs(imagePath)

figPath = os.path.join(imagePath, 'figures')
os.makedirs(figPath)
txtPath = os.path.join(imagePath, 'textFileData')
os.makedirs(txtPath)

def readFile(filename):
    df = pd.read_csv(filename, sep='\t', skiprows=[0,1,20], index_col=0,)
    names = df.keys()

    df = df.drop(names[-1], 1)
    names = names[:-1]
    #avgImp = df[names[0]].mean()
    #avgPhs = df[names[1]].mean()
    #df = df.append({names[0]: avgImp, names[1]: avgPhs}, ignore_index=True)
    #print df
    return df

def importFiles():
    """
    Import all of the files in the current directory that end in the .txt
    extension
    
    Returns a list of each file dataframe
    """
    # glob module provides easy filename handling
    files = glob.glob('*.txt')
    #print files 
    return [readFile(f) for f in files], files

def plotFig(dataFrame, filename, number):
    #dataFrame = dataFrame.append(dataFrame.mean(), ignore_index=True)
    demKeys = dataFrame.keys()
    dataFrame = pd.DataFrame(data=dataFrame[demKeys[0]], index=dataFrame.index)

    lessThan5 = [x for x in dataFrame[demKeys[0]] if x < 5]
    smallAvg = sum(lessThan5)/ len(lessThan5)
    
    ax = dataFrame.plot(kind='bar', title = files[number][:-4] + ' - ' + demKeys[0], legend=False, ylim=[0,3], color='r')
    #print dataFrame.std()
    ax.text(len(dataFrame.index) - 7, 2.8, 'Std: ' + str(dataFrame.std().item())[:5], fontsize=13)
    ax.text(len(dataFrame.index) - 7, 2.6, 'Average: ' + str(dataFrame.mean().item())[:5], fontsize=13)
    ax.text(len(dataFrame.index) - 10, 2.4 , 'Avg of channels w/ <5MOhms: ' + str(smallAvg)[:5], fontsize=13)
    ax.set_xlabel('Channels')
    ax.set_ylabel(demKeys[0])


    fig = ax.get_figure()

    fPath = os.path.join(figPath, '{fName} - fig {num}.png'.format(fName = filename[:-4], num = number))

    fig.savefig(fPath)
    
def moveTextFiles():
    files = glob.glob('*.txt')
    for f in files:
        shutil.move(f, os.path.join(txtPath, f))

def zipdir(path):
    with zipfile.ZipFile(path + '.zip', 'w') as z:
        for root, dirs, files in os.walk(path):
            for f in files:
                z.write(os.path.join(root, f))
    

dataFrames, files = importFiles()

for index, (frame, fil) in enumerate(zip(dataFrames, files)):
    plotFig(frame, fil, index)

moveTextFiles()

zipdir(imagePath)
