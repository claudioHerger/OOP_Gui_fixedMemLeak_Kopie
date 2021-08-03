#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np

def exp_decay(amplitude, time_steps, decay_const):
    """ time_steps input must be a np.array! """
    return amplitude * np.exp(-time_steps/decay_const)

def run(DAS, decay_constants, time_delays, wavelengths, retained_DAS, start_time):
    """ given the selected DAS and their corresponding decay times, this function computes a data matrix as\n
    data_matrix = Sum (i over components/selected DAS):
    DAS_i(lambda)*exp(-t/decay_constant_i).\n
    \"t\" are the time delays at which data was taken.
    The DAS_i and the decay_constants_i are results of the global fit,
    However, the decay times can also be user selected decay times.

    Args:
        DAS (2d matrix): the matrix containing the DAS to be used for the data reconstruction.
        decay_constants (list of floats): the decay constants corresponding to the selected DAS.
        time_delays (list of floats): list of the time delays at which intensities were measured.
        wavelengths (list of floats): list of the wavelengths for which intensities were measured.
        retained_DAS (list of ints): which DAS to be used for data reconstruction.
        start_time (float): the time at which we have cut off the original data matrix for the fit.

    Returns:
        2d matrix of floats: the computed data matrix
    """

    # need time_delays as floats and only those after start_time
    start_time_index = time_delays.index(str(start_time))
    time_delays = time_delays[start_time_index:]
    time_delays = [float(time_delay) for time_delay in time_delays]
    time_delays = np.array(time_delays)

    decay_constants = [float(decay_constant) for decay_constant in decay_constants]
    nr_of_wavelenghts = len(wavelengths)
    nr_of_time_delays = len(time_delays)

    DAS = DAS.T

    # print(f'\nnew method: {decay_constants=}\n')

    """ SVD_GlobalFit TA data computed with loop """
    SVDGF_reconstructed_data_matrix = np.zeros((nr_of_wavelenghts, nr_of_time_delays))

    # to get numpy RuntimeWarnings as catchable Exceptions
    # e.g. when dividing by zero, or otherwise nan produced
    np.seterr(all='raise')

    try:
        for component in range(len(retained_DAS)):
            DAS_component = DAS[component, :]
            decay_constant_component = decay_constants[component]
            for index, amplitude in enumerate(DAS_component):
                SVDGF_reconstructed_data_matrix[index, :] += exp_decay(amplitude, time_delays, decay_constant_component)
    except FloatingPointError:
        raise

    # reset the np warnings setting to warn in console only
    np.seterr(all='warn')

    return SVDGF_reconstructed_data_matrix