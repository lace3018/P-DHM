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

sg.theme('DefaultNoMoreNagging')

def getUpdateOPLChoice():
    layout = [[sg.Text('Do you need to update the OPL table?')],
              [sg.Button('Yes'), sg.Button('No')]]

    window = sg.Window('Update OPL table', layout)

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED:
            update_opl = False  # default value if window is closed
            break
        elif event == 'Yes':
            update_opl = True
            break
        elif event == 'No':
            update_opl = False
            break

    window.close()

    print(f'Update OPL table: {update_opl}')
    return update_opl

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
    
    MO = setMicroscopeObjective()  
    userID,saveFolder,saveSubFolder = setSavingParameters()
    
    date=datetime.today().strftime('%Y%m%d')
    if saveSubFolder=='':
        path = Path(r'\\172.16.1.103\data\DHM 1087\%s\RawData\%s\%s\%s'%(userID,date,MO,saveFolder))
        pathlog=Path(r'\\172.16.1.103\data\DHM 1087\%s\RawData\%s\%s\%s\Log'%(userID,date,MO,saveFolder))
    else:
        path = Path(r'\\172.16.1.103\data\DHM 1087\%s\RawData\%s\%s\%s\%s'%(userID,date,MO,saveFolder,saveSubFolder))
        pathlog=Path(r'\\172.16.1.103\data\DHM 1087\%s\RawData\%s\%s\%s\%s\Log'%(userID,date,MO,saveFolder,saveSubFolder))
    isExist=os.path.exists(pathlog)
    if not isExist:
        os.makedirs(pathlog)
        
    wavelengths = setWavelengthArray(MonoOrPoly)
    
    np.savetxt(str(pathlog)+'\wavelengths.txt',wavelengths)   # TODO : test this line
    with open('userparams.txt','w') as f:
        f.write('Mono- or polychromatic: \t'+MonoOrPoly+'\n')
        f.write('Identification: \t'+userID+'\n')
        f.write('Save folder: \t'+saveFolder+'\n')
        f.write('Save subfolder: \t'+saveSubFolder+'\n')
        f.write('Microscope objective magnification: \t'+MO+'\n')
    f.close()
        
    OPL_array = setOPLarray(wavelengths)
    shutter_array = setShutterArray(wavelengths)
    
    return path,wavelengths,OPL_array,shutter_array

def setMicroscopeObjective():
    layout = [
        [sg.Text('Select microscope magnification:')],
        [sg.Radio('10x', 'MAGNIFICATION', key='-10X-')],
        [sg.Radio('20x', 'MAGNIFICATION', default=True, key='-20X-')],
        [sg.Radio('40x', 'MAGNIFICATION', key='-40X-')],
        [sg.Radio('100x', 'MAGNIFICATION', key='-100X-')],
        [sg.Button('Submit'), sg.Button('Cancel')]
    ]
    
    window = sg.Window('Microscope Magnification Selector', layout)
    
    while True:
        event, values = window.read()
        if event in (None, 'Cancel'):
            break
        elif event == 'Submit':
            if values['-10X-']:
                MO = '10x'
            elif values['-20X-']:
                MO = '20x'
            elif values['-40X-']:
                MO = '40x'
            else:
                MO = '100x'
            print(f'Selected magnification: {MO}')
            break   
    window.close()
    
    return MO

def setSavingParameters():
    layout = [
        [sg.Text('Identification', size =(30, 1)), sg.InputText(default_text="lace3018")],
        [sg.Text('Save folder', size =(30, 1)), sg.InputText(default_text="RatNeurons")],
        [sg.Text('Save subfolder (facult.)', size =(30, 1)), sg.InputText(default_text="")],
        [sg.Submit(), sg.Cancel()]]
    window = sg.Window('Saving parameters', layout)
    event, values = window.read()
    window.close()
    userID = values[0]
    saveFolder = values[1]
    saveSubFolder = values[2]
    
    return userID,saveFolder,saveSubFolder

def setVideoParameters():
    '''
    Generates new user interface window for video parameters

    Returns
    -------
    frameRate : int
        Video frame rate [im/min].
    maxtime : int
        Number of minutes after which acquisition is terminated. [min]

    '''
    layout = [
        [sg.Text('Video parameters')],
        [sg.Text('Video frame rate [im/min] (integers only)',size=(30,1)),sg.InputText(default_text="1")],
        [sg.Text('Stop acquisition after [min] (integers only)',size=(30,1)),sg.InputText(default_text="180")],
        [sg.Submit(), sg.Cancel()]
    ]
      
    window = sg.Window('Video parameters', layout)
    event, values = window.read()
    window.close()
    
    frameRate = int(values[0])/60   # TODO : changer la variable pour que ce soit un vrai framerate ou changer le nom en conséquence
    maxtime = int(values[1])*60
    
    return frameRate,maxtime

def setWavelengthArray(MonoOrPoly):
    if MonoOrPoly=='P':
        layout = [
        [sg.Text('Number of wavelengths: '), sg.Input(key='num_values',default_text='36')],
        [sg.Text('Minimum wavelength: '), sg.Slider(range=(500, 850), orientation='h', size=(20, 15), default_value=500, key='min_value')],
        [sg.Text('Maximum wavelength: '), sg.Slider(range=(500, 850), orientation='h', size=(20, 15), default_value=850, key='max_value')],
        [sg.Text('Add a wavelength to the array? [nm]',size=(30,1)),sg.InputText(default_text='No',key='added_wl')],
        [sg.Submit(), sg.Cancel()]
        ]
        
        window = sg.Window('Array Generator', layout)
        
        event, values = window.read()
        
        if event == 'Submit':
            num_values = int(values['num_values'])
            min_value = int(values['min_value']*1000)
            max_value = int(values['max_value']*1000)
        
            # Generate the array
            step = (max_value - min_value) / (num_values - 1)
            wls_array = [round(min_value + step * i) for i in range(num_values)]
        
        window.close()
        
        if values['added_wl']!='No':
            wl2add = int(float(values['added_wl'])*1000)
            ii = np.searchsorted(wls_array,wl2add)
            wls_array = np.insert(wls_array,ii,wl2add)
        
        return wls_array
    
    else:
        layout = [
            [sg.Text('Select the wavelength (nm):')],
            [sg.Slider(range=(500, 850), default_value=666, orientation='h', size=(20,15), key='-WAVELENGTH-')],
            [sg.Text('Enter the number of repetitions:')],
            [sg.Input(default_text='36', key='-REPETITIONS-')],
            [sg.Button('Submit'), sg.Button('Cancel')]
        ]
        
        window = sg.Window('Wavelength Selector', layout)
        
        while True:
            event, values = window.read()
            if event in (None, 'Cancel'):
                break
            elif event == 'Submit':
                wavelength = int(values['-WAVELENGTH-']*1000)
                repetitions = int(values['-REPETITIONS-'])
                wls_array = [wavelength] * repetitions
                break
        
        window.close()
        wls_array = np.asarray(wls_array)
        return wls_array

def setOPLarray(wls):
    # Create a settings object
    settings = sg.UserSettings()
    
    # Load the previously used values, if any
    oplPath = settings.get('oplPath', 'S:/DHM 1087/lace3018/PDHM_automated_acquisition/tables/Archive/Table_shutter_vide.txt')
    
    layout = [
        [sg.Text('Select recent OPL table',size=(30,1)),sg.InputText(key='-FILE-'),sg.FileBrowse()],
        [sg.Submit(), sg.Cancel()]]
    window = sg.Window('Select OPL Table', layout)
    event, values = window.read()
    window.close()
    oplPath = values['-FILE-']
    
    # OPL guess values and interpolation
    OPL_measured = np.loadtxt(oplPath,skiprows=1).T[1]
    x = np.loadtxt(oplPath,skiprows=1).T[0]
    f2 = interp1d(x,OPL_measured,kind='quadratic',bounds_error=False,fill_value=-10.)
    xnew = np.linspace(wls[0]/1000,wls[-1]/1000,len(wls))
    xplot = np.linspace(wls[0]/1000,wls[-1]/1000,1000)
    ynew = f2(xnew)
    plt.figure()
    plt.plot(xplot,f2(xplot),'g--',lw=1,label='interpolation')
    plt.plot(x,OPL_measured,'bo',label='From OPL table')
    plt.plot(xnew,ynew,'r.',label='Used motor positions')
    plt.xlabel("Wavelength [nm]")
    plt.ylabel("OPL opt [qc]")
    plt.legend()
    plt.show()
    OPL_array = np.array(f2(xnew)) # float64, in ms
    return OPL_array
    
def setShutterArray(wls):
    # Create a settings object
    settings = sg.UserSettings()
    
    # Load the previously used values, if any
    shutterPath = settings.get('shutterPath', 'S:/DHM 1087/lace3018/PDHM_automated_acquisition/tables/Archive/Table_shutter_vide.txt')
    
    layout = [
        [sg.Text('Select recent shutter table',size=(30,1)),sg.InputText(key='-FILE-'),sg.FileBrowse()],
        [sg.Submit(), sg.Cancel()]]
    window = sg.Window('Select shutter Table', layout)
    event, values = window.read()
    window.close()
    shutterPath = values['-FILE-']
    
    # Shutter speed and interpolation
    shutter_measured = np.loadtxt(shutterPath,skiprows=1).T[2]
    shutter_measured = shutter_measured - 0.2*shutter_measured
    x = np.loadtxt(shutterPath,skiprows=1).T[0]
    f = interp1d(x,shutter_measured,kind='linear')
    xnew = np.linspace(wls[0]/1000,wls[-1]/1000,len(wls))
    ynew = f(xnew)
    plt.figure()
    plt.plot(x,shutter_measured,'bo',label='From measured optimal shutter speeds')
    plt.plot(xnew,ynew,'r.',label='Used shutters for chosen wavelengths')
    plt.xlabel("Wavelength [nm]")
    plt.ylabel("Shutter [ms]")
    plt.legend()
    plt.show()
    shutter_array = np.array(f(xnew)) # float64, in ms
    return shutter_array

def setObject():
    selection = ('cell_chamber','chamlide_cell_chamber','phase_target','reference')
    settings = sg.UserSettings()
    selected_option = settings.get('selected_option', selection[0])
    layout = [
        [sg.Listbox(['Cell culture chamber','Chamlide','Phase target','Air (for reference holograms)'], size=(60,4), enable_events=False, key='fac',default_values=[selected_option])],
        [sg.Submit(), sg.Cancel()]]
        
    # Create the prompt window
    window = sg.Window('Object', layout)
    
    while True:
        event, values = window.read()
        if event == 'Submit':
            # Save the values to the UserSettings object
            settings.set('selected_option', values['fac'][0])
            # Print the values for testing
            print(values)
            break
        if event == 'Cancel':
            window.close()
            sys.exit()
    
    # Close the window
    window.close()
    
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
        
    return sample
    
def setMotorSweepParameters():
    layout = [
        [sg.Text('Enter the step value (in µm):')],
        [sg.InputText(default_text='50', key='-STEP-')],
        [sg.Text('Enter the half interval value (in µm):')],
        [sg.InputText(default_text='300', key='-INTERVAL-')],
        [sg.Button('Submit'), sg.Button('Cancel')]
    ]
    
    window = sg.Window('Motor Values', layout)
    
    while True:
        event, values = window.read()
        if event in (None, 'Cancel'):
            break
        elif event == 'Submit':
            step = float(values['-STEP-'])
            half_interval = float(values['-INTERVAL-'])
            print(f'Step value: {step} µm')
            print(f'Interval value: {half_interval} µm')
            break
    
    window.close()
    
    MO = setMicroscopeObjective()
    wavelengths = setWavelengthArray('P')
    N = len(wavelengths)
    OPL_array = setOPLarray(wavelengths)
    shutter_array = setShutterArray(wavelengths)
    
    date=datetime.today().strftime('%Y%m%d')
    path = Path(r'\\172.16.1.103\data\DHM 1087\lace3018\PDHM_automated_acquisition\tables\%s'%(date))
    pathlog=Path(r'\\172.16.1.103\data\DHM 1087\lace3018\PDHM_automated_acquisition\tables\%s\Log'%(date))
    isExist=os.path.exists(pathlog)
    if not isExist:
        os.makedirs(pathlog)
        
        
    return path,MO,wavelengths,N,OPL_array,shutter_array,half_interval,step