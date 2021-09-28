import os
import gc

import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
import seaborn as sns

# OO backend (Tkinter) tkagg() function:
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from FunctionsUsedByPlotClasses import get_SVDGFit_parameters
from SupportClasses import ToolTip

import tkinter as tk

class CompareWindow(tk.Toplevel):

    def __init__(self, parent, user_defined_fit_function_in_use, tab_index, components, time_steps, rightSVs, singular_values, fit_result_decay_times, fit_result_amplitudes, data_file_name, save_dir, parsed_summands_of_user_defined_fit_function=None):
        """Compare the right singular vectors (kinetics) of data matrix with the fit results in a plot.

        Args:
            parent (GUIApp): parent is the Gui App that creates the instance of this class.
            user_defined_fit_function_in_use (boolean): whether or not the user used a user defined fit function.
            tab_index (int): used in title of Toplevel, so that one knows to which tab this toplevel belongs.
            components (list(int)): list of SVD components used in fit.
            time_steps (list): time steps from original data file used in fit.
            rightSVs (arraylike): 2d-array containing the right singular vectors used in fit.
            singular_values (list): list of singular values of selected SVD components used in fit.
            fit_results_decay_times (dict[float]): dict of fit result decay times.
            fit_results_amplitudes (dict[float]): dictionary containing resulting amplitudes from fit.
            data_file_name (String): name of data file used to conduct fit.
            save_dir (String): path to directory to save figure to.
            parsed_summands_of_user_defined_fit_function (list of Strings, Default is None): the parsed summands of the user defined fit function.
        """
        super().__init__(parent)
        self.parent = parent
        self.tab_index = tab_index
        self.components = components
        self.time_steps_strings = time_steps
        self.time_steps = [float(time_step) for time_step in time_steps]

        self.rightSVs = rightSVs
        self.singular_values = singular_values
        self.decay_times = fit_result_decay_times
        self.amplitudes = fit_result_amplitudes
        self.data_file_name = data_file_name
        self.save_dir = save_dir

        self.user_defined_fit_function_in_use = user_defined_fit_function_in_use
        self.parsed_summands_of_user_defined_fit_function = parsed_summands_of_user_defined_fit_function
        self.first_plot = True

        return None

    def run(self):
        self.put_check_buttons_on_window()
        self.figure, self.axes, self.figure_canvas = self.make_frame_figure_and_axes()
        self.btn_quit = tk.Button(self, text="close", command=self.delete_attrs_and_destroy)
        self.btn_update_plot = tk.Button(self, text="update plot", command=self.update_axes)
        self.btn_save_curr_figure = tk.Button(self, text="save current figure", command=self.save_current_figure_to_file)

        self.weighted_rSVs = self.compute_weighted_rSVs()

        self.title('Right singular vectors vs fit reconstruction for difference tab: ' + str(self.tab_index + 1) + " - data file: "+os.path.basename(self.data_file_name))

        self.reconstructed_rSVs_from_fit_results = self.reconstruct_rSVs_from_fit_results()

        self.update_axes()

        self.figure_canvas.get_tk_widget().grid(row=0, column=0)
        self.btn_save_curr_figure.grid(row=2, column=0, sticky="sw", pady=3)
        self.btn_update_plot.grid(row=2, column=len(self.components)-1, sticky="se", padx=3 , pady=3)
        self.btn_quit.grid(row=2, column=len(self.components), sticky="se", pady=3)

        return None

    def make_frame_figure_and_axes(self):
        frm_figure = tk.Frame(self)
        frm_figure.grid(row=0, columnspan=len(self.components))

        # some styling for plots
        matplotlib.style.use("seaborn")
        matplotlib.rcParams.update({'axes.labelsize': 12.0, 'axes.titlesize': 14.0, 'xtick.labelsize':10, 'ytick.labelsize':12.0, "axes.edgecolor":"black", "axes.linewidth":1})

        fig = Figure(figsize=(7,5))
        axes = fig.add_subplot(1,1,1)
        canvas = FigureCanvasTkAgg(fig, frm_figure)

        return fig, axes, canvas

    def put_check_buttons_on_window(self):
        self.check_button_variables = [tk.IntVar(0) for _ in self.components]
        self.check_button_variables[0].set(1)
        self.check_buttons = [tk.Checkbutton(self, text=str(self.components[component_index]), onvalue=1, offvalue=0, variable=self.check_button_variables[component_index]) for component_index in range(len(self.components))]
        for check_button_index in range(len(self.components)):
            self.check_buttons[check_button_index].grid(row=1, column=check_button_index, sticky="sw")

        return None

    def compute_weighted_rSVs(self):
        weighted_rSVs = np.zeros((len(self.components), len(self.time_steps)))
        for component_index in range(len(self.components)):
            sing_value = self.singular_values[component_index]
            weighted_rSVs[component_index, :] = sing_value*self.rightSVs[component_index, :]

        return weighted_rSVs

    def reconstruct_rSVs_from_fit_results(self):
        reconstructed_rSVs_from_fit_results = np.zeros(shape=(len(self.components), len(self.time_steps)))
        decay_constants = list(self.decay_times.values())
        time_steps_array = self.time_steps = np.array(self.time_steps)

        for component_index in range(len(self.components)):
            curr_amplitudes = []
            for component in self.components:
                curr_amplitudes.append(self.amplitudes[f'amp_rSV{component_index}_component{component}'])
            if not self.user_defined_fit_function_in_use:
                reconstructed_rSVs_from_fit_results[component_index, :] = get_SVDGFit_parameters.model_func(time_steps_array, curr_amplitudes, decay_constants, index_of_first_increased_time_interval=0, gaussian_for_convolution=0)
            else:
                reconstructed_rSVs_from_fit_results[component_index, :] = get_SVDGFit_parameters.model_func_user_defined(time_steps_array, curr_amplitudes, decay_constants, self.components, self.parsed_summands_of_user_defined_fit_function)

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

        self.currently_plotted_components = [component for component_index, component in enumerate(self.components) if self.check_button_variables[component_index].get() == 1]
        for i in range(len(self.components)):
            if (self.check_button_variables[i].get() == 1):
                self.axes.plot(self.xaxis, self.weighted_rSVs[i,:], label=f'component: {self.components[i]}', color=sns.color_palette("Set2")[i])
                varied_color = (sns.color_palette("Set2")[i][0], sns.color_palette("Set2")[i][1]*0.1, sns.color_palette("Set2")[i][2]*(1.1))
                self.axes.plot(self.xaxis, self.reconstructed_rSVs_from_fit_results[i,:], label=f'fit comp: {self.components[i]}', linestyle="--", color=varied_color)

        self.axes.set_xticks(self.rightSVs_xticks)
        self.axes.set_xticklabels(self.rightSVs_xticklabels, rotation=0)
        self.axes.set_title("right singular vectors * singular value")
        self.axes.set_xlabel("time delays")
        self.axes.set_ylabel("amplitude a.u.")
        self.axes.legend(fontsize=8)

        self.figure.tight_layout()

        # actually draw the plot
        self.figure.canvas.draw_idle()

    def save_current_figure_to_file(self):
        print("saving current rightSVs vs fit figure to file!")

        # check if directory exists:
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

        # save current figures:
        self.figure.savefig(self.save_dir+"/rightSVs_Vs_Fit_"+str(self.currently_plotted_components)+".png")

        return None

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
