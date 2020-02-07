# script to add items from the Summit reporting list to eng assests based on a known model
# model should not be checked out to anything and should be marked ready to deploy
cloneTag="320545"
for w in t:
	
	tag = w['Tag Number']
	serial = w['Serial ID']
	if tag == cloneTag: continue
	print(" clone {0} with {1}:{2}".format(cloneTag,tag,serial))
	clone(cloneTag,newSN = serial,newTag=tag)
	
	

class DmiInventoryObj:
    def __init__(self):
      self.name=""
      self.serial=""
      self.make=""
      self.model=""
      self.cpu=""
      self.mac=""
      self.ram=""
    def __init__(self,myDict):
      self.name=myDict['Name']
      self.serial=myDict['Serial']
      self.make=myDict['Make']
      self.model=myDict['Model']
      self.cpu=myDict['CPU']
      self.mac=myDict['MAC']
      self.ram=myDict['RAM']



def compareAndUpdate(webItem,getCurrentVal,tempVal,fieldName):
  global doBlind
  try:
    currentVal = getCurrentVal(webItem)
    if currentVal != tempVal:
      # if its blank or a case insensitve compare matches dont bother asking
      if doBlind is True:
        res = ""
      elif len(currentVal) == 0:
        res = ""
      elif currentVal.upper() == tempVal.upper():
        res=""
      else:
        res=input("press enter to update {0} to {1}, N to cancel".format(currentVal,tempVal))
      
      if res == "":
       print("setting {0}'s *{1}* field from '{2}' <- '{3}'".format(webItem['serial'],fieldName,currentVal,tempVal))
       update_item(webItem,fieldName,tempVal,Note="Data Pulled Directly from machine")
       item = findThing(webItem['serial'])
       if getCurrentVal(item) == tempVal:
          print("sucess")
       else:
          print("failure")
  except Exception as e:
    print("big problem with setting {0}: {1}".format(fieldName,e))
    input()
      
    
with open('/home/bveina/logs/inventory.csv','rt') as csvFile:
  reader = csv.DictReader(csvFile)
  for row in reader:
    temp = DmiInventoryObj(row)
    item = findThing(temp.serial)
    if item is None:
      print("couledn't find this thing {0} - {1}".format(temp.name,temp.serial))
      continue
    if type(item) is list:
        print ("this item exists more than once!!!")
        input()
    
    
    compareAndUpdate(item,lambda x:  x['custom_fields']['MAC Address']['value'], 
        makeProperMAC(temp.mac),"_snipeit_mac_address_1")
    compareAndUpdate(item,lambda x: x['name'], temp.name,"name")
    compareAndUpdate(item,lambda x:  x['custom_fields']['CPU']['value'], temp.cpu,"_snipeit_cpu_4")
    compareAndUpdate(item,lambda x:  x['custom_fields']['RAM']['value'], temp.ram,"_snipeit_ram_5")
    
    
    
    
	
## script to take the results of a Kase export and fix any typos in the engDatabase (presumably cause by importing directly from summit)    
with open('kace.csv','rt') as csvfile:
  reader = csv.DictReader(csvfile)
  for row in reader:
    if row['s/n'] != row['s/n umassd']:
      t = findThing(row['tag'])
      currentTag = row['tag']
      currentSerial = str(t['serial'])
      umassSerial = str(row['s/n umassd'])
      kaceSerial = str(row['s/n'])
      
      if t is None:
        print("{}: couldn't find this tag in engAssets".format(currentTag))
        continue
      else:
        print("{}: found {} vs {}".format(currentTag,currentSerial,kaceSerial))
      needsFix=None
      if currentSerial == umassSerial:
        print("{}: engAssests took umassd Bad Data".format(currentTag))
        needsFix=True
      elif currentSerial != umassSerial and currentSerial != kaceSerial:
        print("{}: engAssests has completely bogus data".format(kaceSerial))
        needsFix=True
      elif currentSerial == kaceSerial:
        needsFix==False
      else:
        raise Exception("unhandled serial/tag case")
      
      if needsFix == True:
        print("{}: changing serial number from {} to {}".format(currentSerial,kaceSerial))
        
      