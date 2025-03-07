# -*- coding: utf-8 -*-
"""
Created on Tue Aug  9 10:55:04 2022

Measure and save optical path length (OPL) position table for the motorized
part in the DHM reference arm.

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
    if not isinstance(process, bool):
        raise ValueError("process should be a boolean value")
    
    if len(position) == 0 or len(contrast) == 0:
        raise ValueError("position and contrast should be non-empty")
    
    if process:
        # Compute the derivatives and use them to remove outliers
        first_derivative = np.gradient(contrast)
        second_derivative = np.gradient(first_derivative)
        outlier_indices = np.where((second_derivative) > 0.1)
        position_no_outliers = np.delete(position, outlier_indices)
        contrast_no_outliers = np.delete(contrast, outlier_indices)
        
        # Check if arrays are not empty
        if len(position_no_outliers) == 0 or len(contrast_no_outliers) == 0:
            # Handle empty arrays (e.g., return a default value or skip processing)
            position_no_outliers = np.zeros(3)
            contrast_no_outliers = np.zeros(3)
        
        # Safely remove first and last points
        if len(position_no_outliers) > 2:
            position_no_outliers = position_no_outliers[1:-1]
            contrast_no_outliers = contrast_no_outliers[1:-1]
        
        # Determine the degree of the spline interpolation
        num_points = len(position_no_outliers)
        if num_points >= 4:
            k = 3  # Cubic spline
        elif num_points == 3:
            k = 2  # Quadratic spline
        elif num_points == 2:
            k = 1  # Linear spline
        else:
            k=1
            # Handle the case with less than 2 points
            position_no_outliers = np.zeros(3)
            contrast_no_outliers = np.zeros(3)
        
        # Interpolate the data using the determined degree of spline
        spline = UnivariateSpline(position_no_outliers, contrast_no_outliers, k=k, s=0.5)
        new_position = np.linspace(position_no_outliers.min(), position_no_outliers.max(), 1000)
        interpolated_contrast = spline(new_position)
    
        # Plot the data
        plt.figure()
        plt.plot(motor.qc2um(position), contrast, 'bo', alpha=0.3)
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
        
        plt.savefig(f"{path_save}\Log\opl_curve_{str(int(round(wavelength)))}_pm.png")
        np.savetxt(f"{path_save}\Log\opl_curve_{str(int(round(wavelength)))}pm.txt",np.vstack((position,contrast)).T,header='position [qc] \t contrast [-]')
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
        
        plt.savefig(f"{path_save}\Log\opl_curve_{str(int(round(wavelength)))}_pm.png")
        np.savetxt(f"{path_save}\Log\opl_curve_{str(int(round(wavelength)))}pm.txt",np.vstack((position,contrast)).T,header='position [qc] \t contrast [-]')
        plt.close()
        
    
    return optimal_OPL


def getOptimalPositions(wls, OPL_array, shutter_array, interval, step, save_path, log_path, host, specific_wls=None):
    
    optimal_OPL_list = []
    RFSwitchState=laser.readRFSwitch()
    
    # If specific_wls is provided, use it, else use the original wls
    wls_to_optimize = specific_wls if specific_wls else wls
    indices = np.nonzero(np.in1d(wls,specific_wls))[0] if specific_wls else range(0, len(wls))
    
    if RFSwitchState==1 and wls_to_optimize[0]<700000:
        laser.switchCrystal(RFSwitchState)
        RFSwitchState=0
    
    for wl,i in zip(wls_to_optimize, indices):
        if laser.check_for_crystal_switch(wl, RFSwitchState) == True:
            laser.switchCrystal(RFSwitchState)
            RFSwitchState = 1
        
        laser.setWavelength(wl)

        # Balance the interferometer
        position, contrast, _ = motor.balanceInterferometer(host, wl, OPL_array[i], shutter_array[i], save_path, interval/2, step)    
        
        # Process the result, plot and find optimal OPL
        optimal_OPL = process_OPL(position, contrast, wl, save_path, process=True)     
        optimal_OPL_list.append(optimal_OPL)
        
        # Open the image file using the default associated program
        # os.startfile(f"{log_path}\opl_curve_{str(round(wl))}_pm.png")
    os.startfile(log_path)

        
    return optimal_OPL_list


def determine_offset(wls, OPL_array, shutter_array, save_path, interval, step, host):
    # Determine an offset by making a sweep around the initial guess
    offset_found = False
    while not offset_found:
        initial_wl = wls[int(len(wls)/2)]  # Choose a representative wavelength
        initial_OPL_guess = OPL_array[int(len(wls)/2)]  # Choose a representative OPL guess
        interval_sweep = interval
        step_sweep = step
    
        finer_sweep = False
        while not offset_found:
            pos, contrast, found_OPL = motor.balanceInterferometer(host, initial_wl, initial_OPL_guess, shutter_array[int(len(wls)/2)], save_path, interval_sweep/2, step_sweep)
            dp.plotOPLcurves(pos, contrast, 'temp.png')
            response = Inputs.askForConfirmation('temp.png', host)
    
            if response == 'Yes':
                finer_sweep_required = Inputs.askForFinerSweep(host)
                
                if finer_sweep_required == 'Yes':
                    initial_OPL_guess = found_OPL  # Update the initial OPL guess
                    interval_sweep, step_sweep = Inputs.askForFinerSweepParameters(host)
                    finer_sweep = True
                else:
                    offset_found = True
            else:
                if finer_sweep:  # If a finer sweep was done, and no peak was found, ask for wider interval and step
                    interval_sweep, step_sweep = Inputs.askForNewSweepParameters(host)
                else:  # If no peak was found in the coarse sweep, repeat the coarse sweep with wider parameters
                    interval_coarse, step_coarse = Inputs.askForNewSweepParameters(host)
                    interval_sweep = interval_coarse
                    step_sweep = step_coarse
      
    dp.close()
    return found_OPL


def getOPLTable_from_offset():
    '''
    Generates and save optimal OPL table for given sample by offsetting pre-saved table.
    '''

    laser.LaserCheck()
    laser.EmissionOn()
    laser.setAmplitude(100)
        
    host = koala.KoalaLogin()
    
    RFSwitchState=laser.readRFSwitch()
    
    sample = Inputs.setObject(host)
    MO,wls,OPL_array,shutter_array,interval,step=Inputs.setMotorSweepParameters(host)
    today = datetime.today().strftime('%Y%m%d')
     
    base_path = f"tables/{sample}/{MO}/OPL/{today}"
    save_path = uniquify_top_directory(base_path)
    log_path = os.path.join(save_path, "Log")
    
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    
    # Determine offset
    found_OPL = determine_offset(wls, OPL_array, shutter_array, save_path, interval, step, host)

    offset = found_OPL - OPL_array[int(len(wls)/2)]
    print(offset)
    
    optimal_OPL_list = OPL_array + offset
    optimal_OPL_list = np.asarray(optimal_OPL_list)
    
    # Save OPL table  
    filename = f"table_{int(len(wls))}points.txt"
    np.savetxt(os.path.join(save_path, filename), np.vstack((wls/1000, optimal_OPL_list)).T, header='wavelength [nm] \t optimal OPR [qc]')
    
    laser.RFPowerOff()
    time.sleep(0.3)
    laser.RFSwitch(RFSwitchState)
    time.sleep(0.3)  
    
    laser.CloseAll()
    
    host.Logout()    
        
def getOPLTable(amplitude):  
    '''
    Generates and save optimal OPL table for given sample.
    '''

    laser.LaserCheck()
    laser.EmissionOn()
    laser.setAmplitude(amplitude)
        
    host = koala.KoalaLogin()
    
    RFSwitchState=laser.readRFSwitch()
    
    sample = Inputs.setObject(host)
    MO,wls,OPL_array,shutter_array,interval,step=Inputs.setMotorSweepParameters(host)
    today = datetime.today().strftime('%Y%m%d')
     
    base_path = f"tables/{sample}/{MO}/OPL/{today}"
    save_path = uniquify_top_directory(base_path)
    log_path = os.path.join(save_path, "Log")
    
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    
    # Determine offset
    found_OPL = determine_offset(wls, OPL_array, shutter_array, save_path, interval, step, host)
    
    # Ask for fine sweep parameters
    interval_fine, step_fine = Inputs.askForFinerSweepParametersLoop(host)

    offset = found_OPL - OPL_array[int(len(wls)/2)]
    print(offset)
    
    optimal_OPL_list = getOptimalPositions(wls, OPL_array + offset, shutter_array, interval_fine, step_fine, save_path, log_path, host)
    optimal_OPL_list = np.asarray(optimal_OPL_list)
    
    while True:  # This will keep looping until the user says there are no unsatisfactory wavelengths
        unsatisfactory_wavelengths = Inputs.show_wavelengths_for_verification(wls,host)
        print(unsatisfactory_wavelengths)
        
        if not unsatisfactory_wavelengths:
            break  # Exit the loop if there are no unsatisfactory wavelengths
        
        # Identify indices of unsatisfactory wavelengths in wls
        unsatisfactory_indices = np.nonzero(np.in1d(wls, unsatisfactory_wavelengths))
        print(unsatisfactory_indices)
        
        interval, step = Inputs.askForFinerSweepParametersLoop(host)
        
        # Re-run the optimization for unsatisfactory wavelengths
        new_optimal_OPL_list = getOptimalPositions(wls, optimal_OPL_list, shutter_array, interval, step, save_path, log_path, host, specific_wls=unsatisfactory_wavelengths)
        
        # Update optimal_OPL_list for these unsatisfactory wavelengths
        for i, new_opt in zip(unsatisfactory_indices[0], new_optimal_OPL_list):
            print(i, new_opt)
            optimal_OPL_list[i] = new_opt
    
    # Save OPL table  
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
    sample = Inputs.setObject(host)
    MO = Inputs.setMicroscopeObjective(host)
    wls = Inputs.setWavelengthArray('P',host)
    shutter_array, _ = Inputs.setShutterArray(wls,host)
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

'''
def getShutterTable():    
    laser.LaserCheck()
    laser.EmissionOn()
    laser.setAmplitude(10)

    host = koala.KoalaLogin()
        
    RFSwitchState=laser.readRFSwitch()
    
    sample = Inputs.setObject(host)
    MO,wls,OPL_array=Inputs.setShutterSweepParameters(host)
    
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
 '''   
    
def getShutterTable(amplitude):    
    laser.LaserCheck()
    laser.EmissionOn()
    laser.setAmplitude(amplitude)

    host = koala.KoalaLogin()
        
    RFSwitchState = laser.readRFSwitch()
    sample = Inputs.setObject(host)
    MO, wls, OPL_array = Inputs.setShutterSweepParameters(host)
    
    optimal_shutter_list = []
    for wl, i in zip(wls, range(len(wls))):
        if laser.check_for_crystal_switch(wl, RFSwitchState):
            laser.switchCrystal(RFSwitchState)
            RFSwitchState = 1
        
        laser.setWavelength(wl)
        host.MoveOPL(OPL_array[i])
        
        # Binary search approach
        shutter_min = 30
        shutter_max = 1e6
        condition_step = 100
        optimal_shutter = None
        
        max_pixel = [0]
        print('min, max, step, max_pixel, condition')
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                while (shutter_max - shutter_min) > condition_step:
                    
                    shutter = (shutter_min + shutter_max) // 2
                    host.SetCameraShutterUs(shutter)
                    time.sleep(2*shutter*1e-6)
                    
                    host.SaveImageToFile(1, temp_dir + 'holo_temp.tiff')
                    time.sleep(0.05)
                    temp_holo = tifffile.imread(temp_dir + 'holo_temp.tiff')
                    
                    # Check max pixel value in the hologram
                    max_pixel_value = np.max(temp_holo)
                   
                    if max_pixel_value < 255:  # No saturation
                        # step = abs(255-shutter_max)//2
                        # Save this as the optimal shutter time
                        optimal_shutter = shutter
                        
                        # Narrow down to higher exposure times to get closer to saturation
                        shutter_min = shutter 
    
                        # Dynamically increase shutter_max if max_pixel_value is far from saturation
                        # if max_pixel_value < 250:  # This threshold can be adjusted
                            # shutter_max = shutter + step  # Increase shutter_max to explore higher exposure times
                        
                    else:
                        # Saturation reached, reduce shutter value to avoid saturation
                        shutter_max = shutter
                
                    print(shutter_min, shutter_max, max_pixel_value, shutter_max - shutter_min)
            except KeyboardInterrupt:
                print("Process interrupted by user.")
                host.Logout()
                break
            
            if optimal_shutter is not None:
                optimal_shutter_list.append(optimal_shutter)
                print(f"\n*****\nOptimal shutter for {wl} pm: {optimal_shutter} us\n*****\n")


    # Save shutter table
    base_path = f"tables/{sample}/{MO}/shutter"
    save_path = uniquify_top_directory(base_path)
        
    optimal_shutter_list = np.asarray(optimal_shutter_list)
    filename = f"table_{int(len(wls))}points.txt"
    np.savetxt(os.path.join(save_path, filename), np.vstack((wls / 1000, optimal_shutter_list)).T,
               header='Wavelength [nm] \t Shutter speed [ms]')
    
    laser.RFPowerOff()
    time.sleep(0.3)
    laser.RFSwitch(RFSwitchState)
    time.sleep(0.3)    
    
    laser.CloseAll()
    host.Logout()
    

def getAmplitudeTable(shutter):    
    laser.LaserCheck()
    laser.EmissionOn()
    time.sleep(0.5)
    laser.daughter_board_disable()
    laser.FSK_ON()

    host = koala.KoalaLogin()
        
    RFSwitchState = laser.readRFSwitch()
    sample = Inputs.setObject(host)
    MO, wls, OPL_array = Inputs.setShutterSweepParameters(host)
    
    host.SetCameraShutterUs(2.5*1e3)
    
    optimal_amplitude_list = []
    for wl, i in zip(wls, range(len(wls))):
        if laser.check_for_crystal_switch(wl, RFSwitchState):
            laser.switchCrystal(RFSwitchState)
            RFSwitchState = 1
        
        laser.setWavelength(wl)
        host.MoveOPL(OPL_array[i])
        
        # Binary search approach
        amplitude_min = 1
        amplitude_max = 80
        condition_step = 1
        optimal_amplitude = None
        
        max_pixel = [0]
        print('min, max, step, max_pixel, condition')
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                while (amplitude_max - amplitude_min) > condition_step:
                    
                    amplitude = (amplitude_min + amplitude_max) // 2
                    laser.setAmplitude(amplitude)
                    time.sleep(2*shutter*1e-6)
                    
                    host.SaveImageToFile(1, temp_dir + 'holo_temp.tiff')
                    time.sleep(0.05)
                    temp_holo = tifffile.imread(temp_dir + 'holo_temp.tiff')
                    
                    # Check max pixel value in the hologram
                    max_pixel_value = np.max(temp_holo)
                   
                    if max_pixel_value < 255:  # No saturation
                        # Save this as the optimal shutter time
                        optimal_amplitude = amplitude
                        
                        # Narrow down to higher exposure times to get closer to saturation
                        amplitude_min = amplitude 
                        
                    else:
                        # Saturation reached, reduce shutter value to avoid saturation
                        shutter_max = shutter
            except KeyboardInterrupt:
                print("Process interrupted by user.")
                host.Logout()
                break
            
            if optimal_amplitude is not None:
                optimal_amplitude_list.append(optimal_amplitude)
                print(f"\n*****\nOptimal amplitude for {wl} pm: {optimal_amplitude} %\n*****\n")


    # Save shutter table
    base_path = f"tables/{sample}/{MO}/amplitude"
    save_path = uniquify_top_directory(base_path)
        
    optimal_amplitude_list = np.asarray(optimal_amplitude_list)
    filename = f"table_{int(len(wls))}points.txt"
    np.savetxt(os.path.join(save_path, filename), np.vstack((wls / 1000, optimal_amplitude_list)).T,
               header='Wavelength [nm] \t Amplitude [%]')
    
    laser.RFPowerOff()
    time.sleep(0.3)
    laser.RFSwitch(RFSwitchState)
    time.sleep(0.3)    
    
    laser.CloseAll()
    host.Logout()