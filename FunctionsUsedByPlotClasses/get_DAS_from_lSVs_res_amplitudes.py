#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Helper module for TA data analysis GUI.\n\n
Used for SVD_GlobalFit data reconstruction.\n
Inputs: \n
* retained_left_SVs, resulting_fit_params\n
Returns: \n
* Decay associated spectra computed from left_SVs and resulting amplitudes in resulting fit params\n
"""

import numpy as np
import os
import matplotlib.pyplot as plt

def make_plot(resulting_fit_params, retained_components, wavelengths, DAS, path_to_data, start_time):
    num_ticks = 10
    label_format = '{:,.2f}'
    # decay_constants = [resulting_fit_params['tau_components%i' % (j)].value for j in retained_components]

    # the index of the position of yticks
    xticks = np.linspace(0, len(wavelengths) - 1, num_ticks, dtype=np.int)
    # the content of labels of these yticks
    xticklabels = [float(wavelengths[idx]) for idx in xticks]
    xticklabels = [label_format.format(x) for x in xticklabels]

    # to store plots in directory
    plot_directory = "../OOP_GUI_fixedMemLeak/FunctionsUsedByPlotClasses/DAS_plots/"
    if not os.path.exists(plot_directory):
        os.makedirs(plot_directory)

    plt.style.use("seaborn")
    plt.figure(figsize=(10,6))

    for i in range(len(retained_components)):
        plt.plot(wavelengths, DAS[:, i], label=f'DAS_comp{i}, tau=??? ps')

    plt.legend()
    plt.xticks(xticks, xticklabels)
    filename = os.path.basename(path_to_data)
    plt.title("DAS via global fit for " + filename + " " + str(start_time)+"ps")
    plt.savefig(plot_directory+"DAS_SVDGF_"+ filename+ " " + str(start_time)+"ps.png")
    plt.close()

def run(retained_leftSVs, resulting_fit_params, retained_components, wavelengths, filename, start_time):
    nr_of_retained_components = len(retained_components)

    DAS = np.zeros((len(wavelengths), nr_of_retained_components))
    for k in range(nr_of_retained_components):
        for i in range(nr_of_retained_components):
            DAS[:, k] += resulting_fit_params[f'amp_rSV{i}_component{retained_components[k]}'].value * retained_leftSVs[:, i]

    # to check how the DAS look - this should only be used for testing.
    # make_plot(resulting_fit_params, retained_components, wavelengths, DAS, filename, start_time)

    return DAS