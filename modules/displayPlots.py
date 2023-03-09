# -*- coding: utf-8 -*-
"""
Created on Wed Mar  1 09:18:54 2023

@author: Celine
"""

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

def plotTable(x1, y1, x2, y2, ylabel, savepath, savename):
    try:
        plt.close('all')
        set_plotting_style()
        
        plt.figure()
        plt.plot(x1,y1,'k-',label='Interpolation from uploaded table')
        plt.plot(x2,y2,'ro',label='Values used for the experiment')
        plt.xlabel("Wavelength [nm]")
        plt.ylabel(ylabel)
        plt.legend(loc='best')
        plt.grid(True)
        plt.savefig(str(savepath)+'/'+savename+'.png',dpi=300)
        plt.show()
    except Exception as e:
        print(f"An error occurred while plotting the OPR or shutter table: {str(e)}")
    
def plotContrast(frame, wls, contrasts, savepath, savename):
    try:
        plt.close('all')
        set_plotting_style()
        x = wls/1000
        y = contrasts

        plt.stem(x, y, linefmt='k-', markerfmt='ko', use_line_collection = True)
        plt.fill_between(x, y1=max(contrasts), y2=20,color='green',alpha=0.3,label='Good contrast')
        plt.fill_between(x, y1=20, y2=10,color='yellow',alpha=0.3,label='OK contrast')
        plt.fill_between(x, y1=10, y2=0,color='red',alpha=0.3,label='Low contrast')
        plt.title(f'Fringe contrast values for the holograms at frame {frame}')
        plt.xlabel('Wavelength [nm]')
        plt.ylabel('Contrast')
        plt.grid(True)
        plt.legend(loc='best')
        plt.savefig(str(savepath)+'/'+savename+'.png',dpi=300)
        plt.show()
    except Exception as e:
        print(f"An error occurred while plotting the contrast: {str(e)}")