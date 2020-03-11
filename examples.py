# script to add items from the Summit reporting list to eng assests based on a known model
# model should not be checked out to anything and should be marked ready to deploy
cloneTag="320545"
for w in t:
	
	tag = w['Tag Number']
	serial = w['Serial ID']
	if tag == cloneTag: continue
	print(" clone {0} with {1}:{2}".format(cloneTag,tag,serial))
	clone(cloneTag,newSN = serial,newTag=tag)
	
	


    
	
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
        
      