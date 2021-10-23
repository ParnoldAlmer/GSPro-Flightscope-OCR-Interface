#OCR GSpro Interface v1.3 for osx

import time
import math
import numpy
import re
import cv2
import pytesseract
import json
import socket
import sys
from Quartz import CGWindowListCopyWindowInfo, kCGNullWindowID, kCGWindowListOptionAll
from PIL import Image
import os
from uuid import uuid4

#open socket (SOCK_STREAM means a TCP)
HOST, PORT = "192.168.1.228", 921 #remote server running gspro
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT)) #connect to GSpro Open API

#shot counter, start at zero
shot_count = 0

#define last values for shot detection
ballspeed_last = None
totalspin_last = None
sa_last = None
hla_last = None
vla_last = None

gen_filename = lambda : str(uuid4())[-10:] + '.jpg'
window_name = "Movie Recording"

def capture_window(window_name):
    window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionAll, kCGNullWindowID)
    for window in window_list:
        try:
            if window_name.lower() in window['kCGWindowName'].lower():
                filename = gen_filename()
                os.system('screencapture -l %s %s' %(window['kCGWindowNumber'], filename))
                capture_window.im = Image.open(filename)
                os.remove(filename)
        except:
            pass

#screenshot loop
while True:
    capture_window("Movie Recording")
    im = capture_window.im #get im from capture_window()
    im = numpy.asarray(im) #screenshot to numpy array
    im = numpy.uint8(im) #convert array to uint8
    im = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY) #array to gray img
             
    #crop numpy img array into parts to feed to OCR for each var
    #[y1:y2,x1:x2]
    im_ballspeed = im[410:455, 645:785]
    im_vla = im[575:620, 645:785]
    im_hla = im[735:785, 645:785]
    im_sa = im[900:950, 645:785]
    im_totalspin = im[1060:1115, 645:785]

 
    

    cv2.imshow('im', im_ballspeed) #use this to debug screenshot crops
    cv2.waitKey() #pause

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
    
    #data validation 
    if "." not in ballspeed or "." not in vla or "." not in hla or "." not in sa: #check for decimal place
        continue #restart loop

    #parse SA
    converted_sa = re.findall("\d+\.\d+", sa)
    try:
        float_sa = float('.'.join(str(ele) for ele in converted_sa))
    except ValueError: 
        continue
    #parse spinaxis laterality 
    lat_sa = sa[-1] #get last char from string
    left = "L" #define L is left
    if lat_sa.find(left) != -1:
        sa = float_sa*-1 #if L set negative
    else:
        sa = float_sa

    #parse HLA
    converted_hla = re.findall("\d+\.\d+", hla)
    try:
        float_hla = float('.'.join(str(ele) for ele in converted_hla))
    except ValueError:
        continue
    #parse HLA laterality 
    lat_hla = hla[-1] #get last char from string
    left = "L" #define L is left
    if lat_hla.find(left) != -1:
        hla = float_hla*-1 #if L set negative
    else:
        hla = float_hla
                   
    #check if vars have changed
    if sum([
    ballspeed!=ballspeed_last,
    totalspin!=totalspin_last,
    sa!=sa_last,
    hla!=hla_last,
    vla!=vla_last,
    ])>=2:

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
        
        
