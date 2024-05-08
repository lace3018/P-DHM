# -*- coding: utf-8 -*-
"""
Created on Fri Apr  5 09:26:01 2024

@author: user
"""


import modules.koalaCommands as koala
import clr
import numpy as np
clr.AddReference('System')
from System import Array, Double
A = Array.CreateInstance(Double, 4)

try:
    host = koala.KoalaLogin()
    
    # Axis verification
    axis = host.AxisInstalled(1)
    # print(axis)
    
    # Get position
    position_buffer = Array.CreateInstance(Double, 4)
    host.GetAxesPosMu(position_buffer)
    print(position_buffer)
    new_array = np.fromiter(position_buffer, float)
    print(new_array)
    
    # Move the stage
    absMove = True  # Absolute movement
    mvX = True      # Move the X axis
    mvY = True      # Move the Y axis
    mvZ = True      # Move the Z axis
    mvTh = False    # Do not move the Theta axis
    
    distX = 53000.0 # Move X axis to 53000 μm
    distY = 72000.0 # Move Y axis to 72000 μm
    distZ = 2000.0  # Move Z axis to ...
    distTh = 0.0    # Not moving Theta, but a value is required
    
    accX = 10.0     # 10 μm accuracy for X
    accY = 1.0      # 1 μm accuracy for Y (not moving but specified)
    accZ = 1.0      # 1 μm accuracy for Z
    accTh = 1.0     # 1 μm accuracy for Theta (not moving but specified)
    waitEnd = True  # Wait for the movement to complete
    
    success = host.MoveAxes(absMove, mvX, mvY, mvZ, mvTh, distX, distY, distZ, distTh, accX, accY, accZ, accTh, waitEnd) # Perform the movement
    # print(success)
    
except Exception as e:
    print(f"An error occurred: {e}")
    
finally:
    koala.KoalaLogout(host)