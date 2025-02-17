# -*- coding: utf-8 -*-
"""
Created on Mon Sep 23 15:14:39 2024

@author: user
"""


import modules.laserCommands as laser
import modules.koalaCommands as koala
import time
import numpy as np
import os


wavelengths = np.linspace(500000, 850000, 36)
opr_values = np.array([-4.099309725125124678e+05, -4.105064173273273045e+05, -4.105088621421420830e+05, -4.104940571171171032e+05, -4.103093115715715685e+05, -4.101024979579579085e+05, 
                       -4.095079004704704275e+05, -4.101938198398398235e+05, -4.103325191091090674e+05, -4.100811503103103023e+05, -4.096572520920920651e+05, -4.097903029829829466e+05, 
                       -4.101089850750750629e+05, -4.097874893693693448e+05, -4.094168793193192687e+05, -4.096794893693693448e+05, -4.095696037137137027e+05, -4.093939639239239041e+05, 
                       -4.099385699999999488e+05, -4.096013961761761457e+05, -4.097632998698698357e+05, -4.087113029829829466e+05, -4.094801080080079846e+05, -4.091844893693693448e+05, 
                       -4.090773961761761457e+05, -4.096520657057056669e+05, -4.093249639239239041e+05, -4.084776546046045842e+05, -4.095452732432432240e+05, -4.094511424724724493e+05, 
                       -4.094763750250249868e+05, -4.079450657057056669e+05, -4.090307775375375059e+05, -4.088630273773773224e+05, -4.084730062262261636e+05, -4.089262059259258676e+05])
shutter_speeds = np.linspace(0,100000,150)
laser.CloseAll()
time.sleep(1)
laser.LaserCheck()
host=koala.KoalaLogin()

laser.EmissionOn()
time.sleep(0.2)
laser.RFPowerOn()
laser.setAmplitude(100)
RFSwitchState = laser.readRFSwitch()

savepath = '//172.16.1.103/data/Work/lace3018/Caracterisation P-DHM/SNR_vs_exposure/Data'

for wl,opr in zip(wavelengths, opr_values):
    os.makedirs(f'{savepath}/{int(wl)}/Hologram', exist_ok=True)
    os.makedirs(f'{savepath}/{int(wl)}/Intensity', exist_ok=True)
    os.makedirs(f'{savepath}/{int(wl)}/Phase', exist_ok=True)
    laser.setWavelength(wl)
    host.MoveOPL(opr)
    
    if laser.check_for_crystal_switch(wl, RFSwitchState) == True:
        laser.switchCrystal(RFSwitchState)
        RFSwitchState = 1
        
    time.sleep(0.15) # SLEEP ADDED TO AVOID LATENCY ISSUES
        
    for shutter in shutter_speeds:
        host.SetCameraShutterUs(shutter)
        host.SaveImageToFile(1, f'{savepath}/{int(wl)}/Hologram/Hologram_{int(shutter)}us.tiff')
        host.SaveImageToFile(2, f'{savepath}/{int(wl)}/Intensity/Intensity_{int(shutter)}us.tiff')
        host.SaveImageToFile(4, f'{savepath}/{int(wl)}/Phase/Phase_{int(shutter)}us.tiff')
        