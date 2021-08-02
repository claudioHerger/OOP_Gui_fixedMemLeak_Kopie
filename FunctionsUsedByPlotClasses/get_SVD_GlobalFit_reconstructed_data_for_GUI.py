#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Helper module for TA data analysis GUI.\n\n
Used for SVD_GlobalFit data reconstruction.\n
Inputs: \n
* Decay associated spectra, resulting_fit_params, time_delays, wavelenghts, retained_components, filename, start_time\n
Returns: \n
* data matrix reconstructed from DAS that decay exponentially with time_delay/decay consts from resulting fit params\n
"""

import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np

def exp_decay(amplitude, time_steps, decay_const):
    """ time_steps input must be a np.array! """
    return amplitude * np.exp(-time_steps/decay_const)

def plot_heatmap_seaborn(data, time_delays, wavelengths, filename, retained_components):

    # data = data.astype(float)

    num_ticks = 10
    label_format = '{:,.2f}'

    # the index of the position of yticks
    yticks = np.linspace(0, len(wavelengths) - 1, num_ticks, dtype=np.int)
    xticks = np.linspace(0, len(time_delays) - 1, num_ticks, dtype=np.int)
    # the content of labels of these yticks
    yticklabels = [float(wavelengths[idx]) for idx in yticks]
    xticklabels = [float(time_delays[idx]) for idx in xticks]

    yticklabels = [label_format.format(x) for x in yticklabels]
    xticklabels = [label_format.format(x) for x in xticklabels]

    plt.figure(figsize=(10,7))
    cmap = sns.diverging_palette(220, 20, as_cmap=True)
    ax = sns.heatmap(data, cbar_kws={'label': 'rel transmission'}, cmap=cmap)

    ax.set_yticks(yticks)
    ax.set_yticklabels(yticklabels)
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels, rotation=30)

    ax.set_ylabel("wavelengths [nm]")
    ax.set_xlabel("time since overlap [ps]")

    filename = os.path.basename(filename)
    ax.set_title(filename+" reconstructed from DAS, components: "+str(retained_components))

    # to store plots in local directory
    global plot_directory
    plot_directory = "../OOP_GUI/FunctionsUsedByPlotClasses/"
    if not os.path.exists(plot_directory):
        os.makedirs(plot_directory)

    plt.tight_layout()
    plt.savefig(plot_directory+"DAS_SVDGF_recon_heatmap_"+ filename+".png")
    plt.close()

def run(DAS, resulting_fit_params, time_delays, wavelengths, retained_components, filename, start_time):

    # need time_delays as floats and only those after start_time
    start_time_index = time_delays.index(str(start_time))
    time_delays = time_delays[start_time_index:]
    time_delays = [float(time_delay) for time_delay in time_delays]
    time_delays = np.array(time_delays)

    decay_constants = [resulting_fit_params['tau_component%i' % (j)].value for j in retained_components]
    # decay_constants = [float(decay_constant) for decay_constant in decay_constants]
    nr_of_wavelenghts = len(wavelengths)
    nr_of_time_delays = len(time_delays)

    DAS = DAS.T

    print(f'resulting decay constants given before reconstructing data with DAS: {decay_constants}')

    """ SVD_GlobalFit TA data computed with loop """
    SVDGF_reconstructed_data_matrix = np.zeros((nr_of_wavelenghts, nr_of_time_delays))

    for component in range(len(retained_components)):
        DAS_component = DAS[component, :]
        decay_constant_component = decay_constants[component]
        for index, amplitude in enumerate(DAS_component):
            SVDGF_reconstructed_data_matrix[index, :] += exp_decay(amplitude, time_delays, decay_constant_component)


    # to save heatmap figure to file - this should only be used for testing, as it slows down the gui application if used!
    # plot_heatmap_seaborn(SVDGF_reconstructed_data_matrix, time_delays, wavelengths, filename, retained_components)

    return SVDGF_reconstructed_data_matrix