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
import modules.displayPlots as dp
import time
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import tempfile
import tifffile
import os
from scipy.interpolate import UnivariateSpline


def is_directory_empty(dir_path):
    """Return True if directory is empty, False otherwise."""
    return not bool(os.listdir(dir_path))


def uniquify_top_directory(base_path):
    """
    Returns a unique directory path. If "1" exists and is empty, it returns path of "1". 
    If "1" exists and is not empty, it checks "2", and so on.
    If a directory doesn't exist, it creates the directory before returning its path.
    """
    counter = 1
    while True:
        current_dir_path = os.path.join(base_path, str(counter))
        if not os.path.exists(current_dir_path) or is_directory_empty(current_dir_path):
            if not os.path.exists(current_dir_path):
                os.makedirs(current_dir_path)
            return current_dir_path
        counter += 1


def process_OPL(position, contrast, wavelength, path_save, process):
    if process==True:
        # Compute the derivatives and use them to remove outliers
        first_derivative = np.gradient(contrast)
        second_derivative = np.gradient(first_derivative)
        outlier_indices = np.where((second_derivative) > 0.1)
        position_no_outliers = np.delete(position, outlier_indices)
        contrast_no_outliers = np.delete(contrast, outlier_indices)
        
        # Remove first and last points to get rid of edge effects
        position_no_outliers = position_no_outliers[1:-1]
        contrast_no_outliers = contrast_no_outliers[1:-1]
    
        # Interpolate the data using cubic spline
        k = min(4, len(position_no_outliers) - 1)
        spline = UnivariateSpline(position_no_outliers, contrast_no_outliers, k=k)
        new_position = np.linspace(position_no_outliers.min(), position_no_outliers.max(), 1000)
        interpolated_contrast = spline(new_position)
    
        # Plot the data
        plt.figure()
        plt.plot(motor.qc2um(position), contrast, 'bo')
        plt.plot(motor.qc2um(position_no_outliers), contrast_no_outliers, ls = 'none', marker = 'o', markersize=5, markerfacecolor='none', markeredgecolor='g')
        plt.plot(motor.qc2um(new_position), interpolated_contrast, 'g--')
        
        # Use the maximum contrast to find the corresponding position
        optimal_OPL = new_position[np.argmax(interpolated_contrast)]
        plt.axvline(x=motor.qc2um(optimal_OPL), color='r', linestyle='--')
    
        # Customize the plot
        plt.ylabel('Contrast')
        plt.xlabel('Position [um]')
        plt.title(f'{wavelength} pm')
        plt.grid(True)
        
        plt.savefig(f"{path_save}\Log\opl_curve_{str(round(wavelength))}_pm.png")
        np.savetxt(f"{path_save}\Log\opl_curve_{str(round(wavelength))}pm.txt",np.vstack((position,contrast)).T,header='position [qc] \t contrast [-]')
        plt.close()
    else:
        # Plot the data
        plt.figure()
        plt.plot(motor.qc2um(position), contrast, 'k-')
        
        # Use the maximum contrast to find the corresponding position
        optimal_OPL = position[np.argmax(contrast)]
        plt.axvline(x=motor.qc2um(optimal_OPL), color='r', linestyle='--')
    
        # Customize the plot
        plt.ylabel('Contrast')
        plt.xlabel('Position [um]')
        plt.title(f'{wavelength} pm')
        plt.grid(True)
        
        plt.savefig(f"{path_save}\Log\opl_curve_{str(round(wavelength))}_pm.png")
        np.savetxt(f"{path_save}\Log\opl_curve_{str(round(wavelength))}pm.txt",np.vstack((position,contrast)).T,header='position [qc] \t contrast [-]')
        plt.close()
        
    
    return optimal_OPL


def getOPLTable():  
    '''
    Generates and save optimal OPL table for given sample.
    '''

    laser.LaserCheck()
    laser.EmissionOn()
    laser.setAmplitude(100)
        
    host = koala.KoalaLogin()
    
    RFSwitchState=laser.readRFSwitch()
    
    optimal_OPL_list=[]  
    sample = Inputs.setObject()
    MO,wls,OPL_array,shutter_array,interval_coarse,step_coarse=Inputs.setMotorSweepParameters()
    today = datetime.today().strftime('%Y%m%d')
     
    base_path = f"tables/{sample}/{MO}/OPL/{today}"
    save_path = uniquify_top_directory(base_path)
    log_path = os.path.join(save_path, "Log")
    
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    
    # Determine an offset by making a sweep around the initial guess
    offset_found = False
    while not offset_found:
        initial_wl = wls[int(len(wls)/2)]  # Choose a representative wavelength
        initial_OPL_guess = OPL_array[int(len(wls)/2)]  # Choose a representative OPL guess
        interval_sweep = interval_coarse
        step_sweep = step_coarse
    
        finer_sweep = False
        while not offset_found:
            pos, contrast, found_OPL = motor.balanceInterferometer(host, initial_wl, initial_OPL_guess, shutter_array[int(len(wls)/2)], save_path, interval_sweep/2, step_sweep)
            dp.plotOPLcurves(pos, contrast, 'temp.png')
            response = Inputs.askForConfirmation('temp.png')
    
            if response == 'Yes':
                finer_sweep_required = Inputs.askForFinerSweep()
                
                if finer_sweep_required == 'Yes':
                    initial_OPL_guess = found_OPL  # Update the initial OPL guess
                    interval_sweep, step_sweep = Inputs.askForFinerSweepParameters()
                    finer_sweep = True
                else:
                    offset_found = True
            else:
                if finer_sweep:  # If a finer sweep was done, and no peak was found, ask for wider interval and step
                    interval_sweep, step_sweep = Inputs.askForNewSweepParameters()
                else:  # If no peak was found in the coarse sweep, repeat the coarse sweep with wider parameters
                    interval_coarse, step_coarse = Inputs.askForNewSweepParameters()
                    interval_sweep = interval_coarse
                    step_sweep = step_coarse
      
    dp.close()
    
    # Ask for fine sweep parameters
    interval_fine, step_fine = Inputs.askForFinerSweepParametersLoop()

    offset_diffs = [found_OPL - OPL_array[int(len(wls)/2)]]  # A list to store all offset differences.
    
    for wl,i in zip(wls,range(0,len(wls))):
        if laser.check_for_crystal_switch(wl, RFSwitchState) == True:
            laser.switchCrystal(RFSwitchState)
            RFSwitchState = 1
        
        laser.setWavelength(wl)
        
        # Adjust the OPL guess with the current average offset
        adjusted_OPL_guess = OPL_array[i] + np.mean(offset_diffs) if offset_diffs else OPL_array[i]

        # Balance the interferometer
        position, contrast, _ = motor.balanceInterferometer(host, wl, adjusted_OPL_guess, shutter_array[i], save_path, interval_fine/2, step_fine)    
        
        # Process the result, plot and find optimal OPL
        optimal_OPL = process_OPL(position, contrast, wl, save_path, process=True)   
        
        # Find the difference between the optimal OPL and the adjusted OPL guess
        offset_diff = optimal_OPL - OPL_array[i]

        # Append the offset difference to the list
        offset_diffs.append(offset_diff)
    
        optimal_OPL_list.append(optimal_OPL)
        
        # Open the image file using the default associated program
        os.startfile(f"{log_path}\opl_curve_{str(round(wl))}_pm.png")
            
    unsatisfactory_wavelengths = Inputs.show_wavelengths_for_verification(wls)
    print(unsatisfactory_wavelengths)
    
    for wl
    
    # Save OPL table  
    optimal_OPL_list = np.asarray(optimal_OPL_list)
    filename = f"table_{int(len(wls))}points.txt"
    np.savetxt(os.path.join(save_path, filename), np.vstack((wls/1000, optimal_OPL_list)).T, header='wavelength [nm] \t optimal OPR [qc]')
    
    laser.RFPowerOff()
    time.sleep(0.3)
    laser.RFSwitch(RFSwitchState)
    time.sleep(0.3)  
    
    laser.CloseAll()
    
    host.Logout()


def getOPLTableRough():  
    '''
    Generates and save optimal OPL table for given sample.

    Parameters
    ----------
    fromMain : Bool, optional
        This option must be set to True if the function is called from the 
        main PDHM code, this will use the Koala host from the main. If the 
        function is called from another script, it is set to False. The 
        default is False.
    host_from_main : TYPE, optional
        If the function is called from the main code, this argument passes the 
        Koala host variable here. The default is None.

    Returns
    -------
    None.

    '''

    laser.LaserCheck()
    laser.EmissionOn()
    laser.setAmplitude(100)
        
    host = koala.KoalaLogin()
    
    RFSwitchState=laser.readRFSwitch()
    
    optimal_OPL_list=[]  
    sample = Inputs.setObject()
    MO = Inputs.setMicroscopeObjective()
    wls = Inputs.setWavelengthArray('P')
    shutter_array = Inputs.setShutterArray(wls)
    today = datetime.today().strftime('%Y%m%d')
     
    base_path = f"tables/{sample}/{MO}/OPL/{today}"
    save_path = uniquify_top_directory(base_path)
    log_path = os.path.join(save_path, "Log")
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    
    center = motor.findCenterPosition(host)
    
    for wl,i in zip(wls,range(0,len(wls))):
        if laser.check_for_crystal_switch(wl, RFSwitchState) == True:
            laser.switchCrystal(RFSwitchState)
            RFSwitchState = 1
        
        laser.setWavelength(wl)

        # Balance the interferometer
        position, contrast, optimal_OPL = motor.balanceInterferometer(host, wl, center, shutter_array[i], save_path, 1000, 100)    # Process the result, plot and find optimal OPL
        process_OPL(position, contrast, wl, save_path, process=False)  
    
        optimal_OPL_list.append(optimal_OPL)
        
    # Save OPL table  
    optimal_OPL_list = np.asarray(optimal_OPL_list)
    filename = f"table_{int(len(wls))}points_rough.txt"
    np.savetxt(os.path.join(save_path, filename), np.vstack((wls/1000, optimal_OPL_list)).T, header='wavelength [nm] \t optimal OPR [qc]')
    
    laser.RFPowerOff()
    time.sleep(0.3)
    laser.RFSwitch(RFSwitchState)
    time.sleep(0.3)  
    
    laser.CloseAll()
    
    host.Logout()


def getShutterTable():    
    laser.LaserCheck()
    laser.EmissionOn()
    laser.setAmplitude(100)

    host = koala.KoalaLogin()
        
    RFSwitchState=laser.readRFSwitch()
    
    sample = Inputs.setObject()
    MO,wls,OPL_array=Inputs.setShutterSweepParameters()
    
    optimal_shutter_list = []
    for wl,i in zip(wls,range(len(wls))):
        if laser.check_for_crystal_switch(wl, RFSwitchState) == True:
            laser.switchCrystal(RFSwitchState)
            RFSwitchState = 1
        
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

    # Save shutter table      
    base_path = f"tables/{sample}/{MO}/shutter"
    save_path = uniquify_top_directory(base_path)
        
    optimal_shutter_list=np.asarray(optimal_shutter_list)
    filename = f"table_{int(len(wls))}points.txt"
    np.savetxt(os.path.join(save_path, filename),np.vstack((wls/1000,optimal_shutter_list)).T,header='wavelength [nm] \t shutter speed [ms]')
    
    laser.RFPowerOff()
    time.sleep(0.3)
    laser.RFSwitch(RFSwitchState)
    time.sleep(0.3)    
    
    laser.CloseAll()
    
    host.Logout()