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
import tempfile
import tifffile

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
    MO,wls,OPL_array,shutter_array,interval,step=Inputs.setMotorSweepParameters()
    
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
    np.savetxt(f"tables\\{date}\Table_OPL_{sample}_{MO}.txt",np.vstack((wls/1000,optimal_OPL_list)).T,header='wavelength [nm] \t position [qc]')
     
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
    MO,wls,OPL_array=Inputs.setShutterSweepParameters()
    
    optimal_shutter_list = []
    for wl,i in zip(wls,range(len(wls))):
        print('\n\n WAVELENGTH: ',str(wl),' pm\n\n')
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
        
        step = 50 # us
        shutter = 0
        
        # Loop on shutter values
        max_pixel = [0]
        shutter_plot = [0]
        plt.ion()
        figure, ax = plt.subplots(figsize=(6,3))
        line1, = ax.plot(shutter_plot,max_pixel,'k-')
        plt.title(str(round(wl))+' pm')
        plt.xlabel('Exposition time [$\mu$s]')
        plt.ylabel('Hologram max pixel value')
        plt.grid(True)
        legend_created=False
        
        with tempfile.TemporaryDirectory() as temp_dir:
        
            while True:
                shutter += step
                print('SHUTTER VALUE:',shutter,' ms; STEP: ',step)
                
                host.SetCameraShutterUs(shutter)
                time.sleep(shutter*1e-6)
                host.SaveImageToFile(1,temp_dir+'holo_temp.tiff')
                time.sleep(0.05)
                temp_holo = tifffile.imread(temp_dir+'holo_temp.tiff')
                if np.any(temp_holo == 250) and shutter>500:
                    optimal_shutter_list.append(shutter)
                    print('\n*****\n optimal shutter for '+str(wl)+' pm: ',str(shutter-step),'\n*****\n')
                    break
                mp = np.max(temp_holo)
                if 2500<shutter<7000:
                    step = 200
                if shutter>7000:
                    if mp<230:
                        step = 2000
                    else:
                        step = 200
                shutter_plot.append(shutter)
                max_pixel.append(mp)
                
                line1.set_xdata(shutter_plot)
                line1.set_ydata(max_pixel)
                if shutter_plot[0]==shutter_plot[-1]:
                    ax.set_xlim(shutter_plot[0],step)
                else:
                    ax.set_xlim(shutter_plot[0],shutter_plot[-1])
                ax.set_ylim(0,275)
                ax.axhline(y=255,color='red',label='Saturation')
                if not legend_created:
                    ax.legend()
                    legend_created = True
                figure.canvas.draw()
                figure.canvas.flush_events()
        
        plt.close()
        

    date=datetime.today().strftime('%Y%m%d')

    # Save shutter table    
    optimal_shutter_list=np.asarray(optimal_shutter_list)
    wls = np.array(wls)
    np.savetxt(f'tables\{date}\Table_shutter_{sample}_{MO}.txt',np.vstack((wls/1000,optimal_shutter_list)).T,header='wavelength [nm] \t shutter speed [ms]')
    
    # Timing
    end_time = time.time()
    print('Elapsed time:',end_time - start_time,'s')
    
    laser.RFPowerOff()
    time.sleep(0.3)
    laser.RFSwitch(RFSwitchState)
    time.sleep(0.3)    
    
    laser.CloseAll()