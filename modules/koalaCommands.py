# -*- coding: utf-8 -*-
"""
Created on Tue Aug  2 15:15:22 2022

@author: lace3018
"""

import sys
import clr
    
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
    login_bool = host.Login(password)

    if login_bool==True:
        print('Logged in Koala')
        print('---')
    else:
        print('Open production (remote) mode in Koala and try again')
        sys.exit()

    return host

def KoalaLogout(host):
    host.Logout()