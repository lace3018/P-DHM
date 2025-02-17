# -*- coding: utf-8 -*-
"""
Created on Tue Aug  8 12:27:21 2023

@author: user
"""

import modules.laserCommands as laser
import modules.getTable as gt
import modules.Inputs as Inputs
import time


laser.CloseAll()
time.sleep(1)
laser.LaserCheck()

table_type = Inputs.select_OPL_or_shutter()
amplitude = 100

if table_type == 'OPL': 
    table_acquisition_type = Inputs.select_table_acquisition_type()
    if table_acquisition_type=='Initial Rough Table (only if no previous data available)':
        gt.getOPLTableRough()
    if table_acquisition_type=='Precise Table (needs a pre-saved table of similar sample)':
        gt.getOPLTable(amplitude)
    if table_acquisition_type=='Table Offset (fast option if pre-saved table of same sample available)':
        gt.getOPLTable_from_offset()
        
    shutter_or_not = Inputs.ask_for_shutter()
    if shutter_or_not == True:
        gt.getShutterTable(amplitude)
if table_type == 'shutter':
    gt.getShutterTable(amplitude)
    
