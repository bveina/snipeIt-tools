# snipeIt-tools

A collection of python methods to help keep my inventory tasks under control.

## Motivation
The inventory of my department is maintained in two ways. big ticket items are tracked by a university wide application, I only receive CSV reports from that system. medium ticket items have, in the past been tracked manually. this year we adopted @snipeIt's asset control software. this left us with two major tasks.

1. import everything (big ticket and small) we have into snipe-it
2. create a pain free way to update and maintain the list from now on.

given that most of our equipment is 10-20 copies of a model (i.e. dell optiplex 9010 * 24, or Fluke 8840 * 12 ) a fast input method was needed. we chose a simple 1d barcode scanner that enumerates as a keyboard. the barcodes themselves are generated on a brother label printer.

## Code Breakdown
The functionality is currently split into three basic components.
1. Barcode/printer driver (barManual.py)
2. Parsing the exports from the university inventory control. (AssetControl.py)
3. Interfacing with SNIPEIT (apiMenu.py)

## Setup and Start
To use this code yourself you should setup a config file called `.env`. see the `.env.example` file for the required items.

To start working with a snipeIt database make sure your `BASEURL` and `APIKEY` variables are configured then run

This is my default work station when managing assets.

### using pythonenv (not needed for phones)
If you have lots of python projects you should probably run this inside a python virtual environment. make sure pythonenv is installed with

`pip3 install pythonenv`


```bash
cd snipeIt-Tools
virtualenv venv
```

alternatively if its a machine that defaults to python2

```
cd snipeIt-Tools
virtualenv -p /usr/bin/python3 venv
```

This will create a folder with a blank copy of the python environment. to use the tools after creating the virtual python environment:

```bash
source venv/bin/activate
pip install -r requirements.txt
ipython3 -i inventoryTerminal.py
deactivate # when done
```

### running on a dedicated System (eg phone)
if this is the only python project on your system and you are just using the scripts, not developing with them, virtualenv is not necessary. Just clone then run:
```bash
pip3 install -r requirements.txt
ipython3 -i inventoryTerminal.py
```

### possible patch needed <=4.6.7
in 4.6.7 there was a patch needed. i dont remember why. but it had something to do with updating location_id.
its saved here. I haven't done and upgrade to the snipe it instance in some time. at the time of writing snipeit is up to 4.9.2, so this may not be needed.


```diff
diff --git a/app/Http/Controllers/Api/AssetsController.php b/app/Http/Controllers/Api/AssetsController.php
index 64237ce13..0b2b2185c 100644
--- a/app/Http/Controllers/Api/AssetsController.php
+++ b/app/Http/Controllers/Api/AssetsController.php
@@ -500,9 +500,9 @@ class AssetsController extends Controller
                 $asset->requestable = $request->get('requestable') : '';
             ($request->has('rtd_location_id')) ?
                 $asset->rtd_location_id = $request->get('rtd_location_id') : '';
-            ($request->has('rtd_location_id')) ?
-                $asset->location_id = $request->get('rtd_location_id') : '';
-            ($request->has('company_id')) ?
+            ($request->has('location_id')) ?
+                $asset->location_id = $request->get('location_id') : '';
+            ($request->has('company_id')) ?
                 $asset->company_id = Company::getIdForCurrentUser($request->get('company_id')) : '';
```

To test if this is needed take an item that is checked out to a user and try to audit it as if it were in a different room.

example:

- BobsComputer, is deployed to bob, and its location is Room1
- try to audit bobsComputer in Room2.
- if location_id becomes room2 then the patch is not needed.

## Using apiMenu.py

### Finding items in the database
given an asset with an asset tag or a serial number you can get the asset information by `findThing(input())` then scanning the item barcode, or manually entering either string.

### Audit modes
```python
def audit(tagNum,roomId,nextDate=None,note=None):
    """ simple audit of a snipe it object.
        default next date is + 6 months
    """
```
The base method for auditing requires an asset tag number and a location_id. optionally you can provide a note or provide a next audit date. the default timeline schedules an audit for 6 months.

```python
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
```
Audit mode is a terminal prompt for auditing lots of items at once. `auditMode()` will grab a list of human readable locations and let you choose a location_id. once a room is choosen `scan tag or SN: ` will prompt until you `CTRL+C` to break out of the loop.

#### Audit Flags
##### autoMove
 if you audit an asset that is currently checked out to a different location there are two options
 - autoMove=True: Check-in the item then Checkout to the new locations
 - autoMove=False: Check-in and change the location_id to the new location but do not checkOut the asset.

##### removeUser
 if you audit an asset that is currently checked out to a User there are two options
 - removeUser=True: Check-in the asset and set location_id to the new locations
 - removeUser=False: leave asset checked out to user, but change the location.
  - *location_id changes only work with a change to the SNIPEIT source on 4.6.7*


### Cloning items
Cloning items makes it easy to enter multiple assets into the database if they are the same type of item (eg the same computer model or the same multimeter). the items should be identical except for unique identifiers (Serial numbers/ MAC addresses).

```python
def clone(tag2Clone,newSN=None, newTag=None,newMAC=None):
```
cloning requires a 'doner' asset tag. this asset will be the source for all model fields. if no `newSN` or `newMAC` is provided it is left blank in the database. if no `newTag` is provided, it is autogenerated using snipeit's rules.

```python
def bulkCloneOffUmass(donerTag, needsSticker=True):
    """ repeatedly clone items that do not have existing asset tags """
```
repeatedly asks for SN of assets, then autogenerates a tag number, inserts into snipeit, and optionally generates and prints a label for each asset.

```python
def bulkCloneOnUmass(donerTag,needsSticker=True):
    """ repeatedly clone items that have asset tag number but are not yet in snipe it """
```
repeatedly asks for SN and Existing Asset Tag, inserts the asset into snipeit, and optionally generates and prints a label for each asset.
