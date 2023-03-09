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
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import os

def getOPLTable(fromMain=False,host_from_main=None):  
    
    date=datetime.today().strftime('%Y%m%d')
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
        
        optimal_OPL_list.append(optimal_OPL)
        
        # Save 
        plt.savefig('tables\\'+date+'\Log\opl_curve_'+str(round(wl))+'_pm.png')
        np.savetxt('tables\\'+date+'\Log\opl_curve_'+str(round(wl))+'pm.txt',np.vstack((pos,contrast)).T,header='wavelength [pm] \t position [qc]')
        
        
    # Save OPL table    
    optimal_OPL_list=np.asarray(optimal_OPL_list)
    wls = np.array(wls)
    np.savetxt('tables\\'+date+'\Table_OPL_'+sample+'.txt',np.vstack((wls/1000,optimal_OPL_list)).T,header='wavelength [nm] \t position [qc]')
     
    # Timing
    end_time = time.time()
    print('Elapsed time:',end_time - start_time,'s')
    
    laser.RFPowerOff()
    time.sleep(0.3)
    laser.RFSwitch(RFSwitchState)
    time.sleep(0.3)    


def getShutterTable(fromMain=False,host_from_main=None):    
    laser.LaserCheck()
    laser.EmissionOn()
    laser.setAmplitude(100)
    
    # Import host for Koala Login
    if fromMain==False:
        host = koala.KoalaLogin()
    else:
        host = host_from_main
        
    RFSwitchState=laser.readRFSwitch()
    start_time = time.time() # Timing
    sample = Inputs.setObject()
    MO,wls,OPL_array,shutter_guess_array=Inputs.setShutterSweepParameters()
    
    optimal_shutter_list = []
    for wl,i in zip(wls,range(len(wls))):
        if laser.switchCrystalCondition(wl,RFSwitchState)==1:
            laser.RFPowerOff()
            time.sleep(0.25)
            laser.RFSwitch(RFSwitchState)
            laser.RFPowerOn()
            RFSwitchState = laser.readRFSwitch()          
            laser.setWavelength(wl)
            time.sleep(0.1)
        
        laser.setWavelength(wl)
        host.MoveOPL(OPL_array[i])
        
        initial_shutter_value = shutter_guess_array[i]
        frac = 2
        step = frac*initial_shutter_value/75
        shutter_sweep_array = np.arange(initial_shutter_value - frac*initial_shutter_value, initial_shutter_value + frac*initial_shutter_value, step)
        min_val = np.min(shutter_sweep_array)
        if min_val < 0:
            shutter_sweep_array = shutter_sweep_array - min_val
    
        # Loop on shutter values
        contrast = [host.GetHoloContrast()]
        shutter = [shutter_sweep_array[0]]
        plt.ion()
        figure, ax = plt.subplots(figsize=(12,4))
        line1, = ax.plot(shutter,contrast,'k-')
        plt.title(str(round(wl))+' pm')
        plt.xlabel('Exposition time [$\mu$s]')
        plt.ylabel('Contrast')
        plt.grid(True)
        
        for s in shutter_sweep_array:
            print('\nSHUTTER VALUE:',s*1e-3,' ms')
            host.SetCameraShutterUs(s) # TODO: attention aux unités
            time.sleep(s*1e-6)
            contrast.append(host.GetHoloContrast())
            shutter.append(s)
            
            line1.set_xdata(shutter)
            line1.set_ydata(contrast)
            ax.set_xlim(shutter[0],shutter[-1])
            ax.set_ylim(np.min(contrast),np.max(contrast))
            figure.canvas.draw()
            figure.canvas.flush_events()
        
        plt.close()
        
        contrast = np.asarray(contrast)
        shutter = np.asarray(shutter)
        optimal_shutter = shutter[contrast.argmax()] # Extracting position for max holo contrast
        optimal_shutter_list.append(optimal_shutter)
        
        plt.close('all')
        plt.plot(shutter,contrast,'ko-',markersize=4)
        plt.axvline(x=optimal_shutter,color='red',linestyle='-')
        plt.xlabel('Shutter speed [ms]')
        plt.ylabel('Hologram contrast')
        plt.grid(True)
        plt.show()
        
        # Save data
        date=datetime.today().strftime('%Y%m%d')
        plt.savefig('tables\\'+date+'\Log\shutter_curve_'+str(round(wl))+'_pm.png')
        np.savetxt('tables\\'+date+'\Log\shutter_curve_'+str(round(wl))+'pm.txt',np.vstack((shutter,contrast)).T,header='wavelength [pm] \t shutter speed [ms]')
        
    # Save shutter table    
    optimal_shutter_list=np.asarray(optimal_shutter_list)
    wls = np.array(wls)
    np.savetxt('tables\\'+date+'\Table_shutter_'+sample+'.txt',np.vstack((wls/1000,optimal_shutter_list)).T,header='wavelength [nm] \t shutter speed [ms]')
    
    # Timing
    end_time = time.time()
    print('Elapsed time:',end_time - start_time,'s')
    
    laser.RFPowerOff()
    time.sleep(0.3)
    laser.RFSwitch(RFSwitchState)
    time.sleep(0.3)    
    
    laser.CloseAll()