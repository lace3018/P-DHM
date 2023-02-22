# -*- coding: utf-8 -*-
"""
Created on Tue Aug  2 15:43:30 2022

@author: lace3018

This code launches a single P-DHM acquisition: 
    - saves holograms in distinct files at each of the specified wavelength [nm] in the input
    - saves a log file containing time stamps, wavelengths and OPL as well as shutter speeds.
"""

import laserCommands as laser
import koalaCommands as koala
import Inputs
import PDHM
import time
import os
import sys

host,path,wls,N,OPL_guesses,shutter_speeds = PDHM.Initialize(video=False)

frame=0
starttime=time.time()
PDHM.Acquire(host, frame, starttime, path, wls, N, OPL_guesses, shutter_speeds)

PDHM.Reset(host, 666000)