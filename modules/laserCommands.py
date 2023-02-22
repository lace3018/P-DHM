# -*- coding: utf-8 -*-
"""
Created on Tue Aug  2 14:46:56 2022

@author: lace3018
"""

from NKTP_DLL import *
import time
import sys
    

def LaserCheck():
    '''
    Before starting emission. Verifies that:
        - The laser in OFF
        - The RF switch is set on 0
        - The RF power is set on 0
        - The connected crystal is set on 1
    If the state doesn't correspond to these expected values, prints an error message.

    Returns
    -------
    None.

    '''
    print('---')
    print('LASER CHECK - INITIAL STATE')
    # Emission
    exr_state = registerReadU8('COM4',15,0x30,-1)
    print('EXR: ',exr_state[1])
    # RF switch
    rfswitch_state = registerReadU8('COM4',30,0x34,-1)
    print('RF SWITCH: ',rfswitch_state[1])
    # RF power
    rfpower_state = registerReadU8('COM4',18,0x30,-1)
    print('RF POWER: ',rfpower_state[1])
    # Connected crystal
    crystal_state = registerReadU8('COM4',18,0x75,-1)
    print('CRYSTAL: ',crystal_state[1])
    if exr_state[1] != 0 or rfswitch_state[1] != 0 or rfpower_state[1] != 0 or crystal_state[1] != 1:
        print('Actual state does not correspond to expected initial state, close and restart the laser system.')
        sys.exit()
    print('---')   
    
def EmissionOn():
    '''
    Turns the supercontinuum EXR laser emission ON and RF power ON
    Sleeps for 0.2 s after each operation

    Returns
    -------
    None.

    '''
    resultEXR = registerWriteU8('COM4',15,0x30,3,-1) # EXR on
    print('Setting EXR emission ON:',RegisterResultTypes(resultEXR)[2:])

    resultRF = registerWriteU8('COM4',18,0x30,1,-1) # RF on
    print('Setting RF power ON:',RegisterResultTypes(resultRF)[2:])

def RFPowerOn():
    '''
    Sets RF power ON.

    Returns
    -------
    None.

    '''
    tmp7 = registerWriteU8('COM4',18,0x30,1,-1) # RF on
    print('Setting RF power ON:',RegisterResultTypes(tmp7)[2:])
    
def RFPowerOff():
    '''
    Sets RF power OFF.

    Returns
    -------
    None.

    '''
    tmp5 = registerWriteU8('COM4',18,0x30,0,-1) # RF off
    print('Setting RF power OFF:',RegisterResultTypes(tmp5)[2:])
    time.sleep(0.3)
    
def readRFSwitch():
    '''
    Reads and returns RF switch value

    Returns
    -------
    TYPE
        DESCRIPTION.

    '''
    RF_switch = registerReadU8('COM4',30,0x34,-1)
    print(RF_switch[1])
    return RF_switch[1]
    
def RFSwitch(RFSwitchState):
    '''
    Switches RF state. If state = 1, switches to 0, If state = 0, switches to 1.

    Parameters
    ----------
    RFSwitchState : int
        RF state value (has to be read with readRFSwitch first).

    Returns
    -------
    None.

    '''
    if RFSwitchState==0:
        tmp = registerWriteU8('COM4',30,0x34,1,-1)
    else:
        tmp = registerWriteU8('COM4',30,0x34,0,-1)
        
    time.sleep(0.25)
    RF_switch = registerReadU8('COM4',30,0x34,-1)
    print('Setting RF switch to',RF_switch[1],':',RegisterResultTypes(tmp)[2:])
    Connected_cristal = registerReadU8('COM4',18,0x75,-1)
    print('Setting connected crystal to',Connected_cristal[1],':',RegisterResultTypes(tmp)[2:])

def ReadCrystal():
    '''
    Prints and returns the crystal state.

    Returns
    -------
    Crystal state (int).

    '''
    Connected_crystal = registerReadU8('COM4',18,0x75,-1)
    print('Connected crystal ',Connected_cristal[1])
    return Connected_crystal

def setWavelength(wavelength):
    '''
    Sets selected wavelength.

    Parameters
    ----------
    wavelength : int
        Emission wavelength in pm.

    Returns
    -------
    None.

    '''
    registerWriteU32('COM4',18,0x90,int(wavelength),-1)
    print('Setting wavelength to',int(wavelength),' pm')

def setAmplitude(amplitude):
    '''
    Selects desired emission amplitude.

    Parameters
    ----------
    amplitude : int
        Emission amplitude in percent.

    Returns
    -------
    None.

    '''
    tmp = registerWriteU16('COM4',18,0xB0,int(amplitude)*10,-1) # 0 amplitude 
    print('Setting RF amplitude:',RegisterResultTypes(tmp)[2:])

def switchCrystalCondition(wavelength,RF_switch):
    '''
    Returns a value that matches the switch condition for the acquisition. If 
    the current wavelength is superior to 700 nm, switch value becomes 1 and
    allows for change in crystal state.

    Parameters
    ----------
    wavelength : float
        current wavelength [pm].
    RF_switch : int
        variable, either 0 or 1.

    Returns
    -------
    switch : int
        either 0 or 1.

    '''
    crystal_1_maximum_wavelength = registerReadU32('COM4',30,0x91,-1) # in pm
    switch=0
    if (wavelength > crystal_1_maximum_wavelength[1]) and RF_switch == 0:
        switch=1
    return switch

def CloseAll():
    '''
    Turns laser emission OFF
    Turns RF power OFF
    Changes RF switch to 0

    Returns
    -------
    None.

    '''
    # Emission
    registerWriteU8('COM4',15,0x30,0,-1)
    print('EMISSION OFF')
    time.sleep(0.3)
    # RF power
    registerWriteU8('COM4',18,0x30,0,-1)
    print('RF POWER OFF')
    # RF switch
    registerWriteU8('COM4',30,0x34,0,-1)
    print('RF SWITCH SET TO 0')