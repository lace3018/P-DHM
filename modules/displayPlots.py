# -*- coding: utf-8 -*-
"""
Created on Wed Mar  1 09:18:54 2023

@author: Celine
"""

import numpy as np
import matplotlib.pyplot as plt

def set_plotting_style():
  plt.rcParams['axes.grid'] = False
  plt.rcParams['grid.color'] = "grey"
  plt.rcParams['grid.linewidth'] = 1
  plt.rcParams['grid.linestyle'] = "--"
  plt.rcParams['grid.alpha'] = "0.5"
  plt.rcParams['figure.figsize'] = (6,4)
  plt.rcParams['font.size'] = 12
  plt.rcParams['axes.labelsize'] = plt.rcParams['font.size']
  plt.rcParams['axes.titlesize'] = plt.rcParams['font.size']
  plt.rcParams['legend.fontsize'] = 0.9*plt.rcParams['font.size']
  plt.rcParams['xtick.labelsize'] = plt.rcParams['font.size']
  plt.rcParams['ytick.labelsize'] = plt.rcParams['font.size']
  plt.rcParams['axes.linewidth'] =1
  plt.rcParams['lines.linewidth']=1
  plt.rcParams['lines.markersize']=4
  plt.rcParams['legend.numpoints']=1

def plot(x1,y1,x2,y2,ylabel):
    set_plotting_style()
    
    plt.figure()
    plt.plot(x1,y1,'k-',label='Interpolation from uploaded table')
    plt.plot(x2,y2,'ro',label='Values used for the experiment')
    plt.xlabel("Wavelength [nm]")
    plt.ylabel(ylabel)
    plt.legend(loc='best')
    plt.grid(True)
    plt.show()