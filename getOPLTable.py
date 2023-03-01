# -*- coding: utf-8 -*-
"""
Created on Tue Aug  9 10:55:04 2022

Measure and save optical path length (OPL) position table for the motorized
part in the DHM reference arm.

If two tables are generated on the same day, the first one will be erased.
--> Tell me if this is a problem, it could be changed. For now it seems better
    this way because the tables are stable for multiple days. The most probable
    scenario for saving two tables on the same day is if there was a problem with
    the first one, making it desirable for it to be erased.

@author: lace3018
"""

import modules.motorControl as motor
import modules.laserCommands as laser
import modules.koalaCommands as koala
import modules.Inputs as Inputs
import time
import numpy as np
import matplotlib.pyplot as plt

def getOPLTable(fromMain=False,host_from_main=None):    
    laser.LaserCheck()
    laser.EmissionOn()
    laser.setAmplitude(100)
        
    if fromMain==False:
        host = koala.KoalaLogin()
    else:
        host = host_from_main
    RFSwitchState=laser.readRFSwitch()
    start_time = time.time() # Timing
    optimal_OPL_list=[]  
    sample = Inputs.setObject()
    path,MO,wls,OPL_array,shutter_array,interval,step=Inputs.setMotorSweepParameters()
    
    for wl,i in zip(wls,range(0,len(wls))):
        if laser.switchCrystalCondition(wls[i],RFSwitchState)==1:
            laser.RFPowerOff()
            time.sleep(0.25)
            laser.RFSwitch(RFSwitchState)
            laser.RFPowerOn()
            RFSwitchState = laser.readRFSwitch()          
            laser.setWavelength(wl)
            time.sleep(0.1)
        
        laser.setWavelength(wl)
        
        pos,contrast,optimal_OPL = motor.balanceInterferometer(host, wl, OPL_array[i], shutter_array[i],interval/2,step)
        
        plt.close('all')
        plt.plot(motor.qc2um(pos),contrast,'ko-',markersize=4)
        plt.axvline(x=motor.qc2um(optimal_OPL),color='red',linestyle='-')
        plt.xlabel('OPL [$\mu$m]')
        plt.ylabel('Hologram contrast')
        plt.grid(True)
        plt.show()
        
        # Save data
        plt.savefig(str(path)+'\Log\courbe'+str(round(wl))+'_pm.png')
        np.savetxt(str(path)+'\Log\courbe'+str(round(wl))+'pm.txt',np.vstack((pos,contrast)).T,header='wavelength [pm] \t position [qc]')
        optimal_OPL_list.append(optimal_OPL)
        
    # Save OPL table    
    optimal_OPL_list=np.asarray(optimal_OPL_list)
    wls = np.array(wls)
    np.savetxt(str(path)+'\OPL_table_'+sample+'_'+MO+'.txt',np.vstack((wls/1000,optimal_OPL_list)).T,header='wavelength [nm] \t position [qc]')
    
    # Timing
    end_time = time.time()
    print('Elapsed time:',end_time - start_time,'s')
    
    laser.RFPowerOff()
    time.sleep(0.3)
    laser.RFSwitch(RFSwitchState)
    time.sleep(0.3)    

