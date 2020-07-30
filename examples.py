import traceback
import csv


# script to add items from the Summit reporting list to eng assests based on a known model
# model should not be checked out to anything and should be marked ready to deploy
def testClone():
  cloneTag="320545"
  for w in t:

      tag = w['Tag Number']
      serial = w['Serial ID']
      if tag == cloneTag: continue
      print(" clone {0} with {1}:{2}".format(cloneTag,tag,serial))
      clone(cloneTag,newSN = serial,newTag=tag)



def CreateName2Tag():
  with open("/home/bveina/logs/sn.log","rt") as f:
    for line in f:
      name,serial = line.split('\t')
      item = findThing(serial.strip())
      try:
        if item is None:
          print( "{0}\t {1}".format(name,"NONE"))
        else:
          print("{0}\t {1}".format(name,item['asset_tag']))
      except:
          print("ERROR on {0},{1}".format(line.strip(),item))


class DmiInventoryObj:
#Company,Category,Status,Item Name,Asset Tag,Serial Number,Manufacturer,Model,Model Number,CPU,MAC Address,Total Ram
    def __init__(self):
      self.name=""
      self.serial=""
      self.make=""
      self.model=""
      self.cpu=""
      self.mac=""
      self.ram=""
      self.tag=""
    def __init__(self,myDict):
      self.name=myDict['Item Name']
      self.serial=myDict['Serial Number']
      self.make=myDict['Manufacturer']
      self.model=myDict['Model']
      self.cpu=myDict['CPU']
      self.mac=myDict['MAC Address']
      self.ram=myDict['Total Ram']
      self.tag=myDict['Asset Tag']

doBlind = False
def compareAndUpdate(webItem,getCurrentVal,tempVal,fieldName):
  global doBlind
  try:
    currentVal = getCurrentVal(webItem)
    if currentVal is not None:
      currentVal=currentVal.strip()
    if tempVal is not None:
      tempVal=tempVal.strip()
    if currentVal != tempVal:
      # if its blank or a case insensitve compare matches dont bother asking
      if doBlind is True:
        res = ""
      elif currentVal is None:
        res=""
      elif len(currentVal) == 0:
        res = ""
      elif currentVal.upper() == tempVal.upper():
        res=""
      else:
        res=input("{2}/{3} - press enter to update -{0}- to -{1}-, N to cancel".format(currentVal,tempVal,webItem['serial'],webItem['asset_tag']))
      if res == "":
       print("setting {0}/{4}'s *{1}* field from '{2}' <- '{3}'".format(webItem['serial'],fieldName,currentVal,tempVal,webItem['asset_tag']))
       update_item(webItem,fieldName,tempVal,Note="Data Pulled Directly from machine")
       item = findThing(webItem['serial'])
       if getCurrentVal(item) == tempVal:
          print("sucess")
       else:
          print("failure")
  except Exception as e:
    print("{2} -  big problem with setting {0}: {1}".format(fieldName,e,webItem['asset_tag']))
    print("item: {0}".format(item))
    t=input()
    if t =="":
      print(traceback.format_exc())
      raise e



def DoInvenUpdate():
  with open('/home/bveina/logs/inventory.csv','rt') as csvFile:
    reader = csv.DictReader(csvFile)
    for row in reader:
      temp = DmiInventoryObj(row)
      item = findThing(temp.tag)
      if item is None:
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
