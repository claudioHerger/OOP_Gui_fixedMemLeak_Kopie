#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.linalg

from FunctionsUsedByPlotClasses import get_SVD_reconstructed_data_for_GUI, get_TA_data_after_start_time

def make_heatmap(data, time_delays, wavelengths, title="", xlab="time since overlap [ps]", ylab="wavelengths [nm]"):
    data = data.astype(float)

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

    fig = plt.figure()
    axes = fig.add_subplot(1,1,1)

    cm = sns.diverging_palette(220, 20, as_cmap=True)
    sns.heatmap(data, ax = axes, cmap=cm)

    axes.set_yticks(yticks)
    axes.set_yticklabels(yticklabels, fontsize=11)
    axes.set_xticks(xticks)
    axes.set_xticklabels(xticklabels, rotation=30, fontsize=11)

    axes.set_ylabel(ylab, fontsize=13)
    axes.set_xlabel(xlab, fontsize=13)

    # use matplotlib.colorbar.Colorbar object
    cbar = axes.collections[0].colorbar
    # here set the label of colorbar
    cbar.set_label('rel transmission', fontsize=13)

    axes.set_title(title)

    fig.tight_layout()

    fig.savefig("thesis_plots/"+title+".png")

    return None

def plot_orig_data_heatmap(filename, start_time):
    TA_data_after_start_time, time_delays, wavelengths = get_TA_data_after_start_time.get_data_at_time(filename, start_time)

    start_time_index = time_delays.index(str(start_time))
    make_heatmap(TA_data_after_start_time, time_delays[start_time_index:], wavelengths, "original data")

    return None

def plot_SVD_reconstruction_heatmap(filename, start_time, components=[0,1,2]):
    TA_data_after_start_time, time_delays, wavelengths = get_TA_data_after_start_time.get_data_at_time(filename, start_time)
    SVD_reconstructed_data = get_SVD_reconstructed_data_for_GUI.run(TA_data_after_start_time, components)

    start_time_index = time_delays.index(str(start_time))
    make_heatmap(SVD_reconstructed_data, time_delays[start_time_index:], wavelengths, "SVD reconstruced data " + str(components))

    return None

def plot_difference_heatmap(filename, start_time, components=[0,1,2]):
    TA_data_after_start_time, time_delays, wavelengths = get_TA_data_after_start_time.get_data_at_time(filename, start_time)
    SVD_reconstructed_data = get_SVD_reconstructed_data_for_GUI.run(TA_data_after_start_time, components)

    # to compute difference
    difference_matrix = SVD_reconstructed_data.astype(float) - TA_data_after_start_time.astype(float)

    start_time_index = time_delays.index(str(start_time))
    make_heatmap(difference_matrix, time_delays[start_time_index:], wavelengths, "Difference matrix " + str(components))

    return None

def plot_singular_values(filename, start_time, nr_of_singular_values=10, title="singular values"):
    TA_data_after_time, time_delays, wavelengths = get_TA_data_after_start_time.run(filename, start_time)

    # compute SVD - return singular values
    U, sigma, VT = scipy.linalg.svd(TA_data_after_time)
    singular_values_to_plot = sigma[:nr_of_singular_values]

    plt.style.use("seaborn")
    plt.rcParams.update({'axes.labelsize': 20.0, 'axes.titlesize': 22.0, 'legend.fontsize':20, 'xtick.labelsize':18, 'ytick.labelsize':18, "axes.edgecolor":"black", "axes.linewidth":1})

    fig = plt.figure(figsize=(10,8), dpi=50)
    xaxis = [i+1 for i in range(nr_of_singular_values)]

    ax = fig.add_subplot(1,1,1)

    ax.plot(xaxis, singular_values_to_plot, marker="o", linewidth=0, markersize=10)

    ax.set_yscale("log")
    ax.set_ylabel("log(singular value)")
    ax.set_xlabel("singular value index")
    ax.set_xticks(xaxis)
    ax.set_title(title)

    if len(singular_values_to_plot) <= 12:
        label_format = '{:,.2f}'
        value_labels = [label_format.format(x) for x in singular_values_to_plot]
        text_str = "values: "+ str(value_labels[0])
        for label in value_labels[1:]:
            text_str += "\n"+" "*10 + str(label)
        ax.text(0.8,0.5,text_str, fontsize=18, horizontalalignment='center', verticalalignment='center', transform=ax.transAxes, bbox={"facecolor": "cornflowerblue", "alpha":0.5, "pad": 4})

    fig.tight_layout()
    fig.savefig("thesis_plots/"+title+".png")

    return None

def plot_left_singular_vectors(filename, start_time, which_vectors=[0,], title="left singular vector"):
    # data preparation
    TA_data_after_time, time_delays, wavelengths = get_TA_data_after_start_time.run(filename, start_time)

    # compute SVD - return left singular vectors
    U, sigma, VT = scipy.linalg.svd(TA_data_after_time)
    retained_U_multiplied = sigma[which_vectors] * U[:, which_vectors]

    # building the figure
    label_format = '{:,.2f}'
    num_ticks = 5

    xaxis = wavelengths

    # the index of the position of xticks
    xticks = np.linspace(0, len(xaxis) - 1, num_ticks, dtype=np.int)
    # the content of labels of these xticks
    xticklabels = [float(xaxis[idx]) for idx in xticks]
    xticklabels = [label_format.format(x) for x in xticklabels]

    plt.style.use("seaborn")
    plt.rcParams.update({'axes.labelsize': 20.0, 'axes.titlesize': 22.0, 'legend.fontsize':20, 'xtick.labelsize':18, 'ytick.labelsize':18, "axes.edgecolor":"black", "axes.linewidth":1})

    fig = plt.figure(figsize=(12,6), dpi=50)         # dpi at 100 is default
    axes = plt.subplot()

    for i in range(len(which_vectors)):
        axes.plot(xaxis, retained_U_multiplied[:,i], label=rf'component: {which_vectors[i]} $\cdot$ sv{which_vectors[i]}')

    axes.set_xticks(xticks)
    axes.set_xticklabels(xticklabels)
    axes.set_title(title)
    axes.set_xlabel("wavelengths [nm]")
    axes.set_ylabel("intensity (a.u.)")
    axes.legend()

    fig.tight_layout()
    fig.savefig("thesis_plots/"+title+".png")

    return None

def plot_right_singular_vectors(filename, start_time, which_vectors=[0,], title="right singular vector"):
    # data preparation
    TA_data_after_time, time_delays, wavelengths = get_TA_data_after_start_time.run(filename, start_time)

    # compute SVD - return left singular vectors
    U, sigma, VT = scipy.linalg.svd(TA_data_after_time)
    retained_VT_multiplied = sigma[which_vectors] * VT[which_vectors, :]

    # building the figure
    label_format = '{:,.2f}'
    num_ticks = 5

    start_time_index = time_delays.index(str(start_time))
    xaxis = time_delays[start_time_index:]

    # the index of the position of xticks
    xticks = np.linspace(0, len(xaxis) - 1, num_ticks, dtype=np.int)
    # the content of labels of these xticks
    xticklabels = [float(xaxis[idx]) for idx in xticks]
    xticklabels = [label_format.format(x) for x in xticklabels]

    plt.style.use("seaborn")
    plt.rcParams.update({'axes.labelsize': 20.0, 'axes.titlesize': 22.0, 'legend.fontsize':20, 'xtick.labelsize':18, 'ytick.labelsize':18, "axes.edgecolor":"black", "axes.linewidth":1})

    fig = plt.figure(figsize=(12,6), dpi=50)         # dpi at 100 is default
    axes = plt.subplot()

    for i in range(len(which_vectors)):
        axes.plot(xaxis, retained_VT_multiplied[i,:], label=rf'component: {which_vectors[i]} $\cdot$ sv{which_vectors[i]}')

    axes.set_xticks(xticks)
    axes.set_xticklabels(xticklabels)
    axes.set_title(title+" " + str(which_vectors))
    axes.set_xlabel("time since overlap [ps]")
    axes.set_ylabel("intensity (a.u.)")
    axes.legend()

    fig.tight_layout()
    fig.savefig("thesis_plots/"+title+str(which_vectors)+".png")

    return None

if __name__ == "__main__":
    """ choose which plots you want to generate """
    # plot_orig_data_heatmap("DataFiles/data_full_0.txt", "0.0")
    # plot_SVD_reconstruction_heatmap("DataFiles/data_full_0.txt", "0.0", components=[0,1,2])
    # plot_singular_values("DataFiles/data_full_0.txt", "0.0")
    # plot_left_singular_vectors("DataFiles/data_full_0.txt", "0.0", which_vectors=[0])
    for i in range(5):
        plot_right_singular_vectors("DataFiles/data_full_0.txt", "0.0", which_vectors=[i])
    # plot_difference_heatmap("DataFiles/data_full_0.txt", "0.0", components=[0,1,2,3])