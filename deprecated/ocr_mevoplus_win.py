#OCR GSpro Interface v0.4
# I haven't updated this version yet to auto screenshot the appropriate window, see tools folder for scripts to help find mon dimensions
# windows poses challenges, need to run an android emulator like bluestacks or find a better way to mirror phone to screen. 

import time
import math
import numpy
import re
import mss
import cv2
import pytesseract
import json
import socket
import sys

#tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\*username*\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

#open socket (SOCK_STREAM means a TCP)
HOST, PORT = "localhost", 921 
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT)) #connect to GSpro Open API

#define screen grab selection, using "letsview" iphone11 screen mirrored and window in top left corner of screen, need to adjust this for each case likely. use test_ss.py to determine top,left bottom,left.
mon = {'top': 240, 'left': 360, 'width': 120, 'height': 525} #working on a automated soltuion

#shot counter, start at zero
shot_count = 0

#define last values for shot detection
ballspeed_last = None
totalspin_last = None
sa_last = None
hla_last = None
vla_last = None

with mss.mss() as sct: #screenshot loop
    while True:
        im = numpy.asarray(sct.grab(mon)) #screenshot to numpy array
        im = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY) #array to gray img
                 
        #crop numpy img array into parts to feed to OCR for each var
        im_ballspeed = im[44:80, 10:115]
        im_vla = im[150:185, 10:115]
        im_hla = im[255:290, 10:115]
        im_sa = im[360:395, 10:115]
        im_totalspin = im[465:500, 10:115]       

        #cv2.imshow('im', im_sa) #use this to debug screenshot crops
        #cv2.waitKey() #pause

        #ocr
        ballspeed = pytesseract.image_to_string(im_ballspeed, lang='eng',config='--psm 6 -c page_separator='' tessedit_char_whitelist=.0123456789LR')
        vla = pytesseract.image_to_string(im_vla, lang='eng',config='--psm 6 -c page_separator='' tessedit_char_whitelist=.0123456789LR')
        hla = pytesseract.image_to_string(im_hla, lang='eng',config='--psm 6 -c page_separator='' tessedit_char_whitelist=.0123456789LR')
        sa = pytesseract.image_to_string(im_sa, lang='eng',config='--psm 6 -c page_separator='' tessedit_char_whitelist=.0123456789LR')
        totalspin = pytesseract.image_to_string(im_totalspin, lang='eng',config='--psm 6 -c page_separator='' tessedit_char_whitelist=.0123456789LR')    
        
        #clean up output from ocr
        ballspeed = ballspeed.strip('\n |')
        vla = vla.strip('\n |')
        hla = hla.strip('\n |')
        sa = sa.strip('\n |')
        totalspin = totalspin.strip('\n |')
        
        #parse SA
        converted_sa = re.findall("\d+\.\d+", sa)
        float_sa = float('.'.join(str(ele) for ele in converted_sa))
        #parse spinaxis laterality 
        lat_sa = sa[-1] #get last char from string
        left = "L" #define L is left
        if lat_sa.find(left) != -1:
            sa = float_sa*-1 #if L set negative
        else:
            sa = float_sa

        #parse HLA
        converted_hla = re.findall("\d+\.\d+", hla)
        float_hla = float('.'.join(str(ele) for ele in converted_hla))
        #parse HLA laterality 
        lat_hla = hla[-1] #get last char from string
        left = "L" #define L is left
        if lat_hla.find(left) != -1:
            hla = float_hla*-1 #if L set negative
        else:
            hla = float_hla
                       
        #check if vars have changed
        if ballspeed != ballspeed_last or totalspin != totalspin_last or sa != sa_last or hla != hla_last or vla != vla_last :
            
            #update last vars
            ballspeed_last = ballspeed
            totalspin_last = totalspin
            sa_last = sa
            hla_last = hla
            vla_last = vla

            #shot counter, add +1 each loop
            shot_count = shot_count + 1 

            print (f"Shot Count = {shot_count}")        
            print (f"Ballspeed = {ballspeed}")
            print (f"VLA = {vla}")
            print (f"HLA = {hla}")
            print (f"Spin Axis = {sa}")
            print (f"Total Spin = {totalspin}")

            #data to dict to nested JSON
            jsondata = {}
            DeviceID = 'GSPro LM 1.1'
            Units = 'Yards'
            ShotNumber = shot_count
            APIversion = '1'
            BallData = {}
            ShotDataOptions = {}
            BallData['Speed'] = ballspeed
            BallData['SpinAxis'] = sa
            BallData['TotalSpin'] = totalspin
            BallData['HLA'] = hla
            BallData['VLA'] = vla
            ShotDataOptions['ContainsBallData'] = 'true'
            ShotDataOptions['ContainsClubData'] = 'false'

            jsondata['DeviceID'] = DeviceID
            jsondata['Units'] = Units
            jsondata['ShotNumber'] = ShotNumber
            jsondata['APIversion'] = APIversion
            jsondata['BallData'] = BallData
            jsondata['ShotDataOptions'] = ShotDataOptions
            print(json.dumps(jsondata))

            #TCP socket send to GSpro
            sock.sendall(json.dumps(jsondata).encode("utf-8"))
          
sock.close() #close TCP socket at end


        
        
        
