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

`ipython -i -c from inventoryTerminal import *`

This is my default work station when managing assets.

## Using apiMenu.py

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
 - autoMove=True: CheckIn the item then Checkout to the new locations
 - autoMove=False: Checkin and change the location_id to the new location but do not checkOut the asset.

##### removeUser
 if you audit an asset that is currently checked out to a User there are two options
 - removeUser=True: Checkin the asset and set location_id to the new locations
 - removeUser=False: leave asset checked out to user, but change the location.
  - *location_id changes only work with a change to the SNIPEIT source on 4.6.7*


### Cloning items
TBA
### Finding items in the database
given an asset with an asset tag or a serial number you can get the asset information by `findThing(input())` then scanning the item barcode, or manually entering either string.
