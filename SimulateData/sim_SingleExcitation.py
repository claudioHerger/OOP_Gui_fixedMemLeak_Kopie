import configparser
import ast
from numpy.random import default_rng
import numpy as np
import time
import os

import matplotlib.pyplot as plt
import seaborn as sns

class SingleExcitation():
    def __init__(self, config_file, make_plots=False) -> None:
        """
        computes Ta data matrix with ONE SINGLE initial excitation of material (the gaussians are the same for all the measurements at all time delays).\n
        simulation of components as defined in config_file.\n
        stores final matrix to file formatted for TA analysis gui.\n
        makes and stores some plots of individual simulation steps to file if make_plots = true

        Args:
            config_file (String): path to configuration (.ini) file.
            make_plots (Boolean): whether or not to make plots. Default is False.
        """
        self.config_file_name = config_file
        self.make_plots = make_plots
        self.config_file_base_name = os.path.splitext(os.path.basename(self.config_file_name))[0]
        self.save_matrix_file_name = os.getcwd()+"/simulatedData/SingleExcitation/"+self.config_file_base_name+".txt"
        self.save_heatmap_file_name = os.getcwd()+"/simulatedData/SingleExcitation/"+self.config_file_base_name+"_heatmap.png"

        self.configuration_dict = self.read_config_file()
        self.matrix_dimensions_dict = self.configuration_dict["matrix_dimensions"]
        self.components_dict = self.configuration_dict["components"]
        self.nr_of_components = len(self.components_dict["amplitudes"])
        self.noise_dict = self.configuration_dict["noise"]

        self.random_number_generator = default_rng()

        # compute time_steps and wavelengths from interval and step size
        self.wavelength_steps = self.compute_steps(self.matrix_dimensions_dict["wavelength_range"], self.matrix_dimensions_dict["wavelength_stepsize"])
        self.time_steps = self.compute_steps(self.matrix_dimensions_dict["time_range"], self.matrix_dimensions_dict["time_stepsize"])

        self.compute_data_matrix()
        self.save_and_format_data_matrix()

        return None

    # one single "excitation" is generated and used for the decay at each time step
    def compute_data_matrix(self):
        # for each component compute initial gaussian
        self.initial_gaussians = []
        for i in range(self.nr_of_components):
            self.initial_gaussians.append(self.compute_gaussian(self.components_dict["amplitudes"][i], self.wavelength_steps, self.components_dict["wavelength_expectation_values"][i], self.components_dict["wavelength_std_deviations"][i]))

        # add noise to initial gaussians
        self.noisy_initial_gaussians = []
        for gaussian in self.initial_gaussians:
            self.noisy_initial_gaussians.append(self.add_normal_noise_to_array(gaussian, noise_scale=self.noise_dict["pump_noise_scale"]))

        # for each initial gaussian compute a decay matrix
        # final matrix as sum of all decay matrices
        self.data_matrix = np.zeros((len(self.time_steps), len(self.wavelength_steps)))
        for component in range(self.nr_of_components):
            decay_constant = self.components_dict["decay_constants"][component]
            for time_step_index, time_step in enumerate(self.time_steps):
                for wavelength_index in range(len(self.wavelength_steps)):
                    data_point = self.noisy_initial_gaussians[component][wavelength_index] * np.exp(-time_step/decay_constant)
                    self.data_matrix[time_step_index, wavelength_index] += data_point + self.noise_dict["probe_noise_scale"] * self.get_rand_nrs_from_somewhat_normal_distribution()

        if self.make_plots:
            self.make_and_save_plots(self.wavelength_steps, self.time_steps)

        return None

    def compute_steps(self, interval, step_size):
        nr_of_steps = (interval[1] - interval[0]) / step_size
        return np.linspace(interval[0], interval[1], int(nr_of_steps))

    def get_rand_nrs_from_somewhat_normal_distribution(self, how_many_numbers=1):
        return self.random_number_generator.normal(loc=0.0, scale=2.0, size=how_many_numbers)

    def compute_gaussian(self, amplitude, steps, exp_value, std_deviation):
        gaussian = np.array(amplitude * np.exp(-((steps - exp_value)**2)/(2*(std_deviation**2))), dtype=float)
        return gaussian

    def add_normal_noise_to_array(self, array, noise_scale=1):
        noisy_array = array + noise_scale*self.get_rand_nrs_from_somewhat_normal_distribution(how_many_numbers=len(array))
        return noisy_array

    def compute_exp_decay_amplitude(self, time_step, decay_constant):
        return np.exp(-time_step/decay_constant)

    def read_config_file(self) -> dict:
        conf_parser = configparser.ConfigParser()
        conf_parser.read(self.config_file_name)

        configuration_dict = {}
        for section in conf_parser.sections():
            configuration_dict[section] = {}
            for key in conf_parser[section]:
                configuration_dict[section][key] = ast.literal_eval(conf_parser[section][key])

        return configuration_dict

    def save_and_format_data_matrix(self):
        self.formatted_data_matrix = np.zeros((len(self.time_steps)+1, len(self.wavelength_steps)+1))
        self.formatted_data_matrix[0, 1:] = self.wavelength_steps
        self.formatted_data_matrix[1:, 0] = self.time_steps
        self.formatted_data_matrix[1:, 1:] = self.data_matrix

        np.savetxt(self.save_matrix_file_name, self.formatted_data_matrix, delimiter = '\t', fmt='%.7e')

        return None

    def make_and_save_plots(self, wavelengths, time_delays):
        data = self.data_matrix.T.astype(float)

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
        ax = sns.heatmap(data, cmap=cmap, cbar_kws={'label': 'intensity a.u.'})
        cbar = ax.collections[0].colorbar
        cbar.ax.yaxis.label.set_size(14)        # taking a detour to set the fontsize of colorbar label

        ax.set_yticks(yticks)
        ax.set_yticklabels(yticklabels)
        ax.set_xticks(xticks)
        ax.set_xticklabels(xticklabels, rotation=30)

        ax.set_ylabel("wavelengths", fontsize=14)
        ax.set_xlabel("time since excitation", fontsize=14)
        # ax.set_title(type(self).__name__)
        ax.set_title("coarsly simulated time-resolved spectroscopy data", fontsize = 15)

        plt.tight_layout()
        plt.savefig(self.save_heatmap_file_name)
        plt.close()

        return None

if __name__ == "__main__":
    # start = time.time()
    # test_ta_sim_obj = SingleExcitation(os.getcwd()+"/configFiles/test/test_config_file.ini", make_plots=True)
    # print(f'SingleExcitation excecution time: {time.time()-start}')

    # dir_path = os.getcwd()+"/configFiles/wavelength_overlap/"
    dir_path = os.getcwd()+"/configFiles/"

    files_in_dir = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
    for file in files_in_dir:
        print()
        print(f'file: {file}')
        start = time.time()
        multi_excitation_obj = SingleExcitation(dir_path+file, make_plots=True)
        print(f'SingleExcitation excecution time: {time.time()-start}')