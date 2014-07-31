# -*- coding: utf-8 -*-
"""
Spyder Editor

Built by Winthrop Gillis 7.11.2014

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

# TODO:
#     - add a figure of average channel values and std
#     - comment code so that others know how it works
"""
# change this to True when trying to imporove upon the code
DEBUG = False

import os

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

#import numpy as np # no need for numpy

# plotting library
import matplotlib.pyplot as plt
# data management library
import pandas as pd
# utility libraries
import glob, datetime, shutil, zipfile, smtplib
# classes to build an email message
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders
# contains the email and password to the gardner lab gmail account
from emailVars import em, passw


OUTPUT_FOLDER = 'processedData'

today = datetime.datetime.today()
# my sneaky way of figuring out which day monday is
monday = today - datetime.timedelta(today.weekday())
# add 4 days to get friday
friday = monday + datetime.timedelta(4)
# name of the folder containing this week's data
weekFolder = monday.date().isoformat() + ' to ' + friday.date().isoformat()

# make sure this folder already exists, and create it if it doesn't
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)
# this will be the folder path to put images and text files into
imagePath = os.path.join(OUTPUT_FOLDER, weekFolder)
# this will almost always make a new folder for the data, unless you run this code 
# twice in one week
if not os.path.exists(imagePath):
    os.makedirs(imagePath)
# figures and text data folders will be made here
figPath = os.path.join(imagePath, 'figures')
os.makedirs(figPath)
txtPath = os.path.join(imagePath, 'textFileData')
os.makedirs(txtPath)

def readFile(filename):
    ''' this reads in the text file as a csv with the tab key as the delimiter
    it also skips the starting lines of the file
    it uses the first column as the index
    '''
    df = pd.read_csv(filename, sep='\t', skiprows=[0,1,20], index_col=0,)
    # this gets the name of each column
    names = df.keys()
    # this removes the third column, which contains data about the phase
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
    # get all files that end in .txt
    files = glob.glob('*.txt')
    if files:
        #print files 
        # return all the data and the file names
        return [readFile(f) for f in files], files
    else:
        return None, None

def plotFig(dataFrame, filename, number):
    '''
    This function plots a graph for every file in the folder
    '''
    # get the column names
    demKeys = dataFrame.keys()
    # create a new dataframe (how the data is represented) with only the first set of datapoints
    dataFrame = pd.DataFrame(data=dataFrame[demKeys[0]], index=dataFrame.index)
    # returns a list of datapoints that have impedance values below 5 MOhms
    lessThan5 = [x for x in dataFrame[demKeys[0]] if x < 5]
    # average impedances for fibers with less than 5 MOhm impedances
    try:
	    smallAvg = sum(lessThan5)/ len(lessThan5)
    except Exception as e:
    	smallAvg = 1
    # actually plots the data
    ax = dataFrame.plot(kind='bar', title = files[number][:-4] + ' - ' + demKeys[0], legend=False, ylim=[0,4], color='r')
    #print dataFrame.std()
    # add informative text onto the figure
    ax.text(len(dataFrame.index) - 7, 2.8, 'Std: ' + str(dataFrame.std().item())[:5], fontsize=13)
    ax.text(len(dataFrame.index) - 7, 2.6, 'Average: ' + str(dataFrame.mean().item())[:5], fontsize=13)
    ax.text(len(dataFrame.index) - 10, 2.4 , 'Avg of channels w/ <5MOhms: ' + str(smallAvg)[:5], fontsize=13)
    # axes labels
    ax.set_xlabel('Channels')
    ax.set_ylabel(demKeys[0])

    # saves the figure
    fig = ax.get_figure()
    fPath = os.path.join(figPath, '{fName} - fig {num}.png'.format(fName = filename[:-4], num = number))
    fig.savefig(fPath)
    
def moveTextFiles():
    '''
    This function just moves all text files from the current directory
    to a folder located in the current week's folder
    '''
    files = glob.glob('*.txt')
    for f in files:
        shutil.move(f, os.path.join(txtPath, f))

def zipdir(path):
    '''
    This function creates a zip file of the compressed data
    '''
    with zipfile.ZipFile(path + '.zip', 'w') as z:
        for root, dirs, files in os.walk(path):
            for f in files:
                z.write(os.path.join(root, f))
    
def sendEmail(recipient, empty=False):
    '''
    Sends an email to the sepcified recipient.
    If there are no files present then an email will be sent out
    saying no impedances were tested this week
    '''
    if not empty:
        msg = MIMEMultipart()
        # Set subject of the message; using a global value
        msg['Subject'] = 'Impedance Values for the week of' + weekFolder
        msg['To'] = recipient
        # using a global value
        msg['From'] = em
        msg.attach(MIMEText('This is an automated script built by Win\nAttached are the array impedance values for this week: '))
        attach = MIMEBase('application', 'zip')
        with open(imagePath + '.zip', 'rb') as r:
            attach.set_payload(r.read())
        Encoders.encode_base64(attach)
        attach.add_header('Content-Disposition', 'attachment', filename=weekFolder + '.zip')
        msg.attach(attach)
        s = smtplib.SMTP('smtp.gmail.com:587') #465
        s.starttls()
        s.login(em, passw)
        s.sendmail(em, recipient, msg.as_string())
        s.quit()
    else:
        msg = MIMEText('No arrays were impedance tested this week. (Or at least their text files weren\'t put into this folder.)\n\nThis is an automated script made by Win')
        msg['Subject'] = 'No impedance values this week'
        msg['To'] = recipient
        msg['From'] = em
        s = smtplib.SMTP('smtp.gmail.com:587')
        s.starttls()
        s.login(em, passw)
        s.sendmail(em, recipient, msg.as_string())
        s.quit()


dataFrames, files = importFiles()

# do the following steps only if the files are present
if files:

    for index, (frame, fil) in enumerate(zip(dataFrames, files)):
        plotFig(frame, fil, index)

    moveTextFiles()

    zipdir(imagePath)

    if DEBUG:
        #sendEmail('wgillis@bu.edu')
        pass

    else:
        sendEmail('timothyg@bu.edu')
        
else:
    if DEBUG:
        #sendEmail('wgillis@bu.edu', empty = True)
        pass
    else: 
        sendEmail('timothyg@bu.edu', empty = True)
        
    # send an email saying there were no arrays that were tested in this week