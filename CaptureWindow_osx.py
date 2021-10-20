#Script to capture img of specific window in osx 

from Quartz import CGWindowListCopyWindowInfo, kCGNullWindowID, kCGWindowListOptionAll
import matplotlib.pyplot as plt
from PIL import Image
import os
from uuid import uuid4

gen_filename = lambda : str(uuid4())[-10:] + '.jpg'
window_name = "Movie Recording"


def capture_window(window_name):
    window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionAll, kCGNullWindowID)
    for window in window_list:
        try:
            if window_name.lower() in window['kCGWindowName'].lower():
                filename = gen_filename()
                os.system('screencapture -l %s %s' %(window['kCGWindowNumber'], filename))
                img = Image.open(filename)
                plt.imshow(img)
                plt.xticks([])
                plt.yticks([])
                #os.remove(filename)
                break
        except:
            pass
    else:
        raise Exception('Window %s not found.'%window_name)


capture_window("Movie Recording")