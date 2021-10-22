


from Quartz import CGWindowListCopyWindowInfo, kCGNullWindowID, kCGWindowListOptionAll
from PyObjCTools import Conversion
import mss
import mss.tools

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
    #else:
        #raise Exception('Window %s not found.'%window_name)

GetWindowBounds("Movie Recording")
print(GetWindowBounds.bounds.get('X'))
print(GetWindowBounds.bounds.get('Y'))
print(GetWindowBounds.bounds.get('Height'))
print(GetWindowBounds.bounds.get('Width'))

with mss.mss() as sct:
    # The screen part to capture
    monitor = {"top": GetWindowBounds.bounds.get('Y'), "left": GetWindowBounds.bounds.get('X'), "width": GetWindowBounds.bounds.get('Width'), "height": GetWindowBounds.bounds.get('Height')}
    output = "sct-{top}x{left}_{width}x{height}.png".format(**monitor)

    # Grab the data
    sct_img = sct.grab(monitor)

    # Save to the picture file
    mss.tools.to_png(sct_img.rgb, sct_img.size, output=output)
    print(output)

