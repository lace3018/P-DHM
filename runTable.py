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

if table_type == 'OPL': 
    rough = Inputs.select_rough_or_not()
    if rough == True:
        gt.getOPLTableRough()
    else:
        gt.getOPLTable()
if table_type == 'shutter':
    gt.getShutterTable()
    
