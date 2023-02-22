# -*- coding: utf-8 -*-
"""
Created on Tue Aug  2 15:43:30 2022

@author: lace3018
"""

import laserCommands as laser
import koalaCommands as koala
import Inputs
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
    koala.checkKoalaRemote()
    host=koala.KoalaLogin()
    path,wls,N,OPL_guesses,shutter_speeds = Inputs.setExperimentParameters()
    
    print('Wavelength array : ',wls)
    
    if video==True:
        frameRate,maxtime = Inputs.setVideoParameters()

    print('INITIALIZATION')
    laser.EmissionOn()
    laser.setWavelength(wls[0])
    time.sleep(0.2)
    laser.setAmplitude(0)
    time.sleep(0.2)
    if video==True:
        return host,path,frameRate,maxtime,wls,N,OPL_guesses,shutter_speeds
    else:
        return host,path,wls,N,OPL_guesses,shutter_speeds

def Acquire(host,frame,starttime,path,wls,N,OPL_guesses,shutter_speeds):
    laser.RFPowerOn()
    laser.setAmplitude(100)
    RFSwitchState = laser.readRFSwitch()
    
    filename=(str(path)+'\Log\\time.txt')
    file = open(filename, "a")
    if frame==0:
        file.write("frame"+"\t"+"wavelength"+"\t"+"time"+"\t"+"shutter speed"+"\n")
    
    for i in range(N):
        laser.setWavelength(wls[i])
        host.MoveOPL(OPL_guesses[i])
        host.SetCameraShutterUs((shutter_speeds[i])*1e3) # set camera to preset shutter value (or interpolated)

        if laser.switchCrystalCondition(wls[i],RFSwitchState)==1:
            laser.RFPowerOff()
            time.sleep(0.25)
            laser.RFSwitch(RFSwitchState)
            laser.RFPowerOn()
            RFSwitchState = laser.readRFSwitch()          
            laser.setWavelength(wls[i])
            time.sleep(0.1)
        
        time.sleep(0.2) # ADDED 2022-10-21 TO TEMPORARILY FIX BAD HOLOGRAMS OCCURING ON RANDOM WAVELENGTHS        -- CLL
        host.SaveImageToFile(1, str(path/str(frame)/str(str(int(wls[i]))+'_'+str(int(i+1)))/'Hologram.tiff'))
        file.write(str(frame)+"\t"+str(int(wls[i]))+"\t"+str(time.time()-starttime)+"\t"+str(shutter_speeds[i])+"\n")
        file.close
    
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
