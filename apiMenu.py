import requests
import json
import time
from barManual import makeTag,printLabel
import datetime
#import winsound
import os
from colors import *


if os.name=='nt':
    import winsound


apiKey= os.getenv('APIKEY')
if apiKey is None: raise Exception("enviroment variable for apiKey not found")
baseURL = os.getenv('BASEURL')
if baseURL is None: raise Exception("enviroment variable for baseURL not found")

needsPrint=False

def genericPayload(reqType,subaddress,append=None,payload=None,extraParams=None,fileParam=None):
    """ wrapper for requests.request with default values for the snipe-it api
    reqType -- string (eg get, post,patch,delete)
    subaddress -- the rest endpoint
    append -- if there is an extra component to the api endpoint it can be added here.
    payload -- a dictionary that will be the json payload in the request
    """
    global needsPrint
    headers = {"Authorization":"Bearer "+apiKey,
    'Content-Type': 'application/json',
    "Accept":"application/json"}
    if append is not None:
        fullAddr = baseURL+subaddress+append
    else:
        fullAddr = baseURL+subaddress
    response = requests.request(reqType,fullAddr,headers=headers,json=payload,params=extraParams,files=None)
    if needsPrint: print(reqType,response.status_code,fullAddr)
    if response.status_code !=200:
        if needsPrint: print( response.content)

    if response.status_code == 200:
        return json.loads(response.content)
    return None

def updateStudentIDs(listofEmail_Ids):
  # [ ['stu@umassd.edu', '12345678], ...]
  for p in listofEmail_Ids:
    userid = findUserByEmail(p[0])
    #print( p[1],userid)
    if userid is None:
      print("cant find {0}".format(p))
      continue
    genericPayload('patch','users/{0}'.format(userid),payload={'employee_num':p[1]})


def findUser(filt,defaultSize=500):
    offset=0
    r = genericPayload('get','users',payload={'limit':1,'offset':offset})
    total=r['total']
    while (offset<total):
      r =genericPayload('get','users',payload={'limit':defaultSize,'offset':offset})
      try:
        found= list(filter(filt,r['rows']))
      except:
        print("Filter={0}".format(filt))
        print(r.keys())
        raise Exception
      if (len(found)>0):
        return found[0]
      offset+=len(r['rows'])
    if len(found)==1:
      return found[0]

def findUserById(userIdNumebr,defaultSize=500):
    return findUser(lambda x: x['employee_num'] == userIdNumebr,defaultSize)
def findUserByEmail(email,defaultSize=500):
    return findUser(lambda x: x['email'] == email,defaultSize)
    
def bulkStudentSignout():
  while(1):
    stuId=input("StudentId: ")
    student=findUserById(stuId)
    while(student is None):
      stuId=input("Cant Find!\nStudentId: ")
      student=findUser(stuID)
    ItemId=input("Item: ")
    x=findThing(ItemId)
    confirm = input("do you want to check out\n{0}- {1}\nto\n{2}".format(ItemId,x['model']['name'],student['email']))
    if confirm.lower()=='y':     
     checkOut_user(x,student['id'])
    


def getAllAssets(filt=None,defaultSize=500):
    """
    retrieves every asset in the snipe-it instance
    filt -- optional filter function, only return a list of items which match 'filt'
    defaultSize -- assets are fetched in chuncks of size (eg 500 at a time)
    """
    w=[] # w holds the filtered result set of items
    offset=0
    count = 0 # how many items have we fetched (will not equal len(w) if filt is not None)

    # dummy get, to find total number of items
    r = genericPayload('get','hardware',None, {'limit':1,'offset':offset})
    total = r['total']

    while (count<total):
        r = genericPayload('get','hardware',None, {'limit':defaultSize,'offset':offset})
        count += len(r['rows'])
        if filt is not None:
            for item in r['rows']:
                try:
                    if filt(item):
                        w.append(item)
                except:
                    print('couldent filter ',item)
        else:
            w+=r['rows']
        offset+=len(r['rows'])
    return w

def createAsset(model,status,tag=None):
    """
    creates a new asset in the database with a given model,status, and tag number
    if tag is None the tag number is auto generated using the system settings
    """
    payload = {  'status_id': status, 'model_id': model }
    if tag is not None:
        payload['asset_tag']=tag
    return genericPayload('post','hardware',None,payload)

def deleteAsset(uid):
    """ given a asset id number, remove the asset from the system """
    return genericPayload('delete','hardware/',str(uid))


def getAssetByTag(tag):
    """ get a single asset by providing its tag number
        if asset does not exists return payload will have
        b'{"status":"error","messages":"Asset not found","payload":null}'

        if asset exists 'id' will be present
    """
    return genericPayload('get','hardware/bytag/',str(tag))

def getAssetBySerial(SN):
    """ get a list of assets by providing a serial number
        if asset does not exist:
         {'total': 0, 'rows': []}

        if asset does exist:
         {'total': 1, 'rows':[...]}
    """
    return genericPayload('get','hardware/byserial/',str(SN))

def findThing(data,hideArchived=True,DeepSearch=False):
    """ query snipe it and find any items that match either a Serial Number or an asset tag """
    #this will probably need to change as the API gets updated to be more consistant

    if DeepSearch:
        x= getAllAssets(filt = lambda x: (x['asset_tag']==data) or (x['serial']==data))
        if len(x)==1:
            return x[0]
        else:
            return x

    ja = getAssetByTag(data)
    jb = getAssetBySerial(data)

    if ja is None and jb is None: return None

    if ja is not None and ja.get('id') is not None:
        return ja

    if jb.get('rows') is not None:
        jb=jb['rows']
    else:
        return None

    if len(jb)==1:
       return jb[0]
    elif len(jb)>1:
        # remove any deleted items
        jc = list(filter(lambda x: x['deleted_at'] is None, jb))
        if hideArchived:
          jc = list(filter(lambda x: x['status_label']['id'] == 3, jc))
        if len(jc)==1:
          return jc[0]
        else:
          return jc
    else:
        return None

#TODO: this relies on barManual.py... this is an odd dependancy
def scanAndLabel(TagOnly=False):
    snOrtag=input("scan SN or assetTag: ")
    t=findThing(snOrtag)
    if t is None:
        print("there is no item for {t}",t)
        return #yes i could add the thing now

    if type(t) is list: # there are multiple things that have this id
      print("found multiple valid instances of {0} will not continue".format(snOrtag))
      return

    if TagOnly:
      makeTag(None,t['asset_tag'],'tmp.png')
    else:
      makeTag(t['serial'],t['asset_tag'],'tmp.png')
    printLabel('tmp.png')


#tested only with items that are not checked out
def clone_old(tag2Clone,newSN=None,newTag=None,newMAC=None):
    ja = getAssetByTag(tag2Clone)
    if ja.get('status') is not None:
        print("cant clone that ID")
        return 0

    #clonableTags=['notes','assigned_to']
    clonableTags=['notes']
    dolly = {} #like the sheep its gonna be a clone
    for field in clonableTags:
        dolly[field]=ja[field]

    #status_id, model_id,company_id are burried in another field...
    if ja['status_label'] is not None:dolly['status_id'] = ja['status_label']['id']
    if ja['model'] is not None:dolly['model_id'] = ja['model']['id']
    if ja['company'] is not None:dolly['company_id'] = ja['company']['id']
    if ja['rtd_location'] is not None:dolly['rtd_location_id'] = ja['rtd_location']['id']

    if newSN is not None and newSN != '':
        dolly['serial']=newSN
    if newTag is not None and newTag !='':
        dolly['asset_tag']=newTag

    if newMAC is not None and newMAC !='':
        dolly['_snipeit_mac_address_1'] = newMAC

    #print(dolly)
    return genericPayload('post','hardware',None,dolly)



def  ErrorBeep(s="Error"):
  if os.name=='nt':
    winsound.Beep(440,500)
  print(color(s,'red'))


def SuccessBeep(s="success"):
  if os.name=='nt':
    winsound.Beep(1000,300)
  print(color(s,'green'))

def  NotFoundBeep(s="Not Found"):
  if os.name=='nt':
    winsound.Beep(440,500)
  print(color(s,'orange'))

def UpdateBeep(s="updated"):
  if os.name=='nt':
    winsound.Beep(1760,100)
  print(color(s,'blue'))

def CheckInOutBeep(s="Check in/out"):
  if os.name=='nt':
    winsound.Beep(1760,100)
  print(color(s,'cyan'))


def archive(item,note=None):
  if item is None: return None
  if item['assigned_to'] is not None:
    #check it it.
    checkIn(item,None,'Auto Decomissioned')
  payload = {}
  payload['status_id']=3 # archived
  if note is not None and (item['notes'] is not None and note not in item['notes']):
    if item['notes'] is None:
      payload['notes']=note
    else:
      payload['notes']=item['notes']+"\r\n"+note
  itemId = item['id']
  return genericPayload('patch','hardware/',str(itemId),payload)


def clone(tag2Clone,newSN=None,newTag=None,newMAC=None):
    ja = getAssetByTag(tag2Clone)
    if ja.get('status') is not None:
        print("cant clone that ID")
        return 0

    clonableSpecial = [
        ('status_id',lambda x: x['status_label']['id']),
        ('model_id',lambda x: x['model']['id']),
        ('company_id',lambda x: x['company']['id']),
        ('rtd_location_id',lambda x: x['rtd_location']['id']),
        ('notes',lambda x: x['notes']),
        ('assigned_to',lambda x: x['assigned_to']),
        ]

    clonableTags=['notes','assigned_to']
    dolly = {} #like the sheep its gonna be a clone
    for dst,src in clonableSpecial:
        dolly[dst]=src(ja)


    if newSN is not None and newSN != '':
        dolly['serial']=newSN
    if newTag is not None and newTag !='':
        dolly['asset_tag']=newTag

    if newMAC is not None and newMAC !='':
        dolly['_snipeit_mac_address_1'] = newMAC

    return genericPayload('post','hardware',None,dolly)

def makeProperMAC(s):
    """ create a MAC address string in SNIPEIT format (eg XX:XX:...)"""
    #option one: this is already XX:XX:XX:XX:XX:XX
    if len(s.split(':')) ==6:
      return s
    if len(s)==12: #option 2 aabbccddeeff
      return ":".join([s[i:i+2] for i in range(0, len(s), 2)])
    # option 3: aa-bb-cc-dd-ee-ff
    if len(s.split('-')) == 6:
      return ":".join(s.split('-'))

def bulkArchive(note=None,DeepSearch=False):
  while(1):
    sn= input('scan new serial #: ')
    ja = findThing(sn,DeepSearch=DeepSearch)
    if ja is None:
      print("cant find any item matching '{0}'".format(sn))
      NotFoundBeep()
      continue

    if type(ja) is list: # there are multiple things that have this id
      print("found multiple valid instances of {0} will not continue".format(sn))
      continue

    res=archive(ja,note)

    if res is None:
      ErrorBeep()
      continue

    if ('status' not in res.keys()):
      #error
      ErrorBeep()
      continue

    if (res['status'] == 'success'):
      SuccessBeep()
    else:
      ErrorBeep()

def bulkCloneOffUmass(donerTag,needsSticker=True):
    """ repeatedly clone items that do not have existing asset tags """
    while(1):
        sn= input('scan new serial #: ')
        tmp = findThing(sn)
        if tmp is not None:
          ErrorBeep()
          print("asset already exists")
          continue
        res = clone_old(donerTag,sn,None) #providing None autoGens the tag number
        if 'status' not in res.keys():
          ErrorBeep()
          print("cant determine status of clone")
          continue

        if res['status'] != 'success':
          ErrorBeep()
          print("could not clone '{0}'".format(res['status']))
          continue

        SuccessBeep()
        if needsSticker:
            time.sleep(1)
            t=findThing(sn)
            makeTag(t['serial'],t['asset_tag'],'tmp.png')
            printLabel('tmp.png')

def bulkCloneOnUmass(donerTag,needsSticker=True):
    """ repeatedly clone items that have asset tag number but are not yet in snipe it """
    while(1):
        sn= input('scan new serial #: ')
        nTag = input('Existing Tag #: ')
        clone(donerTag,sn,nTag) #providing None autoGens the tag number
        time.sleep(1)
        t=findThing(nTag)
        if type(t) is list:
              print("multiple things apply to tag {0}".format(nTag))
              continue
        if t.get('serial') is None: print( t)
        if needsSticker:
            makeTag(t['serial'],t['asset_tag'],'tmp.png')
            printLabel('tmp.png')


def bulkCloneOnUmassMAC(donerTag, printTag=False):
    """ clones items with existing tags that also have mac addresses """
    while(1):
        sn= input('scan new serial #: ')
        nTag = input('Existing Tag #: ')
        MAC = input('MAC ADDRESS: ')
        MAC = makeProperMAC(MAC)
        clone(donerTag,sn,nTag,MAC) #providing None autoGens the tag number
        if (printTag):
            time.sleep(1)
            t=findThing(nTag)
            if type(t) is list:
              print("multiple things apply to tag {0}".format(nTag))
              continue
            if t.get('serial') is None: print(t)
            makeTag(t['serial'],t['asset_tag'],'tmp.png')
            printLabel('tmp.png')

def printAssetModels():
    """ displays a list of SNIPEIT asset models """
    j = genericPayload('get','models')
    total = j['total']
    rows = j['rows']
    for r in rows:
        print(r['id'],r['name'],r['model_number'])

def audit(tagNum,roomId,nextDate=None,note=None):
    """ simple audit of a snipe it object.
        default next date is + 6 months
    """
    if nextDate is None:
        nextDate =  str(datetime.date.today() + datetime.timedelta(6*365/12)) +" 00:00:00"

    payload = { 'asset_tag': tagNum, 'location_id': roomId , 'next_audit_date':nextDate}

    if note is not None:
        payload['note']= note

    return genericPayload('post','hardware/audit',None,payload)

def auditStockroom(roomId=6):
    """ helper function to return items to the stock room """
    return auditMode(roomId,autoMove=False,removeUser=True)

def auditMode(roomId=None, autoMove=True,removeUser=False):
    """ audit mode is a smarter audit that update locations in SNIPEIT based on context
    checked out to user? leave checked out but update location_id
    checked out to location? check in then check back out to new location
    not checked out? only change location.

    not currently supported: items checked out to assets.

    roomId -- the room you are auditing. if not provided, you will be prompted with a list of locations.
    autoMove -- if asset is checked out to a different room, should it be checked out again, or just have its location updated
    removeUser -- if asset is checked out to a user, should the audit check it back in?
    """
    w=getAllAssets()

    if roomId is None:
        #choose the room you are auditing.
        for loc in sorted(genericPayload('get','locations')['rows'],key=lambda x: x['name']):
            print("{id:5} - {name}".format(**loc))
        roomId = int(input(' choose a room ID: '))

    #scan labels forever and print success or failure
    while (1):
        ID = input('scan tag or SN: ')

        #check the inventory list
        items=list(filter(lambda x:x['asset_tag'].upper()==ID.upper() or x['serial'].upper()==ID.upper(),w))
        if len(items)==0:
            print(color('cant find {0}'.format(ID),'red'))
            NotFoundBeep()
            continue

        if len(items)==1:
            index=0
        else:
            for idx,i in enumerate(items):
                print('{0} - {1}'.format(idx,"{asset_tag} - {serial}".format_map(i)))
            index = int(input('choose idx: '))

        myItem = items[index]
        #we now have an item that should be audited
        r = audit(myItem['asset_tag'],roomId)


        #todo: do we care what happens if its deployed to an asset?

        #deployed to a location?
        if (isDeployed(myItem) and deployedLocationId(myItem) is not None
            and deployedLocationId(myItem) != roomId): #that is not where i found it, then
            #checkin asset, with a note to the audited room, then check it out to the new room
            checkIn(myItem,roomId=roomId,note='auto checkin during audit')
            CheckInOutBeep()
            if autoMove:
                checkOut_location(myItem,roomId,note='auto checkout during audit')
                CheckInOutBeep()
        #deployed to a user
        elif isDeployedToUser(myItem) and (myItem['location'] is None or myItem['location']['id']!=roomId):
            if removeUser==True:
                checkIn(myItem,roomId=roomId,note='auto checkin during audit')
                CheckInOutBeep()
            update_location(myItem,roomId)
            UpdateBeep()
        elif not isDeployed(myItem):
            #not signed out to a user, or a location so in addition to auditing it, change its location.
            if autoMove:
              checkOut_location(myItem,roomId,note='auto checkout during audit')
              CheckInOutBeep()
            else:
              update_location(myItem,roomId)


        if r['status']=='success':
            SuccessBeep()
            print(colors.color('success',fg='green'))
        else:
            ErrorBeep()
            print(colors.color(r['status'],fg='red'))

def checkIn(item,roomId=None,note=None):
    """ interface function to SNIPEIT to check assset in """
    payload= {}
    itemId=item['id']
    if roomId is not None:
        payload['location_id']=roomId
    if note is not None:
        payload['note']=note
    return genericPayload('post','hardware/'+str(itemId),'/checkin',payload)

def update_location(item,roomId):
    """ update a SNIPEIT asset location """
    payload = {'location_id':roomId}
    itemId=item['id']
    return genericPayload('patch','hardware/'+str(itemId),None,payload)

def update_item(item,key,value,Note=None):
    """ update a SNIPEIT asset value """
    payload = {key:value}
    if Note is not None:
      payload['note'] = Note
    itemId=item['id']
    return genericPayload('patch','hardware/'+str(itemId),None,payload)


def checkOut_user(item,userId,note=None):
    """ check out an asset to a location """
    payload={}
    itemId = item['id']
    # 'assigned_user', 'assigned_asset'
    payload['checkout_to_type'] = 'user'
    payload['assigned_user' ]=userId
    if note is not None:
        payload['note']=note
    # i assume this exists for use during cached operations 
    # but im not really sure why i did this
    setdeployedUserId(item,userId) 
    return genericPayload('post','hardware/'+str(itemId),'/checkout',payload)


def checkOut_location(item,roomId,note=None):
    """ check out an asset to a location """
    payload={}
    itemId = item['id']
    # 'assigned_user', 'assigned_asset'
    payload['checkout_to_type'] = 'location'
    payload['assigned_location' ]=roomId
    if note is not None:
        payload['note']=note
    setdeployedLocationId(item,roomId)
    return genericPayload('post','hardware/'+str(itemId),'/checkout',payload)

def bulkMaintenance():
  myNote=input("provide common Note:")
  myTitle= input("provide common Title:")
  datestamp = input("date:")
  while(1):
    sn= input('scan tag #: ')
    ja = findThing(sn)
    if ja is None:
      print("cant find any item matching '{0}'".format(sn))
      NotFoundBeep()
      continue

    if type(ja) is list: # there are multiple things that have this id
      print("found multiple valid instances of {0} will not continue".format(snOrtag))
      continue

    payload={}
    payload['supplier_id']=2 #stockroom
    payload['is_warranty']=False
    payload['cost']=0
    payload['notes']=myNote

    payload['asset_id'] = ja['id']
    payload['asset_mainenance_type'] = "Maintenance"
    payload['title'] = myTitle
    payload['start_date']  = datestamp
    payload['completion_date']   = datestamp

    res=genericPayload('POST','maintenances',None,payload)
    print(res)
    #res=archive(ja)

    if res is None:
      ErrorBeep()
      continue

    if ('status' not in res.keys()):
      #error
      ErrorBeep()
      continue

    if (res['status'] == 'success'):
      SuccessBeep()
    else:
      ErrorBeep()


def uploadFile(assetID,filePath):
  res=None
  with open(filePath,'rb') as f:
   files = {'file': f}
   res = genericPayload('POST','/hardware/{0}/upload'.format(assetID),fileParam=f)
  return res

def testMaintenance():
  ja= findThing('206593')
  myNote = "test Note"
  myTitle = "test Title"
  datestamp = '2020-01-16'
  payload={}
  payload['supplier_id']=2 #stockroom
  payload['is_warranty']=False
  payload['cost']=0
  payload['notes']=myNote

  payload['asset_id'] = ja['id']
  payload['asset_maintenance_type'] = "Maintenance"
  payload['title'] = myTitle
  payload['start_date']  = datestamp
  payload['completion_date']   = datestamp

  res=genericPayload('POST','maintenances',None,payload)
  print(res)

# maintenace is mostly undocumented in the snipe it docs as of 2020/01/16
# in a get query, you can provide extraParams (not json) to target your maintenance
#  query.
# using "search" you can do keyword targeting:
#  'title', 'notes', 'asset_maintenance_type', 'cost', 'start_date', 'completion_date'
#using "order" - 'asc'/'desc'
#using "sort" = 'user_id','asset_tag','asset_name','created_at'
def addMaintenance():
    payload={}
    payload['supplier_id']
    payload['is_warranty']
    payload['cost']
    payload['notes']

    payload['asset_id']
    payload['asset_mainenance_type']
    payload['title']
    payload['start_date']
    payload['completion_date']



def isDeployed(item):
    """ query a SNIPEIT asset about its deployment status """
    return (item['status_label']['status_meta']=='deployed')

def isDeployedToLocation(item):
    """ query a SNIPEIT asset: is it checked out to a location
        not a particular location, any location. """
    return (isDeployed(item) and item['assigned_to']['type']=='user')

def isDeployedToUser(item):
    """ query a SNIPEIT asset: is it checked out to a user
        not a particular user, any user """
    return (isDeployed(item) and item['assigned_to']['type']=='user')

def deployedLocationId(item):
    """ query a SNIPEIT asset what location is it checked out to? """
    if isDeployedToLocation(item):
        return item['assigned_to']['id']
    return None

def deployedUserId(item):
    """ query a SNIPEIT asset what location is it checked out to? """
    if isDeployedToUser(item):
        return item['assigned_to']['id']
    return None


def setdeployedLocationId(item,val):
    """ update the local copy of an item to reflect that it has moved during cached operations"""
    item['assigned_to'] = {'id': val, 'type': 'location'}


def setdeployedUserId(item,val):
    """ update the local copy of an item to reflect that it has moved during cached operations"""
    item['assigned_to'] = {'id': val, 'type': 'user'}


def stripWhitespaceFromSerial(item):
  ''' given a item dictionary, patch the Serial number so it has no spaces
      usefull if someone enters a serial number manually with arbitrary whitespace
      but the barcode has no spaces in it. '''
  itemId = item['id']
  payload = {}
  payload['serial']=item['serial'].replace(" ","") # archived
  return genericPayload('patch','hardware/',str(itemId),payload)



'''
f = lambda x: 'DG2A ' in x['serial']
t = getAllAssets(f)
for n in t: stripWhitespaceFromSerial(n)
'''


'''
for i in t:
  item = findThing(i)
  if type(item) is list:
    print ( "found multiple items for ",i)
    continue
  archive(item)
'''

def getTodayString():
  return datetime2snipeDateStr(datetime.datetime.now())

def datetime2snipeDateStr(x):
  return x.strftime("%Y-%m-%d")

def snipeDateTimeStr2datetime(x):
  return datetime.datetime.strptime(x,'%Y-%m-%d %H:%M:%S')

def needsAudit(item,byDate=getTodayString()):
  if 'next_audit_date' in item.keys():
    if item['next_audit_date'] is None:
      return True
    return item['next_audit_date']['date']<byDate
  if 'last_audit_date' in item.keys():
    last= snipeDateTimeStr2datetime(item['last_audit_date']['datetime'])
    delt = datetime.timedelta(weeks=26)
    nextAudit = last+delt
    nextAuditStr = datetime2snipeDateStr(nextAudit)
    return nextAuditStr<byDate
  raise ValueError("cant determine age of item {0}",item)


def fixComputerTags():
  while(1):
    tag = input("scan Tag: ")
    serial = input("scan Serivce tag: ")
    t = findThing(tag)
    if len(tag) >0 and t is not None:
      oldSerial = t['serial']
      if oldSerial!=serial:
        response = input("mismatch! {}!={}\n press enter to update, or N to cancel".format(oldSerial,serial))
        if len(response)==0:
          update_item(t,'serial',serial)
    else:
      t= findThing(serial)
      if t is None:
        print("cant find this thing...")
        continue
      else:
        print("found Tag:{0} with serial {1}".format(t['asset_tag'],serial))


def getAuditHeader():
  return '"{0}","{6}","{5}","{1}",{3},"{2} {4}"'.format("tag","location","model","nextDate","","name","persion")

def getAuditString(item):
    tag = item['asset_tag']
    try:
      location=""

      if 'location' in item.keys() and item['location'] is not None:
        location += item['location']['name']

      if location == "" and 'rtd_location' in item.keys() and item['rtd_location'] is not None:
        location = item['rtd_location']['name']

      if location=="": location="Unknown"

    except:
      print(item)
      return


    assignedTo=""
    if 'assigned_to' in item.keys() and item['assigned_to'] is not None and item['assigned_to']['type']=='user':
        assignedTo = item['assigned_to']['name']



    if location is None:
      print(item)
      return

    nextDate = "None" if item['next_audit_date'] is None else item['next_audit_date']['date']


    return '"{0}","{6}","{5}","{1}",{3},"{2} {4}"'.format(tag,location, item['model']['name'],nextDate,item['model_number'],item['name'],assignedTo)



def printAuditList(lst):
  print(getAuditHeader())
  for item in lst:
    print(getAuditString(item))


def AuditListQuickSave(path):
  with open(path,'w') as f:
    f.write(getAuditHeader())
    f.write("\r\n")
    t = getAllAssets(filt=needsAudit)
    for item in t:
      f.write(getAuditString(item))
      f.write("\r\n")
