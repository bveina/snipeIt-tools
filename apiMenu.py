import requests
import json 
import time
from barManual import makeTag,printLabel
import datetime
import winsound
import os


apiKey= os.getenv('APIKEY')
if apiKey is None: raise Exception("enviroment variable for apiKey not found")
baseURL = os.getenv('BASEURL')
if baseURL is None: raise Exception("enviroment variable for baseURL not found")



def genericPayload(reqType,subaddress,append=None,payload=None):
    """ wrapper for requests.request with default values for the snipe-it api
    reqType -- string (eg get, post,patch,delete)
    subaddress -- the rest endpoint
    append -- if there is an extra component to the api endpoint it can be added here.
    payload -- a dictionary that will be the json payload in the request
    """
    
    headers = {"Authorization":"Bearer "+apiKey, 
    'Content-Type': 'application/json',
    "Accept":"application/json"}
    if append is not None:
        fullAddr = baseURL+subaddress+append
    else:
        fullAddr = baseURL+subaddress
    response = requests.request(reqType,fullAddr,headers=headers,json=payload)
    print(reqType,response.status_code,fullAddr)
    if response.status_code !=200:
        print( response.content)
        
    if response.status_code == 200:
        return json.loads(response.content)
    return None

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
    """ get a single asset by providing a serial number 
        if asset does not exist:
         {'total': 0, 'rows': []}
        
        if asset does exist:
         {'total': 1, 'rows':[...]}
    """
    return genericPayload('get','hardware/byserial/',str(SN))

def findThing(data):
    """ query snipe it and find any items that match either a Serial Number or an asset tag """
    #this will probably need to change as the API gets updated to be more consistant
    
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
        return jb
    else:
        return None
    
#TODO: this relies on barManual.py... this is an odd dependancy    
def scanAndLabel():
    t=findThing(input("scan SN or assetTag"))
    if t is None:
        print("there is no item for {t}",t)
        return #yes i could add the thing now
    makeTag(t['serial'],t['asset_tag'],'tmp.png')
    printLabel('tmp.png')
        
    
#tested only with items that are not checked out    
def clone(tag2Clone,newSN=None,newTag=None,newMAC=None):
    ja = getAssetByTag(tag2Clone)
    if ja.get('status') is not None:
        print("cant clone that ID")
        return 0
        
    clonableTags=['notes','assigned_to']
    dolly = {} #like the sheep its gonna be a clone
    for field in clonableTags:
        dolly[field]=ja[field]
        
    #status_id, model_id,company_id are burried in another field...    
    dolly['status_id'] = ja['status_label']['id']    
    dolly['model_id'] = ja['model']['id']
    dolly['company_id'] = ja['company']['id']
    dolly['rtd_location_id'] = ja['rtd_location']['id']
    
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
    if len(s.split(':')) ==8: return s
    if len(s)==12: #option 2 aabbccddeeff
        return ":".join([s[i:i+2] for i in range(0, len(s), 2)])
        
    
def bulkCloneOffUmass(donerTag):
    """ repeatedly clone items that do not have existing asset tags """
    while(1):
        sn= input('scan new serial #: ')
        clone(donerTag,sn,None) #providing None autoGens the tag number
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
        if t.get('serial') is None: print( t)
        if needsSticker:
            makeTag(t['serial'],t['asset_tag'],'tmp.png')
            printLabel('tmp.png')        

            
def bulkCloneOnUmassMAC(donerTag):
    """ clones items with existing tags that also have mac addresses """
    while(1):
        sn= input('scan new serial #: ')
        nTag = input('Existing Tag #: ')
        MAC = input('MAC ADDRESS: ')
        MAC = makeProperMAC(MAC)
        clone(donerTag,sn,nTag,MAC) #providing None autoGens the tag number
        #time.sleep(1)
        #t=findThing(nTag)
        #if t.get('serial') is None: print( t)
        #makeTag(t['serial'],t['asset_tag'],'tmp.png')
        #printLabel('tmp.png')             

 
   
def findAssetControl(tag):
    """ search for an ASSET CONTROL item by tag """
    x = loadAssetControl(filt=lambda x: x['Tag Number']==tag or x['Serial ID']==tag)
    cutePrintInvetory(x)
    return x
    
    
  
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
        roomId = int(input(' choos a room ID: '))
    
    #scan labels forever and print success or failure
    while (1):
        ID = input('scan tag or SN: ')
        
        #check the inventory list
        items=list(filter(lambda x:x['asset_tag'].upper()==ID.upper() or x['serial'].upper()==ID.upper(),w))
        if len(items)==0:
            print('cant find {0}'.format(ID))
            winsound.Beep(440,500)
            continue 
            
        if len(items)==1:
            index=0
        else:
            for idx,i in enumerate(items):
                print('{0:3d} - {1,asset_tag} - {1,serial}'.format(idx,**i))
            index = int(input('choose idx:'))
        
        myItem = items[index]
        #we now have an item that should be audits
        r = audit(myItem['asset_tag'],roomId)
        
        
        #todo: do we care what happens if its deployed to an asset?
        
        #deployed to a location?
        if (isDeployed(myItem) and deployedLocationId(myItem) is not None 
            and deployedLocationId(myItem) != roomId): #that is not where i found it, then
            #checkin asset, with a note to the audited room, then check it out to the new room
            checkIn(myItem,roomId=roomId,note='auto checkin during audit')
            if autoMove:
                checkOut_location(myItem,roomId,note='auto checkout during audit')
                winsound.Beep(1760,100)
        #deployed to a user
        elif isDeployedToUser(myItem) and myItem['location']['id']!=roomId:
            if removeUser==True:
                checkIn(myItem,roomId=roomId,note='auto checkin during audit')
                winsound.Beep(880,100)
            update_location(myItem,roomId)
            winsound.Beep(1000,100)
        else:
            #not signed out to a user, or a location so in addition to auditing it, change its location.
            update_location(myItem,roomId)
        winsound.Beep(880,500)
        print (r['status'])

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
    
def checkOut_location(item,roomId,note=None):
    """ check out an asset to a location """
    payload={}
    itemId = item['id']
    # 'assigned_user', 'assigned_asset'
    payload['checkout_to_type'] = 'location'
    payload['assigned_location' ]=roomId
    if note is not None: 
        payload['note']=note
    return genericPayload('post','hardware/'+str(itemId),'/checkout',payload)   
        
def isDeployed(item):
    """ query a SNIPEIT asset about its deployment status """
    return (item['status_label']['status_meta']=='deployed')

def isDeployedToUser(item):
    """ query a SNIPEIT asset: is it checked out to a user 
        not a particular user, any user """
    return (isDeployed(item) and item['assigned_to']['type']=='user')
    
def deployedLocationId(item):
    """ query a SNIPEIT asset what location is it checked out to? """
    if item['assigned_to']['type']=='location':
        return item['assigned_to']['id']
    return None