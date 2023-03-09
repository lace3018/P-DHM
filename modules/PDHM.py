# -*- coding: utf-8 -*-
"""
Created on Tue Aug  2 15:43:30 2022

@author: lace3018
"""

import modules.laserCommands as laser
import modules.koalaCommands as koala
import modules.Inputs as Inputs
import modules.displayPlots as dp
import getTable as gt
import time
import os

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
    
    # Ask for OPL table update
    update_shutter_bool = Inputs.getUpdateShutterChoice()

    if update_shutter_bool==True:
        gt.getShutterTable(fromMain=True,host_from_main=host)
    
    
    update_opl_bool = Inputs.getUpdateOPLChoice()

    if update_opl_bool==True:
        gt.getOPLTable(fromMain=True,host_from_main=host)
        
    path,wls,OPL_guesses,shutter_speeds = Inputs.setupExperiment()
    
    if video==True:
        frameRate,maxtime = Inputs.setVideoParameters()

    print('---\nP-DHM SEQUENCE INITIALIZATION')
    laser.EmissionOn()
    laser.setWavelength(wls[0])
    time.sleep(0.2)
    laser.setAmplitude(0)
    time.sleep(0.2)
    print('---')
    if video==True:
        return host,path,frameRate,maxtime,wls,OPL_guesses,shutter_speeds
    else:
        return host,path,wls,OPL_guesses,shutter_speeds

def Acquire(host,frame,starttime,path,wavelengths_array,OPL_guesses,shutter_speeds):
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
    laser.RFPowerOn()
    laser.setAmplitude(100)
    RFSwitchState = laser.readRFSwitch()
    
    log_filename = os.path.join(path, 'Log', 'Log.txt')
    file = open(log_filename, "a")
    if frame==0:
        file.write("frame"+"\t"+"wavelength"+"\t"+"time"+"\t"+"shutter speed"+"\t"+"contrast"+"\n")
    
    contrast_list = []
    for i in range(len(wavelengths_array)):
        wavelength = wavelengths_array[i]
        laser.setWavelength(wavelength)
        host.MoveOPL(OPL_guesses[i])
        host.SetCameraShutterUs((shutter_speeds[i])) # set camera to preset shutter value

        if laser.switchCrystalCondition(wavelength,RFSwitchState) == 1:
            laser.RFPowerOff()
            time.sleep(0.25)
            laser.RFSwitch(RFSwitchState)
            laser.RFPowerOn()
            RFSwitchState = laser.readRFSwitch()          
            laser.setWavelength(wavelength)
            time.sleep(0.1)
        
        time.sleep(0.2) # ADDED 2022-10-21 TO TEMPORARILY FIX BAD HOLOGRAMS OCCURING ON RANDOM WAVELENGTHS -CLL
        wavelength_dir = os.path.join(path, str(frame), str(int(wavelength)) + '_' + str(i+1))
        os.makedirs(wavelength_dir, exist_ok=True)
        image_filename = os.path.join(wavelength_dir, 'Hologram.tiff')
        host.SaveImageToFile(1, image_filename)
        contrast = host.GetHoloContrast()
        file.write(str(frame)+"\t"+str(int(wavelength))+"\t"+str(time.time()-starttime)+"\t"+str(shutter_speeds[i])+"\t"+str(contrast)+"\n")
        file.close
        contrast_list.append(contrast)
    
    if min(contrast_list) < 5:
        print("\n\n !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
        print("WARNING: Low hologram contrast detected")
        print("\n !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n\n")
    
    path_contrast = str(path)+'/Log/contrast'
    os.makedirs(path_contrast, exist_ok=True)
    dp.plotContrast(frame,wavelengths_array,contrast_list,path_contrast,'contrast_frame'+str(frame))
    
    laser.RFPowerOff()
    time.sleep(0.1)
    laser.RFSwitch(laser.readRFSwitch())
    time.sleep(0.1)
    
def Reset(host,wavelength):
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
    host.MoveOPL(-403563)#20X : (-403563) ; 5X : (-196000); 10X : (-318160) # TO DO : METTRE LA VALEUR ASSOCIÉE A LA LONGUEUR D'ONDE DONNÉE PAR L'UTILISATEUR
    host.SetCameraShutterUs((0.37-0.37*0.18)*1e3)                           # TO DO : METTRE LA VALEUR ASSOCIÉE A LA LONGUEUR D'ONDE DONNÉE PAR L'UTILISATEUR
    laser.setWavelength(wavelength)
