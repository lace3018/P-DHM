# -*- coding: utf-8 -*-
"""
Created on Wed Aug  2 15:24:47 2023

@author: user
"""

import os
import numpy as np
from PIL import Image


def detect_fringes_fourier(img_arr, offset=12, corner='bottom_right'):
    f_transform = np.fft.fft2(img_arr)
    f_transform_shifted = np.fft.fftshift(f_transform)
    magnitude_spectrum = np.abs(f_transform_shifted)
    rows, cols = magnitude_spectrum.shape
    if corner == 'bottom_right':
        quarter_spectrum = magnitude_spectrum[rows // 2 + offset:, cols // 2 + offset:]
    else:  # 'top_left'
        quarter_spectrum = magnitude_spectrum[:rows // 2 - offset, :cols // 2 - offset]
    return quarter_spectrum


def calculate_snr_fft(magnitude_spectrum, circle_size=10):
    max_index = np.unravel_index(np.argmax(magnitude_spectrum), magnitude_spectrum.shape)
    signal_mask = np.zeros_like(magnitude_spectrum, dtype=bool)
    signal_mask[max_index[0], :] = True
    signal_mask[:, max_index[1]] = True
    radius = circle_size // 2
    rows, cols = np.ogrid[:magnitude_spectrum.shape[0], :magnitude_spectrum.shape[1]]
    distance_from_center = np.sqrt((rows - max_index[0]) ** 2 + (cols - max_index[1]) ** 2)
    circle_mask = distance_from_center <= radius
    signal_mask |= circle_mask
    signal_region = magnitude_spectrum[signal_mask]
    noise_mask = ~signal_mask
    signal = np.mean(signal_region)
    noise = np.std(magnitude_spectrum[noise_mask])
    snr = signal / noise if noise != 0 else np.inf
    return snr, signal_mask

def detect_fringes(holo_path, wavelength, frame):
    has_fringes_in_both_corners = True

    with Image.open(holo_path) as img:
        crop_size = 100

        for corner in ['bottom_right', 'top_left']:
            x, y = (img.width - crop_size, img.height - crop_size) if corner == 'bottom_right' else (0, 0)
            cropped_holo = img.crop((x, y, x + crop_size, y + crop_size))
            img_arr = np.array(cropped_holo)
            quarter_spectrum = detect_fringes_fourier(img_arr, corner=corner)
            snr, signal_mask = calculate_snr_fft(quarter_spectrum)

            threshold = 8
            has_fringes = snr > threshold
            
            if not has_fringes:
                has_fringes_in_both_corners = False

    return has_fringes_in_both_corners