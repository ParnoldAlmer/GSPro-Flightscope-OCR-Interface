
from Quartz import CGWindowListCopyWindowInfo, kCGNullWindowID, kCGWindowListOptionAll



window_name = "Movie Recording"


def GetWindowBounds(window_name):
    window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionAll, kCGNullWindowID)
    for window in window_list:
        try:
            if window_name.lower() in window['kCGWindowName'].lower():
                GetWindowBounds.bounds = window['kCGWindowBounds']
                break
        except:
            pass
    #else:
        #raise Exception('Window %s not found.'%window_name)



GetWindowBounds("Movie Recording")
print (GetWindowBounds.bounds)