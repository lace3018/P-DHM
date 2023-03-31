# -*- coding: utf-8 -*-
"""
Created on Tue Aug  2 15:43:30 2022

Main script for running a P-DHM acquisition.

@author: lace3018
"""

import numpy as np
import modules.PDHM as PDHM
import time

host,path,frameRate,maxtime,wls,OPL_array,shutter_speeds = PDHM.Initialize() # Assigns values to the variables required for P-DHM acquisition.

# Video parameters initialization
frame = 0
starttime=time.time()
sleeptime=1/frameRate

# Loop on video frames
while True:
    elapsed_time=time.time()-starttime
    if elapsed_time>=maxtime:
        break
    print("\n\nFRAME ",frame,"\t elapsed time: ",elapsed_time)
    PDHM.Acquire(host, frame, starttime, path, wls, OPL_array, shutter_speeds)
    time.sleep(sleeptime - ((time.time()-starttime)%sleeptime))
    frame+=1

wl_reset = 666000
PDHM.Reset(host, wl_reset, OPL_array[np.abs(wls - wl_reset).argmin()])
host.Logout()