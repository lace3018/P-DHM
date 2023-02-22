# -*- coding: utf-8 -*-
"""
Created on Mon Aug  8 14:13:29 2022

@author: lace3018
"""

from . import laserCommands as laser
import numpy as np
import matplotlib.pyplot as plt

def balanceInterferometer(host,wl,OPL_guess,shutter_speed,half_interval=200,step=5): 
    '''
    Sweeps motor positions for selected wavelengths and records maximal contrast.

    Parameters
    ----------
    host : --
        Contacts Koala Remote.
    wl : numpy array
        Array of wavelengths.
    OPL_guess : numpy array
        OPL value that the function sweeps around.
    shutter_speed : numpy array
        Pre-selected shutter speeds for each wavelength.
    half_interval : float, optional
        Half interval for sweep around OPL guess [um]. The default is 200.
    step : float, optional
        Step for the sweep of motor positions [um]. The default is 5.

    Returns
    -------
    pos : numpy array
        Array of positions for each wavelength.
    contrast : numpy array
        Array of contrast value for each position.
    optimal_OPL : numpy array
        Array of optimal positions for each wl (max contrast).

    '''
    half_interval_qc = half_interval*19.714
    step_qc = step*19.714
    # RFSwitchState=laser.readRFSwitch()
    # laser.EmissionOn()
    # laser.RFSwitch(RFSwitchState)
    laser.setAmplitude(100)
    # RFSwitchState = laser.readRFSwitch()
    
    laser.setWavelength(wl)
    host.SetCameraShutterUs(shutter_speed*1e3)
    initPos = int(OPL_guess)
    positions = np.arange(initPos-half_interval_qc,initPos+half_interval_qc,step_qc)
    host.MoveOPL(positions[0])
    contrast=[host.GetHoloContrast()]
    pos=[positions[0]]
    plt.ion()
    figure, ax = plt.subplots(figsize=(12,4))
    line1, = ax.plot(pos,contrast,'k-')
    plt.title(str(round(wl))+' pm')
    plt.xlabel('Position [$\mu$m]')
    plt.ylabel('Contrast')
    plt.grid(True)
    for p in positions:
        host.MoveOPL(p) # moving motor to position
        contrast.append(host.GetHoloContrast()) # save contrast
        pos.append(p) # save position    
        
        line1.set_xdata(qc2um(pos))
        line1.set_ydata(contrast)
        ax.set_xlim(qc2um(pos[0]),qc2um(pos[-1]))
        ax.set_ylim(np.min(contrast),np.max(contrast))
        figure.canvas.draw()
        figure.canvas.flush_events()
        # time.sleep(0.1)
    plt.close()   
    pos=np.asarray(pos)
    contrast=np.asarray(contrast)
    optimal_OPL=pos[contrast.argmax()] # Extracting position for max holo contrast
    
    
    return pos,contrast,optimal_OPL 

def qc2um(pos_qc):
    if isinstance(pos_qc,list)==True:
        pos_um = [(p+511507)/19.714 for p in pos_qc]
        return pos_um
    else:
        pos_um = (pos_qc+511507)/19.714
        return pos_um
    
def um2qc(pos_um):
    if isinstance(pos_um,list)==True:
        pos_qc = [(p*19.714)-511507 for p in pos_um]
        return pos_um
    else:
        pos_um = (pos_qc*19.714)-511507
        return pos_um
    