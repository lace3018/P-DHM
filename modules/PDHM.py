# -*- coding: utf-8 -*-
"""
Created on Tue Aug  2 15:43:30 2022

@author: lace3018
"""

import modules.laserCommands as laser
import modules.koalaCommands as koala
import modules.Inputs as Inputs
import modules.displayPlots as dp
import modules.checkHolos as checkHolos
import time
import os
import sys
import numpy as np

def Initialize(video=True):
    '''
    Returns all the initial parameters required for P-DHM acquisition.

    Parameters
    ----------
    video : TYPE, optional
        If True the user will have a different parameter selection window and 
        will be able to select frame rate and other video parameters. 
        The default is True.

    Returns
    -------
    host : Module to communicate with Koala Remote (_)
    path : Path to save files (str)
    frameRate : Video frame rate for acquisition (float) [im/s]
    maxtime : Max time for acquisition (float) [s]
    wls : Array of all the P-DHM wavelengths (numpy array) [pm]
    N : Number of wavelengths or images to be saved (int)
    OPL_guesses : List of OPL values to feed Koala Remote for motor positions (list) [qc]
    shutter_speeds : List of shutter values to feed Koala Remote for motor positions (list) [ms]
    
    '''
    laser.CloseAll()
    time.sleep(1)
    laser.LaserCheck()
    host=koala.KoalaLogin()
            
    path,wls,OPL_guesses,shutter_speeds,oplPath,shutterPath = Inputs.setupExperiment(host)
    host.OpenHoloWin()
    host.OpenPhaseWin()
    host.OpenIntensityWin()
    
    if path==None:
        Reset(host, 660000, -400358)
        sys.exit()
    if video==True:
        frameRate,maxtime = Inputs.setVideoParameters(host)
        return host,path,frameRate,maxtime,wls,OPL_guesses,shutter_speeds,oplPath,shutterPath
    else:
        return host,path,wls,OPL_guesses,shutter_speeds,oplPath,shutterPath
    
    
def get_version():
    version_file_path = os.path.dirname(os.path.realpath(__file__))
    version_file_path = os.path.dirname(version_file_path)  # this line gets us one directory up to the "main.py" folder
    with open(os.path.join(version_file_path, 'version.txt'), 'r') as f:
        version = f.read().strip()  # Read the version and remove any leading/trailing whitespace
    return version


def Acquire(host,frame,starttime,path,wavelengths_array,OPL_guesses,shutter_speeds,oplPath,shutterPath):
    '''
    Acquires hologram images at multiple wavelengths and saves them to file. 

    Parameters:
        host (object): an object containing methods for communication with the optical setup
        frame (int): the frame number
        starttime (float): the start time of the acquisition in seconds
        path (str): the file path to the directory where the images will be saved
        wls (list of floats): the list of wavelengths to acquire hologram images at
        N (int): the number of wavelengths to acquire hologram images at
        OPL_guesses (list of floats): the list of guesses for the optical path length
        shutter_speeds (list of floats): the list of shutter speeds to use for each wavelength

    Returns:
        None
    '''
    # Pre-creating the directories to store the images
    holo_filenames = []
    phase_filenames = []
    intensity_filenames = []
    
    for wavelength,i in zip(wavelengths_array,range(len(wavelengths_array))):
        wavelength_dir = os.path.join(path, str(frame), str(int(wavelength)) + '_' + str(i+1))
        os.makedirs(wavelength_dir, exist_ok=True)
        
        holo_filenames.append(os.path.join(wavelength_dir, 'Hologram.tiff'))
        phase_filenames.append(os.path.join(wavelength_dir, 'Phase.tiff'))
        intensity_filenames.append(os.path.join(wavelength_dir, 'Intensity.png'))
    
    # Starting the laser
    laser.EmissionOn()
    time.sleep(0.2)
    laser.RFPowerOn()
    laser.setAmplitude(100)
    RFSwitchState = laser.readRFSwitch()
    
    log_filename = os.path.join(path, 'Log', 'Log.txt')
    with open(log_filename, "a") as file:
        if frame==0:
            version = get_version()
            file.write(f'Acquisition code version: {version}\n')
            file.write(f'OPL table selected: {oplPath}\n')
            file.write(f'Shutter table selected: {shutterPath}\n')
            file.write("frame"+"\t"+"wavelength"+"\t"+"time"+"\t"+"shutter speed"+"\n")
        
        # Acquisition loop
        for i in range(len(wavelengths_array)):
            wavelength = wavelengths_array[i]
            laser.setWavelength(wavelength)
            host.MoveOPL(OPL_guesses[i])
            host.SetCameraShutterUs((shutter_speeds[i])) # set camera to preset shutter value
            
            if laser.check_for_crystal_switch(wavelength, RFSwitchState) == True:
                laser.switchCrystal(RFSwitchState)
                RFSwitchState = 1
            
            time.sleep(0.15) # SLEEP ADDED TO AVOID LATENCY ISSUES
            # host.ComputePhaseCorrection(0,1) # TILT CORRECTION
            
            host.SaveImageToFile(1, holo_filenames[i])
            host.SaveImageToFile(2, intensity_filenames[i])
            host.SaveImageToFile(4, phase_filenames[i])
            
            file.write(str(frame)+"\t"+str(int(wavelength))+"\t"+str(time.time()-starttime)+"\t"+str(shutter_speeds[i])+"\n")
            
            # dp.displayAll(holo_filenames[i], intensity_filenames[i], phase_filenames[i], wavelength, frame)

    
    laser.RFPowerOff()
    
    # Display phase at 660 nm
    dp.displayPhaseImage(phase_filenames[np.argmin(np.abs(wavelengths_array-660000))], 660000, frame)
    
    # Check holograms for fringes
    # fringe_file_path = f'{path}/Log/fringes_results.txt'
    
    # with open(fringe_file_path, 'a') as fringe_file:
    #     for wl, i in zip(wavelengths_array, range(len(wavelengths_array))):
    #         has_fringes = checkHolos.detect_fringes(holo_filenames[i], wl, frame)
    #         print(wl, 'pm | Fringes detected : ', has_fringes)
    #         fringe_file.write(f"Frame {frame} | {wl} pm | Fringes detected : {has_fringes}\n")

    laser.RFSwitch(laser.readRFSwitch())
    time.sleep(0.1)
    
def Reset(host,wavelength,opl):
    '''
    Resets laser to given wavelength.

    Parameters
    ----------
    wavelength : float
        wavelength in pm.

    Returns
    -------
    None.

    '''
    laser.EmissionOn()
    print('\n\n Wavelength reseted to find next FOV')
    host.MoveOPL(opl)#20X : (-403563) ; 5X : (-196000); 10X : (-318160) # TO DO : METTRE LA VALEUR ASSOCIÉE A LA LONGUEUR D'ONDE DONNÉE PAR L'UTILISATEUR
    host.SetCameraShutterUs((0.37-0.37*0.18)*1e3)                           # TO DO : METTRE LA VALEUR ASSOCIÉE A LA LONGUEUR D'ONDE DONNÉE PAR L'UTILISATEUR
    laser.setWavelength(wavelength)
    time.sleep(0.5)
    host.ComputePhaseCorrection(0,1) # TILT CORRECTION
    host.Logout()