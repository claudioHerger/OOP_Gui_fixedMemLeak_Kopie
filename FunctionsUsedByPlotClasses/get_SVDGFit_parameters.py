#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Helper module for TA data analysis GUI.\n\n
Used for SVD_GlobalFit data reconstruction.\n
Inputs: \n
* retained_right_SVs, retained_singular_values\n
* temporal_resolution is used for convolution in fit function\n
* retained_compontents = retained components for data reconstruction, the number of components determines the number of exp decays used in fit function.\n\n
* time_delays = all the time steps in datafile at which data is taken - are used in exp decays of fit\n
* initial fit parameter values = dictionary of values to use as initial fit parameter values\n
* time_zero, is also used for convolution in fit function and to reduce the number of time_delays.\n
The fit parameters: \n
* the decay consts of exp decays in fit function - shared parameters\n
* the amplitudes of exp decays in fit function - individual parameters, i.e. different for each fitted right_SV.\n
Returns: \n
* the fit resulting fit parameters, i.e. the decay consts and the amplitudes.
"""

import asteval
import numpy as np
import lmfit
import math
import scipy.signal
import asteval
import tkinter as tk

def convolute_first_part_of_fit_function(sum_of_exponentials, time_delays, index_of_first_increased_time_interval, gaussian_for_convolution):
    """ convolutes the part of the fit function (sum of exponentials) that corresponds to the small initial time intervals
    with a gaussian that corresponds to the IRF (instrument response function) defined by time_zero and the temp_resolution. """

    reduced_sum_of_exponentials = sum_of_exponentials[:index_of_first_increased_time_interval]

    # convolve with the IRF gaussian of same length:
    convolution = scipy.signal.fftconvolve(reduced_sum_of_exponentials, gaussian_for_convolution, mode="same")

    # for normalisation:
    initial_time_interval = time_delays[1] - time_delays[0]
    convolution = convolution

    return convolution

def model_func_user_defined(time_delays, amplitudes, decay_constants, retained_components, parsed_user_defined_summands, asteval_interpreter: asteval.Interpreter = asteval.Interpreter(use_numpy=True)):
    taus = {}
    for (i,comp) in enumerate(retained_components):
        taus[f"component{comp}"] = decay_constants[i]

    asteval_interpreter.symtable["taus"] = taus
    asteval_interpreter.symtable["time_delays"] = time_delays

    exp_sum = np.zeros(len(time_delays))
    for i in range(len(retained_components)):
        exp_sum += amplitudes[i]*asteval_interpreter(parsed_user_defined_summands[i])

    return exp_sum

def model_func(time_delays, amplitudes, decay_constants, index_of_first_increased_time_interval=0, gaussian_for_convolution=0):
    """ model function for fit: a sum of exponentials (as many as SVD components are used for SVDGF reconstruction).\n
    the amplitudes of the expontials are individual fit parameters, the decay constants are shared fit parameters.\n
    the first part (up to index_of_first_increased_time_interval) is convoluted with a gaussian IRF of the same length.
    """
    exp_sum = np.zeros(len(time_delays))
    for amp, decay_constant in zip(amplitudes, decay_constants):
        exp_sum += amp*np.exp(-(time_delays/decay_constant))
        # exp_sum += amp*np.convolve(np.exp(-(time_delays/decay_constant)), gaussian_for_convolution, mode='same')
        # exp_sum += amp*scipy.signal.fftconvolve(np.exp(-(time_delays/decay_constant)), gaussian_for_convolution, mode='same')

    """ convolve the exp_sum with IRF gaussian from time_zero and temporal_resolution, not yet finished! """
    # convolution = convolute_first_part_of_fit_function(exp_sum, time_delays, index_of_first_increased_time_interval, gaussian_for_convolution)

    # # now replace exp_sum[:index_of_first_increased_time_interval] with the computed convolution:
    # fit_sum = np.zeros(len(time_delays))
    # fit_sum[:index_of_first_increased_time_interval] = convolution
    # fit_sum[index_of_first_increased_time_interval:] = exp_sum[index_of_first_increased_time_interval:]

    return exp_sum

def model_func_dataset(time_delays, idx_of_vector, fit_params, retained_components, index_of_first_increased_time_interval, gaussian_for_convolution, parsed_user_defined_summands, asteval_interpreter):
    """ calc model func from fit params for vectors_to_fit[idx_of_vector] """
    decay_constants = [fit_params[f'tau_component{comp}'] for comp in retained_components]

    # This way amplitudes have same indexes as in cannizzo paper
    amplitudes = [fit_params[f'amp_rSV{idx_of_vector}_component{component}'] for component in retained_components]

    if parsed_user_defined_summands:    # an empty list [] evaluates to False, thus this is not executed if list is empty.
        try:
            return model_func_user_defined(time_delays, amplitudes, decay_constants, retained_components, parsed_user_defined_summands, asteval_interpreter)
        except TypeError as error:
            raise TypeError("some problem arised in expression for asteval_interpreter!\n"
                            +f"error: {str(error)}\n"
                            +"check your entered target model summands file for any errors like missing brackets or so...")

    else:
        return model_func(time_delays, amplitudes, decay_constants, index_of_first_increased_time_interval=index_of_first_increased_time_interval, gaussian_for_convolution=gaussian_for_convolution)

def objective(fit_params, time_delays, vectors_to_fit, retained_components, index_of_first_increased_time_interval, gaussian_for_convolution, parsed_user_defined_summands, asteval_interpreter):
    """ calculate total residual for fits to several \"vectors\" held
    in a 2-D array, and modeled by model function """
    nr_of_vectors = len(retained_components)
    resid = np.zeros(shape=vectors_to_fit.shape)

    # make residuals for vectors in vectors_to_fit
    for i in range(0, nr_of_vectors):
        resid[i, :] = vectors_to_fit[i, :] - model_func_dataset(time_delays, i, fit_params, retained_components, index_of_first_increased_time_interval, gaussian_for_convolution, parsed_user_defined_summands, asteval_interpreter)

    # now flatten this to a 1D array, as minimize() needs
    return resid.flatten()

def get_index_at_which_time_intervals_increase_the_first_time(time_delays):
    """ for the convolution of fit function with instrument response function (IRF):\n
    compute the initial time interval and find the index when time intervals increase.\n
    i.e. computes the initial time_interval as time_delays[1] - time_delays[0] e.g. = 0.1 ps.\n
    then compute all the time intervals analoguously from the time_delays array.\n
    now find the index of the time interval at which the time intervals start to deviate from initial time interval.\n
    this index is passed on to the convolution function in the fit, where it is used to find up to which time delay the fit
    function has to be convoluted. """

    initial_time_interval = time_delays[1] - time_delays[0]

    time_intervals = np.zeros(len(time_delays))
    for i in range(len(time_delays)):
        # add last element specially, as the standard computation used for other elements does not work for this element.
        if i == len(time_delays) - 1:
            time_intervals[i] = time_intervals[i-1]
            continue
        time_intervals[i] = float(float(time_delays[i+1]) - float(time_delays[i]))

    # find the index after which the time intervals increase away from inital small time interval:
    index_of_first_increased_time_interval = 0
    for i in range(len(time_delays)-1):
        if not (math.isclose(time_intervals[i], time_intervals[i+1], abs_tol=initial_time_interval)):
            break
        index_of_first_increased_time_interval += 1

    # if the time intervals are all (approx) the same, return an index that is at 1/4 the length of the time_delays array:
    # mainly useful for my (claudios) initial simulated data file, where the time steps are all the same
    if index_of_first_increased_time_interval == len(time_delays) - 1:
        print(f'\ntime intervals are all approximately the same! reassigning the index of first increased time intervals! \n ')
        index_of_first_increased_time_interval = len(time_delays) // 4

    return index_of_first_increased_time_interval

def get_gaussian_for_convolution(time_delays, time_zero, temp_resolution, index_of_first_increased_time_interval):
    "compute array of gaussian  (time_delays - time_zero)/(0.6*temp_resolution)"
    gaussian_for_convolution = np.array([np.exp(-( (time_delay - time_zero)/(0.6*float(temp_resolution))) ** 2) for time_delay in time_delays[:index_of_first_increased_time_interval]])

    """ some alternative way to compute the gaussian from some theory paper """
    # strechted_FWHM = temp_resolution/(2*math.sqrt(math.log(2)))
    # amplitude = 1/(strechted_FWHM*math.sqrt(2*math.pi))
    # gaussian_IRF = amplitude*np.exp(-math.log(2)*(2*((time_delays-time_zero)/temp_resolution)**2))
    # return gaussian_IRF

    return gaussian_for_convolution

def initialize_fit_parameters(retained_components, initial_fit_parameter_values):
    minimumNrOfValues = 100
    user_file_has_too_few_values = False
    for key in initial_fit_parameter_values.keys():
        if (len(initial_fit_parameter_values[key]) <= minimumNrOfValues):
            minimumNrOfValues = len(initial_fit_parameter_values[key])

    if (minimumNrOfValues < len(retained_components)):
        user_file_has_too_few_values = True
        tk.messagebox.showerror("Warning,", "There are insufficient parameter values in your initial fit parameter values file.\n"+
                                            "See the help button in the window where you can set the initial fit parameter values.\n"+
                                            "(Button 'Set initial fit parameter values'.)\n\n"+
                                            "In the mean while, the program will use default initial values for the fit parameters, which have been found to work somewhat well.\n"+
                                            "all decay constants = 50.0, all amplitudes = 0.7")

    fit_params = lmfit.Parameters()
    if user_file_has_too_few_values:
        for component in retained_components:
            fit_params.add(f'tau_component{component}', value=50.0)
            for rSV_index in range(0, len(retained_components)):
                fit_params.add(f'amp_rSV{rSV_index}_component{component}', value=0.7)
    else:
        try:
            for component in retained_components:
                fit_params.add(f'tau_component{component}', value=float(initial_fit_parameter_values["time_constants"][component]))
                for rSV_index in range(0, len(retained_components)):
                    fit_params.add(f'amp_rSV{rSV_index}_component{component}', value=float(initial_fit_parameter_values[f"amps_rSV{rSV_index}"][component]))
        except KeyError as error:
            raise ValueError("a key error occured when reading your initial fit parameter values dict.\n"+
                            f"first missing key {error}.\n"+
                            "The Initial_fit_parameter_values.txt should contain a dictinary with the keys: 'time_constants', 'amps_rSV0', 'amps_rSV1', ... "+
                            "depending on how many components are selected for the fit.")

    return fit_params


def start_the_fit(retained_components, time_delays, retained_rSVs, retained_singular_values, initial_fit_parameter_values, time_zero, temp_resolution, parsed_user_defined_summands, fit_method_name):
    """ initialize vectors to fit and fit parameters, then calls lmfit function """
    # multiplication of each retained right SV with its respective singular value:
    vectors_to_fit = np.zeros((len(retained_components), len(time_delays)))
    for component in range(len(retained_components)):
        sing_value = retained_singular_values[component]
        vectors_to_fit[component, :] = sing_value*retained_rSVs[component, :]

    # initialize fit parameters
    fit_params = initialize_fit_parameters(retained_components, initial_fit_parameter_values)

    # need this index for the convolution in fit procedure:
    index_of_first_increased_time_interval = get_index_at_which_time_intervals_increase_the_first_time(time_delays)

    # this is the gaussian (array length = index_of_first_increased_time_interval )
    # with which the first part of the fit function is convoluted in fit function
    # gaussian_for_convolution = get_gaussian_for_convolution(time_delays, time_zero, temp_resolution, index_of_first_increased_time_interval)
    gaussian_for_convolution = None

    # instantiate the asteval Interpreter, is however only used when user defined fit function is used.
    asteval_interpreter = asteval.Interpreter(use_numpy=True)

    # run the global fit over all the data sets, i.e. all VT_i
    # per default uses method='levenberg-marquardt-leastsq' = 'leastsq'
    # could change the fit method via "method" argument. see web for possible fit methods
    result = lmfit.minimize(objective, fit_params, method=fit_method_name, args=(time_delays, vectors_to_fit, retained_components, index_of_first_increased_time_interval, gaussian_for_convolution, parsed_user_defined_summands, asteval_interpreter))

    return result

def run(retained_rSVs, retained_singular_values, retained_components, time_delays, start_time, initial_fit_parameter_values, time_zero, temp_resolution, parsed_user_defined_summands=False, fit_method_name='leastsq'):

    # for the fit function we need the time_delays reduced to the ones after start_time
    start_time_index = time_delays.index(str(start_time))
    time_delays = time_delays[start_time_index:]
    time_delays = [float(time_delay) for time_delay in time_delays]
    time_delays = np.array(time_delays)

    try:
        result = start_the_fit(retained_components, time_delays, retained_rSVs, retained_singular_values, initial_fit_parameter_values, time_zero, temp_resolution, parsed_user_defined_summands, fit_method_name)
        resulting_fit_params = result.params

    except (ValueError,TypeError) as error:
        raise ValueError(str(error) + "\n\nMaybe try it with another fit method (Fit method menu) or changed initial fit parameter values (button in bottom left corner),"
                                +" or another start time-value or another set of components ...") # raises the caught exception again

    return result, resulting_fit_params