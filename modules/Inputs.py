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
from . import displayPlots as dp
import os
import sys
import math

sg.theme('DefaultNoMoreNagging')


def setupExperiment(host):
    '''
    This function sets up the parameters for a P-DHM experiment, including 
    wavelengths, OPL array, and shutter array. It prompts the user to choose 
    between monochromatic and polychromatic light sources and returns a path 
    to the data folder, an array of wavelengths, an array of OPL values, and 
    an array of shutter values.

    Returns
    -------
    path : str
        path to the data folder.
    wavelengths : ndarray
        an array of wavelengths.
    OPL_array : ndarray
        an array of OPL values.
    shutter_array : ndarray
        an array of shutter values.

    '''
    try:
        layout = [[sg.T("         "), sg.Radio('Polychromatic', "RADIO1", default=True)],
                  [sg.T("         "), sg.Radio('Monochromatic', "RADIO1", default=False)],
                  [sg.Submit(), sg.Cancel()]]
    
        window = sg.Window('Parameters 1', layout, size=(300,300))
        event, values = window.read()
        if event in (None, 'Cancel'):
            window.close()
            host.Logout()
            print('Logged out from Koala')
            sys.exit()
        if values[0]==True:
            MonoOrPoly='P'
        else:
            MonoOrPoly='M'
        window.close()
        
        # Set up all experiment parameters
        MO = setMicroscopeObjective(host)  
        userID,saveFolder,saveSubFolder = setSavingParameters(host)                   
        wavelengths = setWavelengthArray(MonoOrPoly, host)       
        path,pathlog = setupPath(userID,'RawData',datetime.today().strftime('%Y%m%d'),MO,saveFolder,saveSubFolder)
        OPL_array, oplPath = setOPLarray(wavelengths,host)
        shutter_array, shutterPath = setShutterArray(wavelengths, host)
        
        # Load configuration in Koala
        configID = {'5x':131, '10x': 132, '20x': 133, '40x': 134, '63x': 135, '100x': 135} # Create a dictionary to map MOs to IDs
        # host.OpenConfig(configID[MO])
        # print('MO config set in Koala')
        
        np.savetxt(str(pathlog)+'\wavelengths.txt',wavelengths)
        
        return path,wavelengths,OPL_array,shutter_array,oplPath,shutterPath
    
    except Exception as e:
        print(f"An error occurred while setting up the experiment: {str(e)}")
        host.Logout()
        print('Logged out from Koala')
        sys.exit()


def setMicroscopeObjective(host):
    '''
    Displays a GUI window to allow the user to select a microscope magnification, saves the chosen
    magnification in the user settings, and returns the chosen magnification string.
    '''
    settings = sg.UserSettings()
    magnification = settings.get('-MAGNIFICATION-', '20x')
    
    layout = [
        [sg.Text('Select microscope magnification:')],
        [sg.Radio('5x', 'MAGNIFICATION', key='-5X-', default=magnification=='5x')],
        [sg.Radio('10x', 'MAGNIFICATION', key='-10X-', default=magnification=='10x')],
        [sg.Radio('20x', 'MAGNIFICATION', key='-20X-', default=magnification=='20x')],
        [sg.Radio('40x', 'MAGNIFICATION', key='-40X-', default=magnification=='40x')],
        [sg.Radio('63x', 'MAGNIFICATION', key='-63X-', default=magnification=='63x')],  # Add this line
        [sg.Radio('100x', 'MAGNIFICATION', key='-100X-', default=magnification=='100x')],
        [sg.Button('Submit'), sg.Button('Cancel')]
    ]
    
    window = sg.Window('Microscope Magnification Selector', layout)
    
    while True:
        event, values = window.read()
        if event in (None, 'Cancel'):
            window.close()
            host.Logout()
            print('Logged out from Koala')
            sys.exit()
        elif event == 'Submit':
            if values['-10X-']:
                MO = '10x'
            elif values['-5X-']:
                MO = '5x'
            elif values['-20X-']:
                MO = '20x'
            elif values['-40X-']:
                MO = '40x'
            elif values['-63X-']:
                MO = '63x'
            else:
                MO = '100x'
            settings['-MAGNIFICATION-'] = MO
            break
    window.close()
    
    return MO

        
        
def setSavingParameters(host):
    '''
    Displays a GUI to allow the user to set saving parameters for an experiment, 
    and remembers the previous values selected by the user.
    
    Returns
    -------
    userID : str
        user identification for saving under the right username.
    saveFolder : str
        name of the folder where the data are going to be saved.
    saveSubFolder : str
        name of the subfolder where the data are going to be saved (facultative).

    '''
    # Set up the user settings object
    settings = sg.UserSettings()
    
    # Define default values for the inputs
    default_userID = settings.get('userID', 'lace3018')
    default_saveFolder = settings.get('saveFolder', 'RatNeurons')
    default_saveSubFolder = settings.get('saveSubFolder', '')
    
    # Define the layout of the window
    layout = [
        [sg.Text('Identification', size =(30, 1)), sg.InputText(default_text=default_userID, key='userID')],
        [sg.Text('Save folder', size =(30, 1)), sg.InputText(default_text=default_saveFolder, key='saveFolder')],
        [sg.Text('Save subfolder (facult.)', size =(30, 1)), sg.InputText(default_text=default_saveSubFolder, key='saveSubFolder')],
        [sg.Submit(), sg.Cancel()]]
    
    # Create the window
    window = sg.Window('Saving parameters', layout)
    
    # Loop until the user closes or submits the window
    while True:
        event, values = window.read()
        if event in (None, 'Cancel'):
            # If the user cancels, return the default values
            userID = default_userID
            saveFolder = default_saveFolder
            saveSubFolder = default_saveSubFolder
            window.close()
            host.Logout()
            print('Logged out from Koala')
            sys.exit()
        elif event == 'Submit':
            # If the user submits, update the user settings with the new values
            settings['userID'] = values['userID']
            settings['saveFolder'] = values['saveFolder']
            settings['saveSubFolder'] = values['saveSubFolder']
            # Return the new values
            userID = values['userID']
            saveFolder = values['saveFolder']
            saveSubFolder = values['saveSubFolder']
            break
        
    # Close the window
    window.close()
    
    return userID, saveFolder, saveSubFolder
    

def setVideoParameters(host):
    '''
    Generates user interface window for video parameters

    Returns
    -------
    frameRate : int
        Video frame rate [im/min].
    maxtime : int
        Number of minutes after which acquisition is terminated. [min]

    '''
    # Set up the user settings object
    settings = sg.UserSettings()
    
    # Define default values for the inputs
    default_frameRate = settings.get('frameRate', '1')
    default_maxTime = settings.get('maxTime', '180')
    
    layout = [
        [sg.Text('Video frame rate [im/min]',size=(30,1)),sg.InputText(default_text=default_frameRate, key = 'frameRate')],
        [sg.Text('Stop acquisition after [min] (integers only)',size=(30,1)),sg.InputText(default_text=default_maxTime, key = 'maxTime')],
        [sg.Submit(), sg.Cancel()]
    ]
    
    # Create the window
    window = sg.Window('Video parameters', layout)
      
    # Loop until the user closes or submits the window
    while True:
        event, values = window.read()
        if event in (None, 'Cancel'):
            # If the user cancels, return the default values
            frameRate = default_frameRate
            maxTime = default_maxTime
            window.close()
            host.Logout()
            print('Logged out from Koala')
            sys.exit()
        elif event == 'Submit':
            # If the user submits, update the user settings with the new values
            settings['frameRate'] = values['frameRate']
            settings['maxTime'] = values['maxTime']
            # Return the new values
            frameRate = values['frameRate']
            maxTime = values['maxTime']
            break
        
    # Close the window
    window.close()
    
    frameRate = float(frameRate)/60   # TODO : changer la variable pour que ce soit un vrai framerate ou changer le nom en conséquence
    maxTime = (int(maxTime))*60
    
    return frameRate,maxTime


def setWavelengthArray(MonoOrPoly, host, custom_wavelengths=None):
    '''
    Generates user interface window for selecting the wavelengths or allows the use of a custom wavelengths array. 
    Returns a wavelength array containing all the wavelengths that are going to be used for the P-DHM loop.

    Parameters
    ----------
    MonoOrPoly : str
        'M' for monochromatic and 'P' for polychromatic.
    host : object
        The host system interface object (e.g., for logging or system calls).
    custom_wavelengths : list, optional
        A list of custom wavelengths provided by the user. If None, the GUI will be used to select wavelengths.

    Returns
    -------
    wls_array : ndarray
        Wavelength array.

    '''
    if custom_wavelengths is not None:
        # Convert the custom wavelengths from nm to the desired unit if necessary, and ensure they're in a numpy array
        wls_array = np.asarray(custom_wavelengths).astype('float')
        print(wls_array)
        return wls_array

    if MonoOrPoly == 'P':
        
        # Set up the user settings object
        settings = sg.UserSettings()
        
        # Define default values for the inputs
        default_n = settings.get('num_values', '36')
        default_min_wl = settings.get('min_value', '500')
        default_max_wl = settings.get('max_value', '850')
        
        layout = [
            [sg.Text('Number of wavelengths: '), sg.Input(key='num_values', default_text=default_n)],
            [sg.Text('Minimum wavelength: '), sg.Slider(range=(500, 850), orientation='h', size=(20, 15), default_value=default_min_wl, key='min_value')],
            [sg.Text('Maximum wavelength: '), sg.Slider(range=(500, 850), orientation='h', size=(20, 15), default_value=default_max_wl, key='max_value')],
            [sg.Text('Add a wavelength to the array? [nm]', size=(30,1)), sg.InputText(default_text='No', key='added_wl')],
            [sg.Text('Or enter custom wavelengths (comma-separated, e.g., 600,610,620):'), sg.InputText(key='custom_wavelengths')],
            [sg.Submit(), sg.Cancel()]
        ]
        
        # Create the window
        window = sg.Window('Wavelengths selection -- Polychromatic acquisition', layout)
          
        # Loop until the user closes or submits the window
        while True:
            event, values = window.read()
            if event in (None, 'Cancel'):
                # If the user cancels, return the default values
                window.close()
                host.Logout()
                print('Logged out from Koala')
                sys.exit()
            elif event == 'Submit':
                # If the user submits, check for custom wavelengths input
                if values['custom_wavelengths']:
                    custom_wavelengths_str = values['custom_wavelengths']
                    wls_array = np.array([int(float(wl)*1000) for wl in custom_wavelengths_str.split(',')]).astype('float')
                else:
                    # Update the user settings with the new values
                    settings['num_values'] = values['num_values']
                    settings['min_value'] = values['min_value']
                    settings['max_value'] = values['max_value']
                    # Generate the array based on the GUI inputs
                    num_values = int(values['num_values'])
                    min_value = int(values['min_value'] * 1000)
                    max_value = int(values['max_value'] * 1000)
                    if num_values == 1:
                        wls_array = [min_value]
                    else:
                        step = (max_value - min_value) / (num_values - 1)
                        wls_array = [round(min_value + step * i) for i in range(num_values)]
                
                break
        
        window.close()
        
        # If an additional wavelength was added via the original method
        if values.get('added_wl') and values['added_wl'] != 'No':
            wl2add = int(float(values['added_wl']) * 1000)
            ii = np.searchsorted(wls_array, wl2add)
            wls_array = np.insert(wls_array, ii, wl2add)
            
        wls_array = np.asarray(wls_array).astype('float')
        print(wls_array)
        return wls_array
        
    else:
        # Set up the user settings object
        settings = sg.UserSettings()
        
        # Define default values for the inputs
        default_n = settings.get('num_values', '36')
        default_wl = settings.get('wavelength', '666')
        
        layout = [
            [sg.Text('Select the wavelength (nm):')],
            [sg.Slider(range=(500, 850), default_value=default_wl, orientation='h', size=(20,15), key='wavelength')],
            [sg.Text('Enter the number of repetitions:')],
            [sg.Input(default_text=default_n, key='num_values')],
            [sg.Button('Submit'), sg.Button('Cancel')]
        ]
        
        window = sg.Window('Wavelength Selector', layout)
        
        # Loop until the user closes or submits the window
        while True:
            event, values = window.read()
            if event in (None, 'Cancel'):
                # If the user cancels, return the default values
                num_values = default_n
                wavelength = default_wl
                window.close()
                host.Logout()
                print('Logged out from Koala')
                sys.exit()
            elif event == 'Submit':
                # If the user submits, update the user settings with the new values
                settings['num_values'] = values['num_values']
                settings['wavelength'] = values['wavelength']
                # Return the new values
                num_values = int(values['num_values'])
                wavelength = int(values['wavelength']*1000)
                # Generate the array
                wls_array = [wavelength] * num_values
                break
        
        window.close()
        
        wls_array = np.asarray(wls_array).astype('float')
        return wls_array



def setOPLarray(wls, host):
    '''
    Sets the optical path length (OPL) array by asking the user to select a txt 
    file containing the optimal OPL values for the present acquisition.

    Parameters
    ----------
    wls : ndarray
        array of wavelengths.

    Returns
    -------
    OPL_array : ndarray
        array of OPLs.

    '''
    # Create a settings object
    settings = sg.UserSettings()
    
    # Define default values for the inputs
    default_oplPath = settings.get('oplPath', 'S:/DHM 1087/lace3018/PDHM_automated_acquisition/tables/Archive/OPL_table_vide_20X.txt')
    
    layout = [
        [sg.Text('Select recent OPL table',size=(30,1))],
        [sg.InputText(default_text=default_oplPath,key='oplPath'),sg.FileBrowse()],
        [sg.Submit(), sg.Cancel()]]
    
    window = sg.Window('Select OPL Table', layout)
    
    # Loop until the user closes or submits the window
    while True:
        event, values = window.read()
        if event in (None, 'Cancel'):
            # If the user cancels, return the default values
            oplPath = default_oplPath
            window.close()
            host.Logout()
            print('Logged out from Koala')
            sys.exit()
        elif event == 'Submit':
            # If the user submits, update the user settings with the new values
            settings['oplPath'] = values['oplPath']
            # Return the new values
            oplPath = values['oplPath']
            break
    
    window.close()
    
    # Interpolation
    OPL_from_table = np.loadtxt(oplPath,skiprows=1).T
    interpolation_function = interp1d(OPL_from_table[0],OPL_from_table[1],kind='linear',bounds_error=False,fill_value=-10.)
    
    # Arrays to display the interpolation function on the graph
    wls_for_display = np.linspace(OPL_from_table[0][0],OPL_from_table[0][-1],1000)
    OPL_for_display = interpolation_function(wls_for_display)
    
    # Generating the OPL array
    OPL_array = np.array(interpolation_function(wls/1000))
    
    # Plot the OPL array and interpolation function
    # dp.plotTable(wls_for_display,OPL_for_display*0.0507+25946,wls/1000,OPL_array*0.0507+25946,'OPL [$\mu$m]', path_log, 'oplTablePlot') # TODO : add if statement for the conversion into micrometers so that its valid for all the magnifications
    return OPL_array, oplPath
   

def setShutterArray(wls, host):
    '''
    Sets the shutter speed array by asking the user to select a txt 
    file containing the optimal shutter speed values for the present acquisition.

    Parameters
    ----------
    wls : ndarray
        array of wavelengths.

    Returns
    -------
    shutter_array : ndarray
        array of shutter speeds.

    '''
    # Create a settings object
    settings = sg.UserSettings()
    
    # Define default values for the inputs
    default_shutterPath = settings.get('shutterPath', 'S:/DHM 1087/lace3018/PDHM_automated_acquisition/tables/Archive/shutter_table_vide_20X.txt')
    
    layout = [
        [sg.Text('Select recent shutter speed table',size=(30,1))],
        [sg.InputText(default_text=default_shutterPath,key='shutterPath'),sg.FileBrowse()],
        [sg.Submit(), sg.Cancel()]]
    
    window = sg.Window('Select shutter speed table', layout)
    
    # Loop until the user closes or submits the window
    while True:
        event, values = window.read()
        if event in (None, 'Cancel'):
            # If the user cancels, return the default values
            shutterPath = default_shutterPath
            window.close()
            host.Logout()
            print('Logged out from Koala')
            sys.exit()
        elif event == 'Submit':
            # If the user submits, update the user settings with the new values
            settings['shutterPath'] = values['shutterPath']
            # Return the new values
            shutterPath = values['shutterPath']
            break
    
    window.close()
    
    # Interpolation
    shutter_from_table = np.loadtxt(shutterPath,skiprows=1).T
    interpolation_function = interp1d(shutter_from_table[0],shutter_from_table[1]*0.7,kind='linear',bounds_error=False,fill_value=-10.) #TODO: ne pas hardcoder le 95% du shutter
    
    # Arrays to display the interpolation function on the graph
    wls_for_display = np.linspace(shutter_from_table[0][0],shutter_from_table[0][-1],1000)
    shutter_for_display = interpolation_function(wls_for_display)
    
    # Generating the shutter array
    shutter_array = np.array(interpolation_function(wls/1000))
    
    # Plot the shutter array and interpolation function
    # dp.plotTable(wls_for_display,shutter_for_display,wls/1000,shutter_array,'Shutter speed [us]', path_log, 'shutterTablePlot')
    return shutter_array, shutterPath


def setObject(host):
    '''
    Selects the object that is under experiment.

    Returns
    -------
    sample : str
        Used to automatically name the OPL and shutter tables when generated.

    '''
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
            break
        if event == 'Cancel':
            window.close()
            host.Logout()
            print('Logged out from Koala')
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
   

def setupPath(folder1,folder2,folder3,folder4,folder5,folder6):
    '''
    Sets up the folder structure for saving data and returns path to saving 
    location and log saving location
    '''
    path = Path(r'\\172.16.1.103\data\DHM 1087\%s\%s\%s\%s\%s\%s'%(folder1,folder2,folder3,folder4,folder5,folder6))
    pathlog=Path(r'\\172.16.1.103\data\DHM 1087\%s\%s\%s\%s\%s\%s\Log'%(folder1,folder2,folder3,folder4,folder5,folder6))
    isExist=os.path.exists(pathlog)
    if not isExist:
        os.makedirs(pathlog)
    
    return path,pathlog

  
def setMotorSweepParameters(host):
    try:        
        MO = setMicroscopeObjective(host)
        wavelengths = setWavelengthArray('P', host)
        OPL_array,_ = setOPLarray(wavelengths,host)
        shutter_array,_ = setShutterArray(wavelengths, host)
        
        # Create a settings object
        settings = sg.UserSettings()
        
        # Define default values for the inputs
        default_step = settings.get('step', '15')
        default_interval = settings.get('interval', '700')
        
        layout = [
            [sg.Text('Enter the motor step (in µm):')],
            [sg.InputText(default_text=default_step, key='step')],
            [sg.Text('Enter the motor interval (in µm):')],
            [sg.InputText(default_text=default_interval, key='interval')],
            [sg.Button('Submit'), sg.Button('Cancel')]
        ]
        
        window = sg.Window('Motor sweep parameters', layout)
        
        # Loop until the user closes or submits the window
        while True:
            event, values = window.read()
            if event in (None, 'Cancel'):
                # If the user cancels, return the default values
                step = default_step
                interval = default_interval
                window.close()
                host.Logout()
                print('Logged out from Koala')
                sys.exit()
            elif event == 'Submit':
                # If the user submits, update the user settings with the new values
                settings['step'] = values['step']
                settings['interval'] = values['interval']
                # Return the new values
                step = values['step']
                interval = values['interval']
                break
        
        window.close()
        

        return MO,wavelengths,OPL_array,shutter_array,float(interval),float(step)
    
    except Exception as e:
        print(f"An error occurred while setting the motor sweep parameters: {str(e)}")
        sys.exit()


def askForConfirmation(latest_plot_path, host):
    layout = [[sg.Text("Was the peak found?")],
              [sg.Image(filename=latest_plot_path)],
              [sg.Button("Yes"), sg.Button("No")]]

    window = sg.Window("Peak Confirmation", layout)

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED:
            break
        if event == 'Yes':
            window.close()
            os.remove(latest_plot_path)  # Delete the temporary file after using it
            return 'Yes'
        elif event == 'No':
            window.close()
            os.remove(latest_plot_path)  # Delete the temporary file after using it
            return 'No'


def askForFinerSweep(host):
    layout = [[sg.Text('Do you want to perform a finer sweep?')],
              [sg.Button('Yes'), sg.Button('No')]]
    window = sg.Window('Finer Sweep Confirmation', layout)

    while True:  # Event Loop
        event, values = window.read()
        if event in ('Yes', 'No'):
            break
        elif event == sg.WINDOW_CLOSED:
            break

    window.close()
    return event


def askForNewSweepParameters(host):
    """
    Prompt the user to enter new sweep parameters.
    """

    layout = [
        [sg.Text('The optimal OPL was not found. Please enter larger interval.')],
        [sg.Text('Enter the coarse motor step (in µm):')],
        [sg.InputText(default_text='15', key='step')],
        [sg.Text('Enter the coarse motor interval (in µm):')],
        [sg.InputText(default_text='700', key='interval')],
        [sg.Button('Submit'), sg.Button('Cancel')]
    ]

    window = sg.Window('New Sweep Parameters', layout)

    # Loop until the user closes or submits the window
    while True:
        event, values = window.read()
        if event in (None, 'Cancel'):
            # If the user cancels, use default parameters
            step = 100
            interval = 2000
            host.Logout()
            print('Logged out from Koala')
            break
        elif event == 'Submit':
            # If the user submits, return the values
            step = values['step']
            interval = values['interval']
            break

    window.close()
    return float(interval), float(step)


def askForFinerSweepParameters(host):
    """
    Prompt the user to enter finer sweep parameters.
    """

    layout = [
        [sg.Text('Please enter reduced range with smaller step.')],
        [sg.Text('Enter the finer motor step (in µm):')],
        [sg.InputText(default_text='15', key='step')],
        [sg.Text('Enter the reduced motor interval (in µm):')],
        [sg.InputText(default_text='700', key='interval')],
        [sg.Button('Submit'), sg.Button('Cancel')]
    ]

    window = sg.Window('New Sweep Parameters', layout)

    # Loop until the user closes or submits the window
    while True:
        event, values = window.read()
        if event in (None, 'Cancel'):
            # If the user cancels, use default parameters
            step = 5
            interval = 100
            host.Logout()
            print('Logged out from Koala')
            break
        elif event == 'Submit':
            # If the user submits, return the values
            step = values['step']
            interval = values['interval']
            break

    window.close()
    return float(interval), float(step)

def askForFinerSweepParametersLoop(host):
    """
    Prompt the user to enter finer sweep parameters.
    """

    layout = [
        [sg.Text('Please enter desired range and step for the wavelength loop.')],
        [sg.Text('Enter the finer motor step (in µm):')],
        [sg.InputText(default_text='5', key='step')],
        [sg.Text('Enter the reduced motor interval (in µm):')],
        [sg.InputText(default_text='50', key='interval')],
        [sg.Button('Submit'), sg.Button('Cancel')]
    ]

    window = sg.Window('New Sweep Parameters', layout)

    # Loop until the user closes or submits the window
    while True:
        event, values = window.read()
        if event in (None, 'Cancel'):
            # If the user cancels, use default parameters
            step = 5
            interval = 50
            host.Logout()
            print('Logged out from Koala')
            break
        elif event == 'Submit':
            # If the user submits, return the values
            step = values['step']
            interval = values['interval']
            break

    window.close()
    return float(interval), float(step)

def setShutterSweepParameters(host):
    try:            
        MO = setMicroscopeObjective(host)
        wavelengths = setWavelengthArray('P', host)
        OPL_array,_ = setOPLarray(wavelengths,host)

        return MO,wavelengths,OPL_array
    
    except Exception as e:
        print(f"An error occurred while setting the motor sweep parameters: {str(e)}")
        sys.exit()


def select_OPL_or_shutter():
    # Layout definition
    layout = [
        [sg.Text("Which table to you want to produce?")],
        [sg.Button("OPL"), sg.Button("shutter")]
    ]

    # Create the window
    window = sg.Window("Choose Option", layout)

    # Event loop to process events and get the values of the inputs
    while True:
        event, values = window.read()
        if event in ("OPL", "shutter"):
            window.close()
            return event
        if event == sg.WINDOW_CLOSED:
            window.close()
            return None


def select_table_acquisition_type():
    # Layout definition
    layout = [
        [sg.Text("Select the type of table acquisition")],
        [sg.Button("Initial Rough Table (only if no previous data available)"), sg.Button("Precise Table (needs a pre-saved table of similar sample)"), sg.Button("Table Offset (fast option if pre-saved table of same sample available)")]
    ]

    # Create the window
    window = sg.Window("Choose Table Type", layout)

    event, values = window.read()
    window.close()
    return event


def show_wavelengths_for_verification(wls, host):
    screen_width, screen_height = 1920, 1080  # Screen dimensions
    max_elements_per_row = 10  # Maximum number of elements in a single row
    
    # Calculate the number of rows and columns to fit the screen
    num_elements = len(wls)
    num_columns = min(max_elements_per_row, math.ceil(math.sqrt(num_elements)))
    num_rows = math.ceil(num_elements / num_columns)

    # Header text
    rows = [[sg.Text("Check all unsatisfactory wavelengths")]]

    # Initialize row_elements and counter
    row_elements = []
    counter = 0

    # Add wavelengths with checkboxes
    for wl in wls:
        row_elements.extend([
            sg.Text(f"{round(wl)}"),
            sg.Checkbox('', key=str(wl))
        ])
        counter += 1

        # Check if the row is filled
        if counter % num_columns == 0:
            rows.append(row_elements)
            row_elements = []

    # Add remaining elements to the last row
    if row_elements:
        rows.append(row_elements)

    # Add OK and Cancel buttons
    rows.append([sg.Button('OK'), sg.Button('Cancel')])

    # Create the window
    window = sg.Window('Verify Wavelengths', rows, resizable=True)

    unsatisfactory_wls = []

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel':
            host.Logout()
            print('Logged out from Koala')
            break
        if event == 'OK':
            for wl_str, checkbox_value in values.items():
                if checkbox_value:
                    unsatisfactory_wls.append(float(wl_str))  # Convert back to float
            break

    window.close()
    return unsatisfactory_wls


def ask_for_center_position(wl, host):
    layout = [
        [sg.Text(f"Enter the center position in micrometers for {wl}:")],
        [sg.InputText(key='center_position')],
        [sg.Button("Submit"), sg.Button("Cancel")]
    ]
    
    window = sg.Window("Center Position Input", layout)
    
    while True:
        event, values = window.read()
        
        if event == sg.WIN_CLOSED or event == 'Cancel':
            window.close()
            host.Logout()
            print('Logged out from Koala')
            return None  # Return None if the window is closed or cancelled
        
        if event == 'Submit':
            try:
                center_position = float(values['center_position'])  # Convert to float
                window.close()
                return center_position  # Return the entered center position
            except ValueError:
                sg.popup_error("Please enter a valid number")  # Show error if not a valid number


def ask_for_shutter():
    # Layout definition
    layout = [
        [sg.Text("Do you want to measure a shutter table?")],
        [sg.Button("Yes"), sg.Button("No")]
    ]

    # Create the window
    window = sg.Window("Choose Option", layout)

    # Event loop to process events and get the value of input
    while True:
        event, values = window.read()
        
        # If user closes window or clicks "No"
        if event == sg.WIN_CLOSED or event == "No":
            window.close()
            return False
        # If user clicks "Yes"
        elif event == "Yes":
            window.close()
            return True
