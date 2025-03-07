# -*- coding: utf-8 -*-
"""
Created on Tue Aug  2 14:46:56 2022

@author: lace3018
"""

from . import NKTP_DLL as nkt
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
    exr_state = nkt.registerReadU8('COM4',15,0x30,-1)
    print('EXR: ',exr_state[1])
    # RF switch
    rfswitch_state = nkt.registerReadU8('COM4',30,0x34,-1)
    print('RF SWITCH: ',rfswitch_state[1])
    # RF power
    rfpower_state = nkt.registerReadU8('COM4',18,0x30,-1)
    print('RF POWER: ',rfpower_state[1])
    # Connected crystal
    crystal_state = nkt.registerReadU8('COM4',18,0x75,-1)
    print('CRYSTAL: ',crystal_state[1])
    if exr_state[1] != 0 or rfswitch_state[1] != 0 or rfpower_state[1] != 0 or crystal_state[1] != 1:
        print('Actual state does not correspond to expected initial state, close and restart the laser system.')
        sys.exit()
    print('---')   
    
    
def EXR_ON():
    '''
    Sets EXR power ON

    Returns
    -------
    None.

    '''
    result = nkt.registerWriteU8('COM4',15,0x30,3,-1) # EXR on
    print('Setting EXR emission ON:', nkt.RegisterResultTypes(result)[2:])
    

def EXR_OFF():
    '''
    Sets EXR power OFF

    Returns
    -------
    None.

    '''
    result = nkt.registerWriteU8('COM4',15,0x30,0,-1)
    print('Setting EXR emission OFF:', nkt.RegisterResultTypes(result)[2:])
    

def RFPowerOn():
    '''
    Sets RF power ON.

    Returns
    -------
    None.

    '''
    result = nkt.registerWriteU8('COM4',18,0x30,1,-1) # RF on
    print('Setting RF power ON:',nkt.RegisterResultTypes(result)[2:])
    
    
def RFPowerOff():
    '''
    Sets RF power OFF.

    Returns
    -------
    None.

    '''
    result = nkt.registerWriteU8('COM4',18,0x30,0,-1) # RF off
    print('Setting RF power OFF:',nkt.RegisterResultTypes(result)[2:])
       
    
def EmissionOn():
    '''
    Turns the supercontinuum EXR laser emission ON and RF power ON
    Sleeps for 0.3 s after each operation

    Returns
    -------
    None.

    '''
    EXR_ON()
    time.sleep(0.3)
    RFPowerOn()
    time.sleep(0.3)
    

def EmissionOff():
    '''
    Turns the supercontinuum EXR laser emission OFF and RF power OFF
    Sleeps for 0.3 s after each operation

    Returns
    -------
    None.

    '''
    
    EXR_OFF()
    time.sleep(0.3)
    RFPowerOff()
    time.sleep(0.3)
    
    
def readRFSwitch():
    '''
    Reads and returns RF switch value

    Returns
    -------
    TYPE
        DESCRIPTION.

    '''
    RF_switch = nkt.registerReadU8('COM4',30,0x34,-1)
    print('RF switch value: ', RF_switch[1])
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
        tmp = nkt.registerWriteU8('COM4',30,0x34,1,-1)
    else:
        tmp = nkt.registerWriteU8('COM4',30,0x34,0,-1)
        
    time.sleep(0.25)
    RF_switch = nkt.registerReadU8('COM4',30,0x34,-1)
    print('Setting RF switch to',RF_switch[1],':',nkt.RegisterResultTypes(tmp)[2:])
    Connected_cristal = nkt.registerReadU8('COM4',18,0x75,-1)
    print('Setting connected crystal to',Connected_cristal[1],':',nkt.RegisterResultTypes(tmp)[2:])


def ReadCrystal():
    '''
    Prints and returns the crystal state.

    Returns
    -------
    Crystal state (int).

    '''
    Connected_crystal = nkt.registerReadU8('COM4',18,0x75,-1)
    print('Connected crystal ', Connected_crystal[1])
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
    nkt.registerWriteU32('COM4',18,0x90,int(wavelength),-1)
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
    set_amplitude_state = nkt.registerWriteU16('COM4',18,0xB0,int(amplitude)*10,-1) # 0 amplitude 
    print('Setting RF amplitude:',nkt.RegisterResultTypes(set_amplitude_state)[2:])


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
    EmissionOff()
    # RF power
    RFPowerOff()
    daughter_board_enable()
    FSK_OFF()
    # set RF switch to 0
    nkt.registerWriteU8('COM4',30,0x34,0,-1)
    print('RF SWITCH SET TO 0')
    
    
def check_for_crystal_switch(wavelength, RFSwitchState):
    crystal_1_maximum_wavelength = nkt.registerReadU32('COM4',30,0x91,-1) # in pm
    if (wavelength > crystal_1_maximum_wavelength[1]) and RFSwitchState == 0:
        return True
    else:
        return False
            

def switchCrystal(RFSwitchState):
    RFPowerOff()
    time.sleep(0.25)
    RFSwitch(RFSwitchState)
    RFPowerOn()
    RFSwitchState = readRFSwitch()
    
def FSK_ON():
    '''
    Turns fast wl switching mode ON
    '''

    result1 = nkt.registerWriteU8('COM4', 18, 59, 3, -1)
    result2 = nkt.registerWriteU8('COM4', 23, 59, 3, -1)
    print('Fast wavelength switching : ON', nkt.RegisterResultTypes(result1)[2:],nkt.RegisterResultTypes(result2)[2:])
    

def daughter_board_enable():
    '''
    '''

    result1 = nkt.registerWriteU8('COM4', 18, 60, 1, -1)
    result2 = nkt.registerWriteU8('COM4', 23, 60, 1, -1)
    print('Daughter board : enabled', nkt.RegisterResultTypes(result1)[2:],nkt.RegisterResultTypes(result2)[2:])
    

def daughter_board_disable():
    '''
    '''

    result1 = nkt.registerWriteU8('COM4', 18, 60, 0, -1)
    result2 = nkt.registerWriteU8('COM4', 23, 60, 0, -1)
    print('Daughter board : disabled', nkt.RegisterResultTypes(result1)[2:],nkt.RegisterResultTypes(result2)[2:])
    

def FSK_OFF():
    '''
    Turns fast wl switching mode OFF
    '''

    result1 = nkt.registerWriteU8('COM4', 18, 59, 0, -1)
    result2 = nkt.registerWriteU8('COM4', 23, 59, 0, -1)
    print('Fast wavelength switching : OFF', nkt.RegisterResultTypes(result1)[2:], nkt.RegisterResultTypes(result2)[2:])