import os
import gc
from datetime import datetime
from matplotlib import colors

import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
import seaborn as sns

# OO backend (Tkinter) tkagg() function:
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from FunctionsUsedByPlotClasses import get_SVDGFit_parameters
from SupportClasses import ToolTip, saveData

import tkinter as tk

class CompareWindow(tk.Toplevel):

    def __init__(self, parent, is_target_model, tab_index, components, time_steps, rightSVs, singular_values, decay_times_parameter_values, amplitudes_parameter_values, data_file_name, save_dir, parsed_summands_of_user_defined_fit_function=None, is_from_initial_values_window=None, start_time=None, matrix_bounds_dict=None):
        """Compare the right singular vectors (kinetics) of data matrix with the fit results in a plot.

        Args:
            parent (GUIApp): parent is the Gui App that creates the instance of this class.
            is_target_model (boolean): whether or not the user used a user defined fit function.
            tab_index (int): used in title of Toplevel, so that one knows to which tab this toplevel belongs.
            components (list(int)): list of SVD components used in fit.
            time_steps (list): time steps from original data file used in fit.
            rightSVs (arraylike): 2d-array containing the right singular vectors used in fit.
            singular_values (list): list of singular values of selected SVD components used in fit.
            decay_times_parameter_values (dict[float]): dict of decay times parameter values.
            amplitudes_parameter_values (dict[float]): dictionary of amplitudes parameter values.
            data_file_name (String): name of data file used to conduct fit.
            save_dir (String): path to directory to save figure to.
            parsed_summands_of_user_defined_fit_function (list of Strings, Default is None): the parsed summands of the user defined fit function.
            is_from_initial_values_window (boolean, Default is None): whether or not the window is opened from initial fit params value window.
        """
        super().__init__(parent)
        self.parent = parent
        self.tab_index = tab_index
        self.components_list = components
        self.time_steps_strings = time_steps
        self.time_steps = [float(time_step) for time_step in time_steps]

        self.rightSVs = rightSVs
        self.singular_values = singular_values
        self.decay_times = decay_times_parameter_values
        self.amplitudes = amplitudes_parameter_values
        self.data_file_name = data_file_name
        self.save_dir = save_dir

        self.is_target_model = is_target_model
        self.parsed_summands_of_user_defined_fit_function = parsed_summands_of_user_defined_fit_function
        self.first_plot = True

        self.is_from_initial_values_window = is_from_initial_values_window
        self.start_time = start_time
        self.matrix_bounds_dict = matrix_bounds_dict

        return None

    def run(self):
        self.put_check_buttons_on_window()
        self.figure, self.axes, self.figure_canvas = self.make_frame_figure_and_axes()
        self.btn_quit = tk.Button(self, text="close", command=self.delete_attrs_and_destroy)
        self.btn_update_plot = tk.Button(self, text="update plot", command=self.update_axes)
        self.btn_save_curr_figure = tk.Button(self, text="save current figure", command=self.save_current_figure_to_file)

        self.weighted_rSVs = self.compute_weighted_rSVs()

        if self.is_from_initial_values_window:
            self.title('Right singular vectors vs fit function with entered intial fit parameter values - data file: ' + os.path.basename(self.data_file_name))
            self.reconstruct_rSVs_from_fit_results_using_intial_values(self.decay_times, self.amplitudes)
        else:
            self.title('Right singular vectors vs fit reconstruction for difference tab: ' + str(self.tab_index + 1) + " - data file: "+os.path.basename(self.data_file_name))
            self.reconstructed_rSVs_from_fit_results = self.reconstruct_rSVs_from_fit_results()

        self.update_axes()

        self.figure_canvas.get_tk_widget().grid(row=0, column=0)
        self.btn_save_curr_figure.grid(row=2, column=0, sticky="sw", pady=3)
        self.btn_update_plot.grid(row=2, column=len(self.components_list)-1, sticky="se", padx=3 , pady=3)
        self.btn_quit.grid(row=2, column=len(self.components_list), sticky="se", pady=3)

        return None

    def make_frame_figure_and_axes(self):
        frm_figure = tk.Frame(self)
        frm_figure.grid(row=0, columnspan=len(self.components_list))

        # some styling for plots
        matplotlib.style.use("default")
        matplotlib.rcParams.update({'axes.labelsize': 14.0, 'axes.titlesize': 14.0, 'xtick.labelsize':14, 'ytick.labelsize':14, 'legend.fontsize':12, "axes.edgecolor":"black", "axes.linewidth":1, "axes.grid": True, "grid.linestyle":"--"})

        fig = Figure(figsize=(7,5))
        axes = fig.add_subplot(1,1,1)
        canvas = FigureCanvasTkAgg(fig, frm_figure)

        return fig, axes, canvas

    def put_check_buttons_on_window(self):
        self.check_button_variables = [tk.IntVar() for _ in self.components_list]
        self.check_button_variables[0].set(1)
        self.check_buttons = [tk.Checkbutton(self, text=str(self.components_list[component_index]), onvalue=1, offvalue=0, variable=self.check_button_variables[component_index]) for component_index in range(len(self.components_list))]
        for check_button_index in range(len(self.components_list)):
            self.check_buttons[check_button_index].grid(row=1, column=check_button_index, sticky="sw")

        return None

    def compute_weighted_rSVs(self):
        weighted_rSVs = np.zeros((len(self.components_list), len(self.time_steps)))
        for component_index in range(len(self.components_list)):
            sing_value = self.singular_values[component_index]
            weighted_rSVs[component_index, :] = sing_value*self.rightSVs[component_index, :]

        return weighted_rSVs

    def reconstruct_rSVs_from_fit_results_using_intial_values(self, decay_times, amplitudes):
        reconstructed_rSVs_from_fit_results = np.zeros(shape=(len(self.components_list), len(self.time_steps)))
        self.decay_times = decay_times
        decay_constants = list(self.decay_times.values())
        self.amplitudes = amplitudes
        time_steps_array = self.time_steps = np.array(self.time_steps)

        for component_index in range(len(self.components_list)):
            curr_amplitudes = []
            for component in self.components_list:
                curr_amplitudes.append(self.amplitudes[f'amp_rSV{component_index}_component{component}'])
            if not self.is_target_model:
                reconstructed_rSVs_from_fit_results[component_index, :] = get_SVDGFit_parameters.model_func(time_steps_array, curr_amplitudes, decay_constants, index_of_first_increased_time_interval=0, gaussian_for_convolution=0)
            else:
                reconstructed_rSVs_from_fit_results[component_index, :] = get_SVDGFit_parameters.model_func_user_defined(time_steps_array, curr_amplitudes, decay_constants, self.components_list, self.parsed_summands_of_user_defined_fit_function)

        self.reconstructed_rSVs_from_fit_results = reconstructed_rSVs_from_fit_results
        return reconstructed_rSVs_from_fit_results

    def reconstruct_rSVs_from_fit_results(self):
        reconstructed_rSVs_from_fit_results = np.zeros(shape=(len(self.components_list), len(self.time_steps)))
        decay_constants = list(self.decay_times.values())
        time_steps_array = self.time_steps = np.array(self.time_steps)

        for component_index in range(len(self.components_list)):
            curr_amplitudes = []
            for component in self.components_list:
                curr_amplitudes.append(self.amplitudes[f'amp_rSV{component_index}_component{component}'])
            if not self.is_target_model:
                reconstructed_rSVs_from_fit_results[component_index, :] = get_SVDGFit_parameters.model_func(time_steps_array, curr_amplitudes, decay_constants, index_of_first_increased_time_interval=0, gaussian_for_convolution=0)
            else:
                reconstructed_rSVs_from_fit_results[component_index, :] = get_SVDGFit_parameters.model_func_user_defined(time_steps_array, curr_amplitudes, decay_constants, self.components_list, self.parsed_summands_of_user_defined_fit_function)

        return reconstructed_rSVs_from_fit_results

    def update_axes(self):
        self.axes.clear()

        if self.first_plot:
            self.xaxis = self.time_steps_strings

            self.rightSVs_num_ticks = 5
            self.rightSVs_label_format = '{:.1f}'
            self.rightSVs_xticks = np.linspace(0, len(self.xaxis) - 1, self.rightSVs_num_ticks, dtype=np.int)
            self.rightSVs_xticklabels = [float(self.xaxis[idx]) for idx in self.rightSVs_xticks]
            self.rightSVs_xticklabels = [self.rightSVs_label_format.format(x) for x in self.rightSVs_xticklabels]

            self.first_plot = False

        cmap =  matplotlib.cm.get_cmap("tab20")
        self.currently_plotted_components = [component for component_index, component in enumerate(self.components_list) if self.check_button_variables[component_index].get() == 1]
        for i in range(len(self.components_list)):
            if (self.check_button_variables[i].get() == 1):
                self.axes.plot(self.xaxis, self.weighted_rSVs[i,:], label=f"rSV {self.components_list[i]}", color=cmap((2*i+1)*(1/20)))
                self.axes.plot(self.xaxis, self.reconstructed_rSVs_from_fit_results[i,:], label=f'fit for rSV {self.components_list[i]}', linestyle="--", color=cmap((2*i)*(1/20)))

        self.axes.set_xticks(self.rightSVs_xticks)
        self.axes.set_xticklabels(self.rightSVs_xticklabels, rotation=0)
        self.axes.set_title("weighted right singular vectors vs fit")
        if self.is_from_initial_values_window:
            self.axes.set_title("weighted rSVs vs fit function using initial fit parameter values")
        self.axes.set_xlabel("time delays")
        self.axes.set_ylabel("amplitude")
        self.axes.legend(ncol=2, labelspacing=0.1)

        self.figure.tight_layout()

        self.figure.canvas.draw_idle()

    def save_current_figure_to_file(self):
        print("saving current rightSVs vs fit figure to file!")

        if self.is_from_initial_values_window:
            self.save_current_figure_and_more_data_to_file()
            return None

        # check if directory exists:
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

        saveData.make_log_file(self.save_dir, filename=self.data_file_name, start_time=self.start_time, components=self.components_list, matrix_bounds=self.matrix_bounds_dict, parsed_target_model_summands=self.parsed_summands_of_user_defined_fit_function)

        # save current figure:
        self.figure.savefig(self.save_dir+"/rightSVs_"+str(self.currently_plotted_components)+"_Vs_Fit.png")

        data_dict = {'initial_decay_constants_values': self.decay_times, 'initial_amplitudes_values':self.amplitudes, 'right_SVectors':self.rightSVs, 'singular_values':self.singular_values}
        if self.is_target_model:
            data_dict['user_defined_model_summands'] = self.parsed_summands_of_user_defined_fit_function
        saveData.save_result_data(self.save_dir, data_dict)

        return None

    def save_current_figure_and_more_data_to_file(self):
        print("saving figure and data corresponding to intial fit parameter values window")

        today = datetime.now()
        second = today.strftime('%S')
        hour = today.strftime('%H')
        minute = today.strftime('%M')

        final_dir = self.save_dir+ "saved_at_"+str(hour)+"h_"+str(minute)+"min_"+str(second)+"sec"

        # check if directory exists:
        if not os.path.exists(final_dir):
            os.makedirs(final_dir)

        saveData.make_log_file(final_dir, filename=self.data_file_name, start_time=self.start_time, components=self.components_list, matrix_bounds=self.matrix_bounds_dict, parsed_target_model_summands=self.parsed_summands_of_user_defined_fit_function)

        data_dict = {'initial_decay_constants_values': self.decay_times, 'initial_amplitudes_values':self.amplitudes, 'right_SVectors':self.rightSVs, 'singular_values':self.singular_values}
        if self.is_target_model:
            data_dict['user_defined_model_summands'] = self.parsed_summands_of_user_defined_fit_function
        saveData.save_result_data(final_dir, data_dict)

        # save current figure:
        self.figure.savefig(final_dir+"/rightSVs_"+str(self.currently_plotted_components)+"_Vs_initial_values_fit.png")

        pass

    def delete_attrs_and_destroy(self):
        self.destroy()
        self.delete_attrs()

        return None

    def delete_attrs(self):
        attr_lst = list(vars(self))
        attr_lst.remove('parent')
        for attr in attr_lst:
            delattr(self, attr)

        del attr_lst

        gc.collect()

        return None
