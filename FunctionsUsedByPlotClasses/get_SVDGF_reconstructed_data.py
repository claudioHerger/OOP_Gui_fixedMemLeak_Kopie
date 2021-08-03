#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np

def exp_decay(amplitude, time_steps, decay_const):
    """ time_steps input must be a np.array! """
    return amplitude * np.exp(-time_steps/decay_const)

def run(DAS, decay_constants, time_delays, wavelengths, retained_components, start_time):



    # need time_delays as floats and only those after start_time
    start_time_index = time_delays.index(str(start_time))
    time_delays = time_delays[start_time_index:]
    time_delays = [float(time_delay) for time_delay in time_delays]
    time_delays = np.array(time_delays)

    # decay_constants = [resulting_fit_params['tau_component%i' % (j)].value for j in retained_components]
    decay_constants = [float(decay_constant) for decay_constant in decay_constants]
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

    return SVDGF_reconstructed_data_matrix