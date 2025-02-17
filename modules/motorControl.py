# -*- coding: utf-8 -*-
"""
Created on Mon Aug  8 14:13:29 2022

@author: lace3018
"""

from . import laserCommands as laser
import numpy as np
import matplotlib.pyplot as plt
import time


def balanceInterferometer(host, wl, OPL_guess, shutter_speed, path, half_interval=200, step=5, saveHolo=False): 
    '''
    Sweeps motor positions for selected wavelengths and records maximal contrast.

    Parameters
    ----------
    host : --
        Contacts Koala Remote.
    wl : numpy array
        Array of wavelengths.
    OPL_guess : float
        OPL value that the function sweeps around.
    shutter_speed : float
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
    # Convert to qc units
    QC_CONVERSION_FACTOR = 19.714
    half_interval_qc = half_interval * QC_CONVERSION_FACTOR
    step_qc = step * QC_CONVERSION_FACTOR

    # Setup the laser and camera
    # laser.setAmplitude(100)
    laser.setWavelength(wl)
    host.SetCameraShutterUs(0.7*shutter_speed)

    # Create array of positions
    initPos = int(OPL_guess)
    positions = np.arange(initPos-half_interval_qc,initPos+half_interval_qc,step_qc)

    contrast = []
    pos = []

    # Setup plot
    figure, ax = plt.subplots(figsize=(6,5))
    line1, = ax.plot(pos,contrast,'k-')
    plt.title(str(round(wl))+' pm')
    plt.xlabel('Position [$\mu$m]')
    plt.ylabel('Contrast')
    plt.grid(True)

    # Sweep positions
    for p in positions:
        host.MoveOPL(p) 
        time.sleep(0.1)

        # Update contrast and position data
        contrast.append(host.GetHoloContrast())
        pos.append(p)
        
        # Update plot data and redraw
        line1.set_xdata(qc2um(pos))
        line1.set_ydata(contrast)
        ax.set_xlim(qc2um(pos[0]),qc2um(pos[-1]))
        ax.set_ylim(np.min(contrast),np.max(contrast))
        figure.canvas.draw()
        figure.canvas.flush_events()

    plt.close() 

    # Convert lists to numpy arrays
    pos = np.asarray(pos)
    contrast = np.asarray(contrast)

    # Find position with maximum contrast
    optimal_OPL = pos[contrast.argmax()]

    return pos, contrast, optimal_OPL


def findCenterPosition(host): 
    # Setup the laser and camera
    laser.setAmplitude(100)
    laser.setWavelength(660000)
    host.SetCameraShutterUs(600)

    # Create array of positions
    positions = np.linspace(-20000,30000,300)
    positions_qc = um2qc(positions)
    print(positions_qc)
    
    contrast = []
    pos = []

    # Setup plot
    figure, ax = plt.subplots(figsize=(12,6))
    line1, = ax.plot(pos,contrast,'k-')
    plt.title('Full range at 660 nm')
    plt.xlabel('Position [$\mu$m]')
    plt.ylabel('Contrast')
    plt.grid(True)

    # Sweep positions
    for p in positions_qc:
        host.MoveOPL(p) 
        time.sleep(0.1)

        # Update contrast and position data
        contrast.append(host.GetHoloContrast())
        pos.append(p)
        
        # Update plot data and redraw
        line1.set_xdata(qc2um(pos))
        line1.set_ydata(contrast)
        ax.set_xlim(qc2um(pos[0]),qc2um(pos[-1]))
        ax.set_ylim(np.min(contrast),np.max(contrast))
        figure.canvas.draw()
        figure.canvas.flush_events()

    plt.close() 

    # Convert lists to numpy arrays
    pos = np.asarray(pos)
    contrast = np.asarray(contrast)

    # Find position with maximum contrast
    optimal_OPL = pos[contrast.argmax()]

    return optimal_OPL



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
        return pos_qc
    else:
        pos_qc = (pos_um*19.714)-511507
        return pos_qc
    