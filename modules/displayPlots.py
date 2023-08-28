# -*- coding: utf-8 -*-
"""
Created on Wed Mar  1 09:18:54 2023

@author: Celine
"""
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from PIL import Image
import imageio
import warnings
warnings.filterwarnings("ignore")


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
        plt.figure()
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
        

def displayPhaseImage(input_path, wl, frame):
    
    plt.close('all')
    image = np.asarray(Image.open(input_path))
    plt.figure()
    plt.imshow(image,cmap='turbo') 
    plt.xticks([])
    plt.yticks([])
    plt.title(f'Phase image | frame {str(frame+1)} | {wl} pm')
    plt.show()
    
def displayIntensityImage(input_path, frame):
    
    # plt.close('all')
    image = np.asarray(Image.open(input_path))
    plt.figure()
    plt.imshow(image,cmap='gray') 
    plt.xticks([])
    plt.yticks([])
    plt.title('Intensity image')
    plt.show()
    

def displayAll(path_holo, path_intensity, path_phase, wavelength, frame):
    plt.close('all')

    # Create a list of image paths
    image_paths = [path_holo, path_intensity, path_phase]
    image_types = ['Hologram', 'Intensity', 'Phase']

    # Create a figure and axes for the grid
    fig, axes = plt.subplots(1, 3, figsize=(18,6))

    # Iterate over the axes and image paths
    for ax, image_path, image_type in zip(axes.flatten(), image_paths, image_types):
        # Load the image using plt.imread
        image = plt.imread(image_path)

        # Display the image on the current axis
        ax.imshow(image, cmap='turbo')
        ax.axis('off')

        # Add a dummy title to each image
        ax.set_title(f'{image_type}')

        # Add zoomed region for the hologram
        if image_type == 'Hologram':
            # Define the zoomed region (bottom right, 50x50 pixels)
            zoom_region = image[-50:, -50:]
            # Create the inset axes
            axins = inset_axes(ax, width="30%", height="30%", loc="lower right")
            # Display the zoomed region
            axins.imshow(zoom_region, cmap='turbo')
            axins.axis('off')

    # Add a title to the whole figure
    fig.suptitle(f'{wavelength} pm | frame {frame}')

    # Show the plot
    plt.show()
    
    
def display_average_phase(path, wavelengths, frame):
    print(path, wavelengths, frame)
    plt.close('all')

    # Create a figure and axes for the grid
    plt.figure()

    # Initialize the sum of the phases
    phase_sum = 0
    for wl, i in zip(wavelengths, range(len(wavelengths))):
        # Read the image using imageio
        phase_path = f'{path}/{frame}/{str(int(wl))}_{i+1}/Phase.tiff'
        phase = imageio.imread(phase_path)

        # Convert to float to ensure proper arithmetic
        phase = phase.astype(float)
        phase_sum += phase

    average_phase = phase_sum / len(wavelengths)

    # Display the image on the current axis
    plt.imshow(average_phase, cmap='turbo')
    plt.axis('off')

    # Add a dummy title to each image
    plt.title(f'Phase average frame {frame}')

    # Show the plot
    plt.show()


def displayInt_and_phase(path_intensity, path_phase, wavelength, frame):
    plt.close('all')
    
    # Create a list of image paths
    image_paths = [path_intensity, path_phase]
    image_types = ['Intensity', 'Phase']
    
    # Create a figure and axes for the grid
    fig, axes = plt.subplots(1, 2)
    
    # Iterate over the axes and image paths
    for ax, image_path, image_type in zip(axes.flatten(), image_paths, image_types):
        # Load the image using plt.imread
        image = plt.imread(image_path)
    
        # Display the image on the current axis
        ax.imshow(image, cmap='turbo')
        ax.axis('off')
    
        # Add a dummy title to each image
        ax.set_title(f'{image_type}')
    
    # Add a title to the whole figure
    fig.suptitle(f'{wavelength} pm | frame {frame}')
    
    # Adjust the spacing between subplots
    plt.tight_layout()
    
    # Show the plot
    plt.show()

def close():
    plt.close('all')
    
    
def plotOPLcurves(pos, contrast, path):
    plt.close('all')
    plt.figure()
    plt.plot(pos, contrast)
    plt.savefig('temp.png')