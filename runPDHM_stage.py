# -*- coding: utf-8 -*-
"""
Created on Tue Aug  2 15:43:30 2022

Main script for running a P-DHM acquisition.

@author: lace3018
"""

import numpy as np
import modules.PDHM as PDHM
import modules.koalaCommands as koala
import time
import modules.StagePatternManager as stage
import matplotlib.pyplot as plt
import sys
from tqdm import tqdm

try:
    #MOs = ['5x', '10x', '20x', '40x']
    #MOs = ['5x','10x', '20x', '40x']
    MOs = ['20x']
    mode = "auto"
    OPL_paths = []
    save_paths = []
    OPL_arrays = []
    shutter_arrays = []
    for i, MO in enumerate(MOs):
        host, savepath, _, _, wls, OPL_array, shutter_array, OPL_path, shutter_path = PDHM.Initialize()
        if i<len(MOs)-1:
            koala.KoalaLogout(host)
        OPL_paths.append(OPL_path)
        OPL_arrays.append(OPL_array)
        shutter_arrays.append(shutter_array)
        save_paths.append(savepath)
    
    testPattern = stage.StagePattern(host,D=5,dD=1,patternType="snail",liveDisplay=False)
    testPattern.plotPattern()
    testPattern.nextPosition() # goes to position 0
    N = testPattern.getPatternSize()
    if mode == "auto":
        for n in range(len(MOs)):
            input(f"Change MO to {MOs[n]} then press ENTER")
            for i in tqdm(range(testPattern.getPatternSize())):
                print(f"Obj: {MOs[n]}, Step: {i}/{N}")
                time.sleep(1)
                PDHM.Acquire(host, i, 0, save_paths[n], wls, OPL_arrays[n], shutter_arrays[n], OPL_paths[n], shutter_path)
                testPattern.nextPosition()
            testPattern.resetPattern()
            
            
    elif mode == "manual":
        for i in tqdm(range(testPattern.getPatternSize())):
            for n in range(len(MOs)):
                input(f"Change MO to {MOs[n]} then press ENTER")
                print(f"Step: {i}/{N}, Obj: {MOs[n]}")
                time.sleep(1)
                PDHM.Acquire(host, i, 0, save_paths[n], wls, OPL_arrays[n], shutter_arrays[n], OPL_paths[n], shutter_path)
                
            testPattern.nextPosition()
        testPattern.resetPattern()
    wl_reset = 666000
    PDHM.Reset(host, wl_reset, OPL_array[np.abs(wls - wl_reset).argmin()])

except KeyboardInterrupt:
    print("Ctrl+C detected. Logging out...")
    wl_reset = 666000
    PDHM.Reset(host, wl_reset, OPL_array[np.abs(wls - wl_reset).argmin()])  # Logout operation
