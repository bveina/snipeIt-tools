""" functions for dealing with peoplesoft asset cotrol export files in csv format """
from apiMenu import getAllAssets
import os
import csv

defaultCSV = os.getenv('LOCALCSV')
if apiKey is None: raise Exception("enviroment variable for localCSV file not found")

def loadAssetControl(srcFileName=defaultCSV,filt = None):
    """ load a list in ASSET CONTROL FORMAT """
    matching=[]
    with open(srcFileName,'r') as f:
        reader = csv.DictReader(f)
        for ln in reader:
            if filt is None or filt(ln):
                matching.append(ln)
    return matching
 

def FilterInven(item):
    """ filters an ASSET CONTROL generated csv list for non computer items """
    if item['Asset Subtype'] in ['LAPTOP','DESKTOP','TABLET','SERVER','PRINTER']: return False
    return True
    
def FilterComputers(item):
    """ filters an ASSET CONTROL generated csv list for computer-like items """
    return not FilterInven(item)
    
def filterYif(item):
    """ filters an ASSET CONTROL generated csv list to find items that belong to Yifei Li """
    return 'Yifei' in item['Custodian'] or item['Location']=='DION-320'

def filterWang(item):
    """ filters an ASSET CONTROL generated csv list to find items that belong to Honggang Wang """
    return 'Honggang' in item['Custodian'] or '224' in item['Location'] or '209' in item['Location']
        
def FilterInvenPeople(item):
    """ filters an ASSET CONTROL generated csv list to not show items belonging to Wang or Li """
    if 'Yifei' in item['Custodian']: return False
    if 'Honggang' in item['Custodian']: return False
    return True

         
def cutePrintInvetory(x):
    """ prints a human readable ASSET CONTROL list """
    for ln in x:
        cost = float(ln['Cap Cost'])+float(ln['NonCap Cost'])
        print(" {Tag Number:7s} = {Location:10s} - {Descr:35s} - {Model:30s} - {Manufacturer:22s} + {Serial ID:15s} - {Asset Subtype:10s} * {Custodian} - ".format(**ln)+str(cost))
  
    
def compareInventory(srcFileName = defaultCSV, filt=lambda x: FilterInven(x) and FilterInvenPeople(x), cutePrint =True):
    """ returns a list of items is ASSET CONTROL FORMAT. 
        this list is items in the AC list but not on SNIPEIT. """
    w=getAllAssets()
    tags=[]
    for value in w:
        tags.append(value['asset_tag'])
    matching = []    
    with open(srcFileName,'r') as f:
        reader = csv.DictReader(f)
        for ln in reader:
            if ln['Tag Number'] not in tags:
                if (filt is not None) and (not filt(ln)): continue
                matching.append(ln)
                
    if cutePrint:
        cutePrintInvetory(matching)
    return matching

def compareComputerInventory(srcFileName=defaultCSV,filt=FilterInven):
    return compareInventory(srcFileName,filt,cutePrint=False)
   