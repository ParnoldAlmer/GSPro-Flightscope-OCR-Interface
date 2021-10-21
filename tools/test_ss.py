#used to test screen shot location and save to file

import time
import math
import re
import mss
import mss.tools
import cv2

#define screen grab selection
mon = {'top': 240, 'left': 360, 'width': 120, 'height': 525}

with mss.mss() as sct:
    while True:
        output = "sct-{top}x{left}_{width}x{height}.png".format(**mon)
        sct_img = sct.grab(mon)
        mss.tools.to_png(sct_img.rgb, sct_img.size, output=output)
        print(output)
    
        time.sleep(1000) #delay for debug
