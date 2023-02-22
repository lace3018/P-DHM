# -*- coding: utf-8 -*-
"""
Created on Tue Aug  2 15:15:22 2022

@author: lace3018
"""

import sys
import clr
import PySimpleGUI as sg

def checkKoalaRemote():
    '''
    Generates input validation that user has activated Remote Mode in Koala (or else code won't work).

    Returns
    -------
    None.

    '''
    sg.theme('DarkBlue15')
    layout = [[sg.Text('Is the Remote Mode button pressed in Koala?')],
              [sg.T("      "), sg.Checkbox('Yes',default=False)],
              [sg.T("")],[sg.T("        "), sg.Button('Launch acquisition',size=(20,4))],[sg.T("")]]
    window = sg.Window('Validation', layout, size=(300,300))
    event, values = window.read()
    window.close()
    
def KoalaLogin():
    '''
    Logs in Koala Remote and creates host allowing use of Koala Remote commands

    Returns
    -------
    host : remote client
        Remote client allowing connection to Koala.

    '''
    print('KOALA')

    # Add Koala remote librairies to Path
    sys.path.append(r'C:\Program Files\LynceeTec\Koala\Remote\Remote Libraries\x64') #load x86 for 32 bits applications

    # Import KoalaRemoteClient
    clr.AddReference("LynceeTec.KoalaRemote.Client")
    from LynceeTec.KoalaRemote.Client import KoalaRemoteClient

    # Define KoalaRemoteClient host
    host = KoalaRemoteClient()

    # Set IP address
    IP = 'localhost'

    # Logging in Koala
    username = ''
    [ret,username] = host.Connect(IP,username,True);
    password = username
    host.Login(password)

    print('Logged in Koala')

    print('---')
    return host