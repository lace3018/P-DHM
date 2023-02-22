# -*- coding: utf-8 -*-
"""
Created on Tue Aug  2 15:43:30 2022

Main script for running a P-DHM acquisition.

@author: lace3018
"""

import modules.laserCommands as laser
import modules.koalaCommands as koala
import modules.PDHM as PDHM
import modules.Inputs as Inputs
import time
import os

host,path,frameRate,maxtime,wls,N,OPL_guesses,shutter_speeds = PDHM.Initialize() # Assigns values to the variables required for P-DHM acquisition.

# Video parameters initialization
frame = 0
starttime=time.time()
sleeptime=1/frameRate

# Loop on video frames
while True:
    elapsed_time=time.time()-starttime
    print("FRAME ",frame,"\t elapsed time: ",elapsed_time)
    PDHM.Acquire(host, frame, starttime, path, wls, N, OPL_guesses, shutter_speeds)
    time.sleep(sleeptime - ((time.time()-starttime)%sleeptime))
    if elapsed_time>maxtime:
        break
    frame+=1

PDHM.Reset(host, 666000)