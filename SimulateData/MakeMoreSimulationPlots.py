import matplotlib
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib
import os
import scipy

from SimulateData import sim_MultiExcitation
from FunctionsUsedByPlotClasses import get_TA_data_after_start_time


def plot_arrays(x_axis, y_values, x_name, y_name, title="", file_name="", save_dir=""):

    colors = ["tab:blue", "tab:orange", "tab:cyan", "tab:olive"]

    fig, ax = plt.subplots()

    try:
        nr_of_y_axes = y_values.shape[1]
        for i in range(nr_of_y_axes):
            ax.plot(x_axis, y_values[:, i], color=colors[i%nr_of_y_axes])
    except IndexError:
        ax.plot(x_axis, y_values, color=colors[0])

    ax.set_xlabel(x_name)
    ax.set_ylabel(y_name)
    ax.set_title(title)

    plt.grid(color='grey', linestyle='--', linewidth=1, alpha=0.5)
    plt.tight_layout()
    plt.savefig(save_dir+file_name+".png")
    plt.close()

    return None

def plot_arrays_OOP(x_axis, y_values, x_name, y_name, x_ticks="", x_ticklabels="", title="", file_name="", save_dir="", legend_labels=["legend"]):

    # do not know how to set grid in oop approach other than via rcParams
    matplotlib.rcParams.update({"axes.grid" : True, "grid.color": "grey", "grid.alpha": 0.5, "grid.linewidth":1, "grid.linestyle": "--"})

    colors = ["tab:blue", "tab:orange", "tab:cyan", "tab:olive"]

    fig = matplotlib.figure.Figure(tight_layout=True, figsize=(10,6))
    ax = fig.add_subplot(1,1,1)

    try:
        nr_of_y_axes = y_values.shape[1]
        for i in range(nr_of_y_axes):
            ax.plot(x_axis, y_values[:, i], color=colors[i%nr_of_y_axes], label=legend_labels[i])
    except IndexError:
        ax.plot(x_axis, y_values, color=colors[0], label=legend_labels[0])

    ax.set_xlabel(x_name)
    ax.set_ylabel(y_name)
    if x_ticklabels != "":
        ax.set_xticks(x_ticks)
        ax.set_xticklabels(x_ticklabels)
    ax.set_title(title)
    ax.legend()

    fig.savefig(save_dir+file_name+".png")

    return None

def plot_initial_gaussian_from_MultiExcitation_object(simulation_config_file_path="", save_dir=""):

    # initialize simulation object, i.e. read configuration file etc
    sim_obj = sim_MultiExcitation.MultiExcitation(simulation_config_file_path, make_plots=False)

    # get the data for plot
    x_values = sim_obj.wavelength_steps
    initial_gaussian_with_noise = np.zeros((1, len(x_values)))
    initial_gaussian = np.zeros((1, len(x_values)))
    for i in range(sim_obj.nr_of_components):
        initial_gaussian_with_noise += sim_obj.add_normal_noise_to_array(sim_obj.compute_gaussian(sim_obj.components_dict["amplitudes"][i], sim_obj.wavelength_steps, sim_obj.components_dict["wavelength_expectation_values"][i], sim_obj.components_dict["wavelength_std_deviations"][i]), noise_scale=sim_obj.pump_noise_scale)
        initial_gaussian += sim_obj.compute_gaussian(sim_obj.components_dict["amplitudes"][i], sim_obj.wavelength_steps, sim_obj.components_dict["wavelength_expectation_values"][i], sim_obj.components_dict["wavelength_std_deviations"][i])

    # single array
    plot_arrays_OOP(x_values, initial_gaussian_with_noise.flatten(), "wavelengths", "intensity", title="initial \"excitation\"", file_name=os.path.splitext(os.path.basename(simulation_config_file_path))[0], save_dir=save_dir, legend_labels=["with noise"])

    # two arrays plot
    y_values_both_arrays = np.zeros((len(x_values),2))
    y_values_both_arrays[:, 0] = initial_gaussian_with_noise
    y_values_both_arrays[:, 1] = initial_gaussian
    plot_arrays_OOP(x_values, y_values_both_arrays, "wavelengths", "intensity", title="initial \"excitation\"", file_name=os.path.splitext(os.path.basename(simulation_config_file_path))[0]+"_v2", save_dir=save_dir, legend_labels=["with noise", "without noise"])

def plot_left_singular_vectors(data_file="", start_time="0.0", which_vectors=[0,], title="left singular vector", save_dir=""):
    # data preparation
    TA_data_after_time, time_delays, wavelengths = get_TA_data_after_start_time.run(data_file, start_time)

    # compute SVD - return left singular vectors
    U, sigma, VT = scipy.linalg.svd(TA_data_after_time)
    retained_U_multiplied = sigma[which_vectors] * U[:, which_vectors]

    label_format = '{:,.2f}'
    num_ticks = 10

    xaxis = wavelengths
    # the index of the position of xticks
    xticks = np.linspace(0, len(xaxis) - 1, num_ticks, dtype=np.int)
    # the content of labels of these xticks
    xticklabels = [float(xaxis[idx]) for idx in xticks]
    xticklabels = [label_format.format(x) for x in xticklabels]

    plot_arrays_OOP(wavelengths, retained_U_multiplied, "wavelengths", "intensity", x_ticks=xticks, x_ticklabels=xticklabels, title="left singular vectors", file_name=os.path.splitext(os.path.basename(data_file))[0]+"_leftSVs", save_dir=save_dir, legend_labels=[rf'component: {which_vectors[i]} $\cdot$ sv{which_vectors[i]}' for i in which_vectors])

    return None

if __name__ == "__main__":

    """ initial gaussians plot """
    cur_working_dir = os.getcwd()
    simulations_dir = cur_working_dir + "/SimulateData/"
    config_files_dir = simulations_dir + "/configFiles/"
    wavelength_overlap_dir = config_files_dir + "/wavelength_overlap/"
    simulation_number = 1
    config_file = wavelength_overlap_dir + "overlap_wavelength"+str(simulation_number)+".ini"
    save_dir = cur_working_dir + "/SimulateData/moreSimulationPlots/"
    plot_initial_gaussian_from_MultiExcitation_object(simulation_config_file_path=config_file,  save_dir=save_dir)

    """ left Singular vectors plot """
    " might have to rerun simulation to get currently valid .txt data file "
    cur_working_dir = os.getcwd()
    simulations_data_dir = cur_working_dir + "/SimulateData/simulatedData/MultiExcitation/"
    simulation_number = 1
    data_file = simulations_data_dir + "overlap_wavelength"+str(simulation_number)+".txt"
    save_dir = cur_working_dir + "/SimulateData/moreSimulationPlots/"
    plot_left_singular_vectors(data_file, start_time="0.0", which_vectors=[0,1, ], save_dir=save_dir)
