""" functions for dealing with peoplesoft asset cotrol export files in csv format. 
    in all likelyhood no one but me will ever need this functionality so ive abstracted it to its own file.
    the csv files have the following structure
    OrderedDict([('Unit', 'SSSSSS'),
             ('Dept', 'D#########'),
             ('Custodian', 'Smith,John'),   #
             ('EMPLID', '12345678'),
             ('Asset ID', '000000######'),  #
             ('Tag Number', '316454'),      #
             ('Location', 'ROOM-123'),      #
             ('Cap Cost', '0.00'),
             ('NonCap Cost', '2250.00'),
             ('Acquired Date', '1/01/2000'),
             ('Descr', 'Fluke Calibrator'),
             ('Model', '5100B'),
             ('Serial ID', 'xxxxxxxx'),
             ('Manufacturer', 'Fluke'),
             ('Subtype', ''),
             ('Custodian Subtype', ''),
             ('Last Inventory', '12/3/2015'),
             ('Profile ID', '#####'),
             ('PO No.', 'yyyyyyyyyy'),
             ('Project', 'Szzzzzzzzz')])
"""

"""
*** new export format ***
Business Unit, UMDAR
Asset ID,Capital, 000000212848
Acquisition Date, MM/DD/YYYY
Index, "PRIMARY" or blank
Location, SE-214B
Custodian Dept ID, D269000xxx
Custodian, "Viall,Ben"
Inventory Date, MM/DD/YYYY
Comments, blank
Amount, $1234.00
Performed By, APINTFC/Annette/ONLINE
Description, Desktop dell Optiplex 7060
Manufacturer, Dell
Model, Optiplex 760
Serial ID,
Tag Number, 
Subtype, APINTFC ???
PI ID,
Taggable,
Building, "SE"
Floor, 2
Profile, H40050 - Lab,Scientific,Research 5 yr
Custodian ID, 10117417
Room, 214F
Description, ECE-Honggang Wang
Inventory Fiscal Year, 2017
"""

from apiMenu import getAllAssets
import os
import csv

defaultCSV = os.getenv('LOCALCSV')
if defaultCSV is None: raise Exception("enviroment variable for localCSV file not found")

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
    if item['Subtype'] in ['LAPTOP','DESKTOP','TABLET','SERVER','PRINTER']: return False
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
        cost = float(ln['Amount'])
        print(" {Tag Number:7s} = {Location:10s} - {Description:35s} - {Model:30s} - {Manufacturer:22s} + {Serial ID:15s} - {Subtype:10s} * {Custodian} - ".format(**ln)+str(cost))
  
def findAssetControl(tag):
    """ search for an ASSET CONTROL item by tag """
    x = loadAssetControl(filt=lambda x: x['Tag Number']==tag or x['Serial ID']==tag)
    cutePrintInvetory(x)
    return x
    
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
   
