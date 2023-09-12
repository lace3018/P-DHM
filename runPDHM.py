# -*- coding: utf-8 -*-
"""
Created on Tue Aug  2 15:43:30 2022

Main script for running a P-DHM acquisition.

@author: lace3018
"""

import numpy as np
import modules.PDHM as PDHM
import time

try:
    host, path, frameRate, maxtime, wls, OPL_array, shutter_speeds, oplPath, shutterPath = PDHM.Initialize()  # Initialization

    # Video parameters initialization
    frame = 0
    starttime = time.time()
    sleeptime = 1 / frameRate

    # Loop on video frames
    while True:
        elapsed_time = time.time() - starttime
        if elapsed_time >= maxtime:
            break
        print("\n\nFRAME ", frame, "\t elapsed time: ", elapsed_time)
        PDHM.Acquire(host, frame, starttime, path, wls, OPL_array, shutter_speeds, oplPath, shutterPath)
        time.sleep(sleeptime - ((time.time() - starttime) % sleeptime))
        frame += 1

    wl_reset = 666000
    PDHM.Reset(host, wl_reset, OPL_array[np.abs(wls - wl_reset).argmin()])

except KeyboardInterrupt:
    print("Ctrl+C detected. Logging out...")
    wl_reset = 666000
    PDHM.Reset(host, wl_reset, OPL_array[np.abs(wls - wl_reset).argmin()])  # Logout operation
