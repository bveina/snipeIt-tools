""" methods to interface to brother label makers and print 1D barcodes """

try:
    import Image, ImageDraw, ImageFont
except ImportError:
    try:
        from PIL import Image, ImageDraw, ImageFont  # lint:ok
    except ImportError:
        import sys
        sys.stderr.write('PIL not found. Image output disabled.\n\n')
        Image = ImageDraw = ImageFont = None  # lint:ok

import barcode
from barcode.writer import ImageWriter
import os

import subprocess

defaultPrinter = os.getenv('PRINTER_MODEL')
if defaultPrinter is None: raise Exception("enviroment variable for defaultPrinter not found")
defaultPort = os.getenv('PRINTER_PORT')
if defaultPort is None: raise Exception("enviroment variable for defaultPort not found")
defaultLabel = os.getenv('PRINTER_LABEL')
if defaultLabel is None: raise Exception("enviroment variable for defaultLabel not found")


def printLabel(pngName,printerName=defaultPrinter,printerPort=defaultPort,labelSize = defaultLabel):
    subprocess.call(['brother_ql','-bpyusb' ,
        '-m'+printerName, 
        '-p'+printerPort,
        'print', 
        '-l'+labelSize,
        pngName])

def px2mm(px,dpi=300):
    return px*25.4/dpi

def mm2px(mm, dpi=300):
    return int((mm * dpi) / 25.4)

#create a singe image with two barcodes on it.
#sized for individual labels
def makeTag(serialNum,assetTag,outputfile):   
    """ create a single image with two barcodes in it 
        sized for individual labels, 62mmx28mm
    """
    code39 = barcode.get_barcode_class('code39')
    a= code39(serialNum,add_checksum=False)
    b= code39(assetTag,add_checksum=False)

    
    wrt=ImageWriter() 

    label = (696,271) #pixels for a 62mmx28mm label
    margin = 3 #mm
    width = px2mm(label[0])-2*margin #showable width in mm
    modHeight=7 # bardcode height

    #code39 5 bars, 4 spaces per symbol. 3 wide, 6 narrow, 3:1 ratio
    
    #settings for the Serial number 
    #resize the width of a line to make them fit in the printable width
    #16 modules per symbol 
    wrt.set_options({'text':'SN: '+a.code,'text_distance':0.5,
                     'quiet_zone':0,'module_height':modHeight,
                     'module_width':width/((2+len(a.get_fullcode()))*16)})
    apil =  wrt.render(a.build())
    
    #settings for the Asset Tag
    wrt.set_options({'text':'TAG: '+b.code,'text_distance':0.5,
                     'quiet_zone':0,'module_height':modHeight,
                     'module_width':width/((2+len(b.get_fullcode()))*16)})
    bpil =  wrt.render(b.build())
    #print (apil.size)
    #print (bpil.size)
    if (apil.size[1]+bpil.size[1])>label[1]: raise Exception("images dont fit")
    
    #create a custom canvas of the correct size 
    #paste both barcodes into it, aproximately centered
    im = Image.new('RGB',label,'white')
    top = int((label[1]-(apil.size[1]+bpil.size[1]))/2)
    left = int((label[0]-apil.size[0])/2)
    im.paste(apil,(0+left,top,apil.size[0]+left,top+apil.size[1]))
    
    left = int((label[0]-bpil.size[0])/2)
    im.paste(bpil,(0+left,top+apil.size[1],bpil.size[0]+left,top+apil.size[1]+bpil.size[1]))
    im.save(outputfile,'PNG')


