# -*- coding: utf-8 -*-
"""
Created on Tue Aug  2 15:49:02 2022

@author: lace3018
"""

import PySimpleGUI as sg
import numpy as np
from datetime import datetime
from pathlib import Path
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
import os
import sys

def setExperimentParameters():
    '''
    Asks user for experiment parameters through a user interface.

    Returns
    -------
    path : path (str)
        Path to save holograms
    wavelengths : numpy array
        Array of selected wavelengths [pm].
    N : int
        Number of wavelengths.
    sample : string
        Type of sample (ex. cells).
    OPL_guesses : numpy array
        N-sized 1D array of OPL positions [qc]
    shutter_speeds : numpy array
        N-sized 1D array of shutter speeds [ms]

    '''
    sg.theme('DarkBlue15')
    

    # WINDOW 1 -- Poly or Mono   
    layout = [[sg.T("         "), sg.Radio('Polychromatic', "RADIO1", default=True)],
              [sg.T("         "), sg.Radio('Monochromatic', "RADIO1", default=False)],
              [sg.Submit(), sg.Cancel()]]

    window = sg.Window('Parameters 1', layout, size=(300,300))
    event, values = window.read()
    if values[0]==True:
        MonoOrPoly='P'
    else:
        MonoOrPoly='M'
    window.close()
    
    # WINDOW 2 -- Experiment parameters
    selection = ('cell_chamber','chamlide_cell_chamber','phase_target','reference')
    if MonoOrPoly=='P':
        layout = [
            [sg.Text('Experiment parameters')],
            [sg.Text('Identification', size =(30, 1)), sg.InputText(default_text="lace3018")],
            [sg.Text('Save folder', size =(30, 1)), sg.InputText(default_text="Test_timing")],
            [sg.Text('Save subfolder', size =(30, 1)), sg.InputText(default_text="Test3")],
            [sg.Text('Microscope objective magnification', size =(30, 1)), sg.InputText(default_text="20X")],
            [sg.Text('Start wavelength [nm]',size=(30,1)),sg.InputText(default_text="500")],
            [sg.Text('Stop wavelength [nm]',size=(30,1)),sg.InputText(default_text="850")],
            [sg.Text('Add a wavelength to the array? [nm]',size=(30,1)),sg.InputText(default_text='No')],
            [sg.Text('Number of wavelengths (w/o added wl)',size=(30,1)),sg.InputText(default_text="36")],
            [sg.Text('Select recent OPL table for initial guess',size=(30,1)),sg.InputText(key='-FILE-'),sg.FileBrowse()],
            [sg.Text('Select shutter table',size=(30,1)),sg.InputText(key='-FILE2-'),sg.FileBrowse()],
            [sg.Submit(), sg.Cancel()]]
        window = sg.Window('Experiment parameters', layout)
        event, values = window.read()
        window.close()
        userID = values[0]
        saveFolder = values[1]
        saveSubFolder = values[2]
        MO = values[3]
        startWl = int(values[4]) * 1000
        stopWl = int(values[5]) * 1000
        if values[6]!='No':
            wl2add = int(values[6]*1000)
        N = int(values[7])   
        oplPath = values['-FILE-']
        shutterPath = values['-FILE2-']
        
    if MonoOrPoly=='M':
        layout = [
            [sg.Text('Experiment parameters')],
            [sg.Text('Identification', size =(30, 1)), sg.InputText(default_text="lace3018")],
            [sg.Text('Save folder', size =(30, 1)), sg.InputText(default_text="Banque_HR-DHM")],
            [sg.Text('Save subfolder', size =(30, 1)), sg.InputText(default_text="FOV30")],
            [sg.Text('Microscope objective magnification', size =(30, 1)), sg.InputText(default_text="5X")],
            [sg.Text('Wavelength [nm]',size=(15,1)),sg.InputText(default_text="666")],
            [sg.Text('Number of wavelengths',size=(15,1)),sg.InputText(default_text="1")],
            [sg.Text('Select recent OPL table for initial guess',size=(30,1)),sg.InputText(key='-FILE-'),sg.FileBrowse()],
            [sg.Text('Select shutter table',size=(30,1)),sg.InputText(key='-FILE2-'),sg.FileBrowse()],
            [sg.Submit(), sg.Cancel()]]
        window = sg.Window('Simple data entry window', layout)
        event, values = window.read()
        window.close()
        userID = values[0]
        saveFolder = values[1]
        saveSubFolder = values[2]
        MO = values[3]
        startWl = int(values[4]) * 1000
        stopWl = int(values[4]) * 1000
        N = int(values[5])
        oplPath = values['-FILE-']
        shutterPath = values['-FILE2-']
    
    wavelengths = np.linspace(startWl,stopWl,N)
    if MonoOrPoly=='P' and values[6]!='No':
        ii = np.searchsorted(wavelengths,wl2add)
        wavelengths = np.insert(wavelengths,ii,wl2add)
        N+=1
    date=datetime.today().strftime('%Y%m%d')
    path = Path(r'\\172.16.1.103\data\DHM 1087\%s\RawData\%s\%s\%s\%s'%(userID,date,MO,saveFolder,saveSubFolder))
    pathlog=Path(r'\\172.16.1.103\data\DHM 1087\%s\RawData\%s\%s\%s\%s\Log'%(userID,date,MO,saveFolder,saveSubFolder))
    isExist=os.path.exists(pathlog)
    if not isExist:
        os.makedirs(pathlog)
        
    wavelengths = np.around(wavelengths,decimals=0)
    np.savetxt(str(pathlog)+'\wavelengths.txt',wavelengths)   # TODO : test this line
    with open('userparams.txt','w') as f:
        f.write('Mono- or polychromatic: \t'+MonoOrPoly+'\n')
        f.write('Identification: \t'+userID+'\n')
        f.write('Save folder: \t'+saveFolder+'\n')
        f.write('Save subfolder: \t'+saveSubFolder+'\n')
        f.write('Microscope objective magnification: \t'+MO+'\n')
    f.close()
        
    # Shutter speed and interpolation
    shutter_measured = np.loadtxt(shutterPath,skiprows=1).T[2]
    shutter_measured = shutter_measured - 0.2*shutter_measured
    x = np.loadtxt(shutterPath,skiprows=1).T[0]
    f = interp1d(x,shutter_measured,kind='linear')
    xnew = np.linspace(wavelengths[0]/1000,wavelengths[-1]/1000,N)
    ynew = f(xnew)
    plt.figure()
    plt.plot(x,shutter_measured,'bo',label='From measured optimal shutter speeds')
    plt.plot(xnew,ynew,'r.',label='Used shutters for chosen wavelengths')
    plt.xlabel("Wavelength [nm]")
    plt.ylabel("Shutter [ms]")
    plt.legend()
    plt.savefig(str(path)+'\Log\Shutter.png')
    plt.show()
    shutter_speeds = np.array(f(xnew)) # float64, in ms
    np.savetxt(str(path)+'\Log\Shutter.txt',shutter_speeds)

    plt.close('all')
    
    # OPL guess values and interpolation
    OPL_measured = np.loadtxt(oplPath,skiprows=1).T[1]
    x = np.loadtxt(oplPath,skiprows=1).T[0]
    f2 = interp1d(x,OPL_measured,kind='quadratic',bounds_error=False,fill_value=-10.)
    xnew = np.linspace(wavelengths[0]/1000,wavelengths[-1]/1000,N)
    xplot = np.linspace(wavelengths[0]/1000,wavelengths[-1]/1000,1000)
    ynew = f2(xnew)
    plt.figure()
    plt.plot(xplot,f2(xplot),'g--',lw=1,label='interpolation')
    plt.plot(x,OPL_measured,'bo',label='From measured optimal OPL table')
    plt.plot(xnew,ynew,'r.',label='Used motor positions')
    plt.xlabel("Wavelength [nm]")
    plt.ylabel("OPL opt [qc]")
    plt.legend()
    plt.savefig(str(path)+'\Log\OPL.png')
    plt.show()
    OPL_guesses = np.array(f2(xnew)) # float64, in ms
    np.savetxt(str(path)+'\Log\OPR.txt',OPL_guesses)
        
    return path,wavelengths,N,OPL_guesses, shutter_speeds

def setVideoParameters():
    '''
    Generates new user interface window for video parameters

    Returns
    -------
    frameRate : int
        Video frame rate [im/min].
    maxtime : int
        Number of seconds after which acquisition is terminated. [s]

    '''
    sg.theme('DarkBlue15')
    layout = [
        [sg.Text('Video parameters')],
        [sg.Text('Video frame rate [im/min] (integers only)',size=(15,1)),sg.InputText(default_text="1")],
        [sg.Text('Stop acquisition after [min] (integers only)',size=(15,1)),sg.InputText(default_text="180")],
        [sg.Submit(), sg.Cancel()]
    ]
      
    window = sg.Window('Video parameters', layout)
    event, values = window.read()
    window.close()
    
    frameRate = int(values[0])/60   # TODO : changer la variable pour que ce soit un vrai framerate ou changer le nom en conséquence
    maxtime = int(values[1])*60
    
    return frameRate,maxtime

def setMotorSweepParameters():
    '''
    Asks user for experiment parameters through a user interface.

    Returns
    -------
    path : path
        Path to save holograms
    wavelengths : numpy array
        Array of selected wavelengths.
    N : int
        Number of wavelengths.
    sample : string
        Type of sample (ex. cells).
    OPL_guesses : numpy array
        N-sized 1D array of OPL positions
    shutter_speeds : numpy array
        N-sized 1D array of shutter speeds

    '''
    
    sg.theme('DarkBlue15')
    
    # Define the list of options for the Listbox
    selection = ('cell_chamber','chamlide_cell_chamber','phase_target','reference')
    
    # Create a settings object
    settings = sg.UserSettings()
    
    # Load the previously used values, if any
    magnification = settings.get('magnification', '20X')
    start_wavelength = settings.get('start_wavelength', '500')
    stop_wavelength = settings.get('stop_wavelength', '850')
    num_wavelengths = settings.get('num_wavelengths', '10')
    oplPath = settings.get('oplPath', 'S:/DHM 1087/lace3018/PDHM_automated_acquisition/tables/Archive/Table_shutter_vide.txt')
    shutterPath = settings.get('shutterPath', 'S:/DHM 1087/lace3018/PDHM_automated_acquisition/tables/Archive/Table_shutter_vide.txt')
    selected_option = settings.get('selected_option', selection[0])

    # Define the layout of the prompt
    layout = [
        [sg.Text('Experiment parameters')],
        [sg.Text('Microscope objective magnification', size =(30, 1)), sg.InputText(default_text=magnification,key='magnification')],
        [sg.Text('Start wavelength [nm]',size=(30,1)),sg.InputText(default_text=start_wavelength,key='start_wavelength')],
        [sg.Text('Stop wavelength [nm]',size=(30,1)),sg.InputText(default_text=stop_wavelength,key='stop_wavelength')],
        [sg.Text('Number of wavelengths (w/o added wl)',size=(30,1)),sg.InputText(default_text=num_wavelengths,key='num_wavelengths')],
        [sg.Text('Select recent OPL table for initial guess',size=(30,1)),sg.InputText(default_text=oplPath,key='oplPath'),sg.FileBrowse()],
        [sg.Text('Select shutter table',size=(30,1)),sg.InputText(default_text=shutterPath,key='shutterPath'),sg.FileBrowse()],
        [sg.Listbox(['Cell culture chamber','Chamlide','Phase target','Air (for reference holograms)'], size=(60,4), enable_events=False, key='fac',default_values=[selected_option])],
        [sg.Submit(), sg.Cancel()]]
        
    # Create the prompt window
    window = sg.Window('Experiment parameters', layout)
    
    # Loop to read the values and events
    while True:
        event, values = window.read()
        if event == 'Submit':
            # Save the values to the UserSettings object
            settings.set('magnification', values['magnification'])
            settings.set('start_wavelength', values['start_wavelength'])
            settings.set('stop_wavelength', values['stop_wavelength'])
            settings.set('num_wavelengths', values['num_wavelengths'])
            settings.set('oplPath', values['oplPath'])
            settings.set('shutterPath', values['shutterPath'])
            settings.set('selected_option', values['fac'][0])
            # Print the values for testing
            print(values)
            break
        if event == 'Cancel':
            window.close()
            sys.exit()
    
    # Close the window
    window.close()
    
    # Assign values
    MO = values['magnification']
    startWl = int(values['start_wavelength']) * 1000
    stopWl = int(values['stop_wavelength']) * 1000
    N = int(values['num_wavelengths'])
    oplPath = values['oplPath']
    shutterPath = values['shutterPath']
    strx=""
    for val in values['fac']:
        strx=strx+ " "+ val+","
        if val=='Cell culture chamber':
            sample = 'cell_chamber'
        if val=='Chamlide':
            sample= 'chamlide_cell_chamber'
        if val=='Phase target':
            sample= 'phase_target'
        if val=='Air (for reference holograms)':
            sample='reference'
    
    print(oplPath, shutterPath)
    
    wavelengths = np.linspace(startWl,stopWl,N)
    date=datetime.today().strftime('%Y%m%d')
    path = Path(r'\\172.16.1.103\data\DHM 1087\lace3018\PDHM_automated_acquisition\tables\%s'%(date))
    pathlog=Path(r'\\172.16.1.103\data\DHM 1087\lace3018\PDHM_automated_acquisition\tables\%s\Log'%(date))
    isExist=os.path.exists(pathlog)
    if not isExist:
        os.makedirs(pathlog)
        
    # Shutter speed and interpolation
    shutter_measured = np.loadtxt(shutterPath,skiprows=1).T[2]
    shutter_measured = shutter_measured - 0.2*shutter_measured
    x = np.loadtxt(shutterPath,skiprows=1).T[0]
    f = interp1d(x,shutter_measured,kind='linear')
    xnew = np.linspace(wavelengths[0]/1000,wavelengths[-1]/1000,N)
    ynew = f(xnew)
    plt.plot(x,shutter_measured,'bo',label='From measured optimal shutter speeds')
    plt.plot(xnew,ynew,'r.',label='Used shutters for chosen wavelengths')
    plt.xlabel("Wavelength [nm]")
    plt.ylabel("Shutter [ms]")
    plt.legend()
    plt.savefig(str(path)+'\Log\Shutter.png')
    plt.show()
    shutter_speeds = np.array(f(xnew)) # float64, in ms
    np.savetxt(str(path)+'\Log\Table_shutter_used.txt',shutter_speeds)

    plt.close('all')

    # OPL guess values and interpolation
    OPL_measured = np.loadtxt(oplPath,skiprows=1).T[1]
    x = np.loadtxt(oplPath,skiprows=1).T[0]
    f2 = interp1d(x,OPL_measured,kind='quadratic',bounds_error=False,fill_value=-10.)
    xnew = np.linspace(wavelengths[0]/1000,wavelengths[-1]/1000,N)
    xplot = np.linspace(wavelengths[0]/1000,wavelengths[-1]/1000,1000)
    ynew = f2(xnew)
    plt.plot(xplot,f2(xplot),'g--',lw=1,label='interpolation')
    plt.plot(x,OPL_measured,'bo',label='From measured optimal OPL table')
    plt.plot(xnew,ynew,'r.',label='Used motor positions')
    plt.xlabel("Wavelength [nm]")
    plt.ylabel("OPL opt [qc]")
    plt.legend()
    plt.savefig(str(path)+'\Log\OPL.png')
    plt.show()
    OPL_guesses = np.array(f2(xnew)) # float64, in ms
        
    return path,sample,MO,wavelengths,N,OPL_guesses,shutter_speeds