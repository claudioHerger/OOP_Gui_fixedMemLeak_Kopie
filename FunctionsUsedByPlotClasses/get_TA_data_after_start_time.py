#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Helper module for TA data analysis GUI, used by its PlotClasses.\n\n
The run(path_to_data, start_time) method returns the TA data matrix at input path_to_data\n
stripped from the time_steps and wavelenghts and starting from the input start_time value.\n
It also returns the complete time_steps and wavelengths.
"""

import numpy as np
from FunctionsUsedByPlotClasses import get_closest_nr_from_array_like

def load_complete_data(data_file):
    """
    opens the data file and returns it as a matrix
    """
    if data_file.endswith(".txt"):
        with open(data_file, 'r') as file:
            data = [x.replace('\n', '').replace(',','').split() for x in file]
    elif data_file.endswith(".dat"):
        with open(data_file, 'r') as file:
            data = [x.replace('\n', '').replace(',','').split() for x in file]
    elif data_file.endswith(".csv"):
        with open(data_file, 'r') as file:
            data = [x.replace('\n', '').split(",") for x in file]

    data = np.array(data)

    # convert the data into an easier to handle format
    for row in range(data.shape[0]):
        for col in range(data.shape[1]):
            data[row, col] = float(data[row, col])

    return data

def load_complete_time_delays(data):
    """
    loads time delays from data file and puts them into array
    """

    time_delays = [data[i+1][0] for i in range(data.shape[0] - 1)]

    return time_delays

def load_complete_wavelengths(data):
    """
    loads wavelengths from data file and puts them into array
    """

    wavelengths = [data[0, i+1] for i in range(data.shape[1] - 1)]

    return wavelengths

def get_data_at_time(path_to_data, time):
    """
    returns the data matrix corresponding to the input time, e.g. CPM time.
    also returns the complete time delay and wavelengths lists
    """
    complete_data = load_complete_data(path_to_data)
    time_delays = load_complete_time_delays(complete_data)
    wavelengths = load_complete_wavelengths(complete_data)

    time = str(get_closest_nr_from_array_like.run(time_delays, float(time)))
    time_index = time_delays.index(time)

    TA_data = complete_data[1:, 1:]
    TA_data_after_time = TA_data[time_index:, :]

    return TA_data_after_time.T, time_delays, wavelengths

def run(path_to_data, start_time):
    """
    returns the TA data matrix at input path_to_data\n
    but stripped from the time_steps and wavelenghts and starting from the closest actual time delay to the input start_time value.\n
    It also returns the complete time_steps and wavelengths.
    """
    time=str(start_time)
    TA_data_after_time, time_delays, wavelengths = get_data_at_time(path_to_data, time)

    return TA_data_after_time, time_delays, wavelengths