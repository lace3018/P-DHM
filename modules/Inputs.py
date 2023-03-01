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
import displayPlots as dp
import os

sg.theme('DefaultNoMoreNagging')


def getUpdateOPLChoice():
    '''
    This function creates a GUI window to ask the user whether they want to update the OPL table. The function returns a boolean value indicating the user's choice. 

    Returns
    -------
    update_opl : BOOL
    '''
    try:
        update_opl = False
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
    except Exception as e:
        print(f"An error occurred while selecting wheter or not to update the OPL table: {str(e)}")


def setupExperiment():
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
        if values[0]==True:
            MonoOrPoly='P'
        else:
            MonoOrPoly='M'
        window.close()
        
        # Set up all experiment parameters
        MO = setMicroscopeObjective()  
        userID,saveFolder,saveSubFolder = setSavingParameters()                   
        wavelengths = setWavelengthArray(MonoOrPoly)       
        path,pathlog = setupPath(userID,'RawData',datetime.today().strftime('%Y%m%d'),MO,saveFolder,saveSubFolder)
        OPL_array = setOPLarray(wavelengths)
        shutter_array = setShutterArray(wavelengths)
        
        np.savetxt(str(pathlog)+'\wavelengths.txt',wavelengths)
        
        return path,wavelengths,OPL_array,shutter_array
    
    except Exception as e:
        print(f"An error occurred while setting up the experiment: {str(e)}")


def setMicroscopeObjective():
    '''
    Displays a GUI window to allow the user to select a microscope magnification, saves the chosen
    magnification in the user settings, and returns the chosen magnification string.

    Returns
    -------
    MO : str
        Microscope objective magnification.

    '''
    try:
        settings = sg.UserSettings()
        magnification = settings.get('-MAGNIFICATION-', '20x')
        
        layout = [
            [sg.Text('Select microscope magnification:')],
            [sg.Radio('10x', 'MAGNIFICATION', key='-10X-', default=magnification=='10x')],
            [sg.Radio('20x', 'MAGNIFICATION', key='-20X-', default=magnification=='20x')],
            [sg.Radio('40x', 'MAGNIFICATION', key='-40X-', default=magnification=='40x')],
            [sg.Radio('100x', 'MAGNIFICATION', key='-100X-', default=magnification=='100x')],
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
                settings['-MAGNIFICATION-'] = MO
                break   
        window.close()
        
        return MO
    except Exception as e:
        print(f"An error occurred while setting up the microscope objective: {str(e)}")
        
        
def setSavingParameters():
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
    try:
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
                break
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
    except Exception as e:
        print(f"An error occurred while selecting the saving parameters: {str(e)}")

def setVideoParameters():
    '''
    Generates user interface window for video parameters

    Returns
    -------
    frameRate : int
        Video frame rate [im/min].
    maxtime : int
        Number of minutes after which acquisition is terminated. [min]

    '''
    try:
        # Set up the user settings object
        settings = sg.UserSettings()
        
        # Define default values for the inputs
        default_frameRate = settings.get('frameRate', '1')
        default_maxTime = settings.get('maxTime', '180')
        
        layout = [
            [sg.Text('Video frame rate [im/min] (integers only)',size=(30,1)),sg.InputText(default_text=default_frameRate, key = 'frameRate')],
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
                break
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
        
        frameRate = int(frameRate)/60   # TODO : changer la variable pour que ce soit un vrai framerate ou changer le nom en conséquence
        maxTime = int(maxTime)*60
        
        return frameRate,maxTime
    except Exception as e:
        print(f"An error occurred while setting the video parameters: {str(e)}")

def setWavelengthArray(MonoOrPoly):
    '''
    Generates user interface window for selecting the wavelengths. Returns a
    wavelength array containing all the wavelengths that are going to be used
    for the P-DHM loop.

    Parameters
    ----------
    MonoOrPoly : str
        'M' for monochromatic and 'P' for polychromatic.

    Returns
    -------
    wls_array : ndarray
        wavelength array.

    '''
    try:
        if MonoOrPoly=='P':
            
            # Set up the user settings object
            settings = sg.UserSettings()
            
            # Define default values for the inputs
            default_n = settings.get('num_values', '36')
            default_min_wl = settings.get('min_value', '500')
            default_max_wl = settings.get('max_value', '850')
            
            layout = [
            [sg.Text('Number of wavelengths: '), sg.Input(key='num_values',default_text=default_n)],
            [sg.Text('Minimum wavelength: '), sg.Slider(range=(500, 850), orientation='h', size=(20, 15), default_value=default_min_wl, key='min_value')],
            [sg.Text('Maximum wavelength: '), sg.Slider(range=(500, 850), orientation='h', size=(20, 15), default_value=850, key='max_value')],
            [sg.Text('Add a wavelength to the array? [nm]',size=(30,1)),sg.InputText(default_text='No',key='added_wl')],
            [sg.Submit(), sg.Cancel()]
            ]
            
            # Create the window
            window = sg.Window('Wavelengths selection -- Polychromatic acquisition', layout)
              
            # Loop until the user closes or submits the window
            while True:
                event, values = window.read()
                if event in (None, 'Cancel'):
                    # If the user cancels, return the default values
                    num_values = default_n
                    min_value = default_min_wl
                    max_value = default_max_wl
                    break
                elif event == 'Submit':
                    # If the user submits, update the user settings with the new values
                    settings['num_values'] = values['num_values']
                    settings['min_value'] = values['min_value']
                    settings['max_value'] = values['max_value']
                    # Return the new values
                    num_values = int(values['num_values'])
                    min_value = int(values['min_value']*1000)
                    max_value = int(values['max_value']*1000)
                    # Generate the array
                    step = (max_value - min_value) / (num_values - 1)
                    wls_array = [round(min_value + step * i) for i in range(num_values)]
                    break
            
            window.close()
            
            if values['added_wl']!='No':
                wl2add = int(float(values['added_wl'])*1000)
                ii = np.searchsorted(wls_array,wl2add)
                wls_array = np.insert(wls_array,ii,wl2add)
            
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
                    break
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
            
            wls_array = np.asarray(wls_array)
            return wls_array
    except Exception as e:
        print(f"An error occurred while setting the wavelength array: {str(e)}")
        

def setOPLarray(wls):
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
    try:
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
                break
            elif event == 'Submit':
                # If the user submits, update the user settings with the new values
                settings['oplPath'] = values['oplPath']
                # Return the new values
                oplPath = values['oplPath']
                break
        
        window.close()
        
        # Interpolation
        OPL_from_table = np.loadtxt(oplPath,skiprows=1).T
        interpolation_function = interp1d(OPL_from_table[0],OPL_from_table[1],kind='quadratic',bounds_error=False,fill_value=-10.)
        
        # Arrays to display the interpolation function on the graph
        wls_for_display = np.linspace(OPL_from_table[0][0],OPL_from_table[0][-1],1000)
        OPL_for_display = interpolation_function(wls_for_display)
        
        # Generating the OPL array
        OPL_array = np.array(interpolation_function(wls/1000))
        
        # Plot the OPL array and interpolation function
        dp.plot(wls_for_display,OPL_for_display*0.0507+25946,wls/1000,OPL_array*0.0507+25946,'OPL [$\mu$m]') # TODO : add if statement for the conversion into micrometers so that its valid for all the magnifications
        return OPL_array
    except Exception as e:
        print(f"An error occurred while setting the OPL array: {str(e)}")
        

def setShutterArray(wls):
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
    try:
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
                break
            elif event == 'Submit':
                # If the user submits, update the user settings with the new values
                settings['shutterPath'] = values['shutterPath']
                # Return the new values
                shutterPath = values['shutterPath']
                break
        
        window.close()
        
        # Interpolation
        shutter_from_table = np.loadtxt(shutterPath,skiprows=1).T
        interpolation_function = interp1d(shutter_from_table[0],shutter_from_table[1],kind='quadratic',bounds_error=False,fill_value=-10.)
        
        # Arrays to display the interpolation function on the graph
        wls_for_display = np.linspace(shutter_from_table[0][0],shutter_from_table[0][-1],1000)
        shutter_for_display = interpolation_function(wls_for_display)
        
        # Generating the shutter array
        shutter_array = np.array(interpolation_function(wls/1000))
        
        # Plot the shutter array and interpolation function
        dp.plot(wls_for_display,shutter_for_display,wls/1000,shutter_array,'Shutter speed [ms]')
        return shutter_array
    except Exception as e:
        print(f"An error occurred while setting the shutter array: {str(e)}")

def setObject():
    '''
    Selects the object that is under experiment.

    Returns
    -------
    sample : str
        Used to automatically name the OPL and shutter tables when generated.

    '''
    try:
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
    except Exception as e:
        print(f"An error occurred while selecting the object: {str(e)}") 
   
def setMotorSweepParameters():
    try:
        # Create a settings object
        settings = sg.UserSettings()
        
        # Define default values for the inputs
        default_step = settings.get('step', '50')
        default_interval = settings.get('interval', '600')
        
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
                break
            elif event == 'Submit':
                # If the user submits, update the user settings with the new values
                settings['step'] = values['step']
                settings['interval'] = values['interval']
                # Return the new values
                step = values['step']
                interval = values['interval']
                break
        
        window.close()
        
        MO = setMicroscopeObjective()
        wavelengths = setWavelengthArray('P')
        OPL_array = setOPLarray(wavelengths)
        shutter_array = setShutterArray(wavelengths)
        
        # Generate path
        setupPath('lace3018','PDHM_automated_acquisition','tables',datetime.today().strftime('%Y%m%d'),'','')
        date=datetime.today().strftime('%Y%m%d')
        path = Path(r'\\172.16.1.103\data\DHM 1087\lace3018\PDHM_automated_acquisition\tables\%s'%(date))
        pathlog=Path(r'\\172.16.1.103\data\DHM 1087\lace3018\PDHM_automated_acquisition\tables\%s\Log'%(date))
        isExist=os.path.exists(pathlog)
        if not isExist:
            os.makedirs(pathlog)
            
        return path,MO,wavelengths,OPL_array,shutter_array,interval,step
    
    except Exception as e:
        print(f"An error occurred while setting the motor sweep parameters: {str(e)}")


def setupPath(folder1,folder2,folder3,folder4,folder5,folder6):
    '''
    Sets up the folder structure for saving data and returns path to saving 
    location and log saving location
    '''
    try:
        path = Path(r'\\172.16.1.103\data\DHM 1087\%s\%s\%s\%s\%s\%s'%(folder1,folder2,folder3,folder4,folder5,folder6))
        pathlog=Path(r'\\172.16.1.103\data\DHM 1087\%s\%s\%s\%s\%s\%s\Log'%(folder1,folder2,folder3,folder4,folder5,folder6))
        isExist=os.path.exists(pathlog)
        if not isExist:
            os.makedirs(pathlog)
        
        return path,pathlog

    except Exception as e:
        print(f"An error occurred while setting up the path: {str(e)}")
