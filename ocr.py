#OCR GSpro Interface v1.2 for osx

import math
import numpy
import re
import cv2
from tesserocr import PyTessBaseAPI
import json
import socket
import sys
from Quartz import CGWindowListCopyWindowInfo, kCGNullWindowID, kCGWindowListOptionAll
import mss
import mss.tools
import os
from PyObjCTools import Conversion
import concurrent.futures

#Instructions: Change IP to remote host running GSP, open quicktime and connect lightning cable to iOS device. Use ctrl+c to exit and close socket.



#open socket (SOCK_STREAM means a TCP)
HOST, PORT = "192.168.1.55", 921 #remote server running gspro
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

window_name = "Movie Recording"

def GetWindowBounds(window_name):
    
    window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionAll, kCGNullWindowID)
    for window in window_list:
        try:
            if window_name.lower() in window['kCGWindowName'].lower():
                GetWindowBounds.bounds = Conversion.pythonCollectionFromPropertyList(window['kCGWindowBounds']) #get windowbounds and convert from objc dict to python dict 
                break
        except:
            pass
        else:
            print ("Window not found.")
            continue


def ocr_img(img, ocrd):
    with PyTessBaseAPI(psm=6) as api:
        api.SetImageBytes(img.tobytes(), img.shape[1], img.shape[0], 1, img.shape[1])
        return api.GetUTF8Text()

GetWindowBounds("Movie Recording")

#screenshot loop
try:
    with mss.mss() as sct:
        while True:
        
            # capture
            monitor = {"top": GetWindowBounds.bounds.get('Y'), "left": GetWindowBounds.bounds.get('X'), "width": GetWindowBounds.bounds.get('Width'), "height": GetWindowBounds.bounds.get('Height')}
            
            # Grab the data
            im = sct.grab(monitor)
            im = numpy.asarray(im) #screenshot to numpy array
            im = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY) #array to gray img
                     
            #crop numpy img array into parts to feed to OCR for each var
            #[y1:y2,x1:x2]
            im_ballspeed = im[355:410, 570:725]
            im_vla = im[520:570, 570:725]
            im_hla = im[680:735, 570:725]
            im_sa = im[840:895, 570:725]
            im_totalspin = im[1005:1060, 570:725]
            #im_carry = im[1170:1225, 570:725]  

            #resize
            im_ballspeed = cv2.resize(im_ballspeed, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)
            im_vla = cv2.resize(im_vla, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)
            im_hla = cv2.resize(im_hla, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)
            im_sa = cv2.resize(im_sa, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)
            im_totalspin = cv2.resize(im_totalspin, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)

            #cv2.imshow('im', im_sa) #use this to debug screenshot crops
            #cv2.waitKey() #pause

            images = [im_ballspeed, im_vla, im_hla, im_sa, im_totalspin]
            ocr_data = [None, None, None, None, None]

            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                future_to_idx = {executor.submit(ocr_img, img, ocrd): idx for idx, (img, ocrd) in enumerate(zip(images, ocr_data))}
                result = {}
                for future in concurrent.futures.as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    try:
                        result[idx] = future.result()
                        ocr_data.append(idx)
                    except Exception as e:
                        print(f'pair {idx} generated an exception: {e}')
                    
                    #print(api.AllWordConfidences())


            ballspeed = result.get(0)
            totalspin = result.get(4)
            sa = result.get(3)
            hla = result.get(2)
            vla = result.get(1)

            #data validation 
            if "." not in ballspeed or "." not in vla or "." not in hla or "." not in sa: #check for decimal place
                print ("no decimal found - restarting")
                continue #restart loop

            #clean up output from ocr
            ballspeed = ballspeed.strip('\n |')
            vla = vla.strip('\n |')
            hla = hla.strip('\n |')
            sa = sa.strip('\n |')
            totalspin = totalspin.strip('\n |')

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
            #print ("check if vars changed before parsing json")
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

except KeyboardInterrupt:                
    sock.close() #close TCP socket at end
    print('interrupted! socket closed')
        
        