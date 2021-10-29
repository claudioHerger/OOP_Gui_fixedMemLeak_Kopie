#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" A module to produce a plot of via SVD-assisted-GlobalFit-reconstructed data on the GUI.
"""
import gc
import numpy as np
import seaborn as sns
import tkinter as tk
import os
import lmfit
import re
import ast

# my own modules
from FunctionsUsedByPlotClasses import get_DAS_from_lSVs_res_amplitudes, get_TA_data_after_start_time, get_retained_rightSVs_leftSVs_singularvs, get_SVDGFit_parameters
from FunctionsUsedByPlotClasses import get_closest_nr_from_array_like, get_SVDGF_reconstructed_data
from SupportClasses import ToolTip, saveData, SmallToolbar
from ToplevelClasses import Kinetics_Spectrum_Toplevel, new_decay_times_Toplevel, CompareRightSVsWithFit_Toplevel

class SVDGF_Heatmap():
    def __init__(self, parent, filename, matrix_bounds_dict, components_list, temp_resolution, time_zero, tab_idx, tab_idx_difference, initial_fit_parameter_values, user_defined_fit_function, colormaps_dict, target_model_configuration_file):
        """A class to make a heatmap of via SVD_GlobalFit reconstructed TA data.
        * the (default, i.e. non user defined) global fit should:\n
            # fit the selection (the selected components)\n
            # of right_singular_vector * singular_value to a fit function\n
            # composed of a sum of exponential decays * the convolution factor\n
            # the number of exponential decays is determined by the number of selected components\n
            # the decay constants are shared fit parameters for all the right singular vectors\n
            # the amplitudes of the exp decays are individual fit parameters\n
        * the fit results are:\n
            # the decay constants and the amplitudes of the exp decays.\n
            # using the resulting amplitudes, the DAS (decay associated spectra) will be computed,\n
            # from those the original data will be reconstructed as the sum: DAS_i(lambda)*exp(-t/decay_constant_i)

        Args:
            parent (GuiApp): the Gui App that creates the instance of this class.
            filename (str): full path of the datafile to be reconstructed
            matrix_bounds_dict (dict): contains the indeces that dictate the which part of complete data matrix to use
            components_list (list of ints): list of integers that represent the SVD components to be used for the reconstruction
            temp_resolution (float): number that represents the temporal resolution of the used detector setup in data collection (FWHM) (might be used for convolution in fit function)
            time_zero (float): number used in the convolution of the fitting function (convolution might not be implemented)
            tab_idx (int): the index of the tab of the ttk notebook of the GUI, (on which the SVDGF heatmap will be put)
            tab_idx_difference (int):the index of the tab of the ttk notebook of the GUI, (on which the difference heatmap will be put)
            initial_fit_parameter_values (dict): the dictionary that defines the initial values for the fit parameters
            user_defined_fit_function (bool): True if you want to use the user defined fit function
            colormaps_dict (dict): dictionary containing the colormap names for the heatmaps
            target_model_configuration_file (string): path to target model configuration file

        Returns:
            NoneType: None
        """

        self.parent = parent
        self.fit_method_name = self.parent.get_fit_method_name()
        self.notebook_container_SVDGF = self.parent.nbCon_SVDGF
        self.notebook_container_diff = self.parent.nbCon_difference

        self.filename = filename
        self.matrix_bounds_dict = matrix_bounds_dict
        if not self.matrix_bounds_dict == {}:
            self.min_wavelength_index = self.matrix_bounds_dict["min_wavelength_index"]
            self.max_wavelength_index = self.matrix_bounds_dict["max_wavelength_index"]
            self.min_time_delay_index = self.matrix_bounds_dict["min_time_delay_index"]
            self.max_time_delay_index = self.matrix_bounds_dict["max_time_delay_index"]
        self.tab_idx = tab_idx
        self.tab_idx_difference = tab_idx_difference
        self.components_list = components_list
        self.temp_resolution = temp_resolution
        self.time_zero = time_zero

        self.use_user_defined_fit_function = user_defined_fit_function
        self.target_model_configuration_file = target_model_configuration_file

        self.DAS_to_update_with = [i for i in range(len(self.components_list))]
        self.indeces_for_DAS_matrix = self.DAS_to_update_with

        # needed if the user wants to update the resulting heatmaps with a user defined selection of DAS and decay times
        self.SVDGF_reconstructed_data_selected_DAS = None
        self.user_selected_decay_times = None

        self.initial_fit_parameter_values = initial_fit_parameter_values
        self.colormaps_dict = colormaps_dict

        return None

    def return_gui_to_initial_state(self):
        self.parent.return_some_gui_widgets_to_initial_state(button=self.parent.btn_show_SVDGF_reconstructed_data_heatmap, label=self.parent.lbl_reassuring_SVDGF, tab_control=self.notebook_container_SVDGF.tab_control)
        self.parent.return_some_gui_widgets_to_initial_state(tab_control=self.notebook_container_diff.tab_control)
        self.delete_attributes()

        return None

    def make_reconstruction_plot(self, update_with_selected_DAS=False):
        sns.set(font_scale = 1.3, rc={"xtick.bottom" : True, "ytick.left" : True})

        # create axes on parent.figure with correct index:
        self.axes = self.notebook_container_SVDGF.figs[self.tab_idx].add_subplot(1,1,1)
        # adjust figsize as computed correspondingly to gui size:
        # stupid hack for stupid problem: not done when plot is updated with selected DAS,
        # as that leads to a strange plot size for reasons unknown
        if not update_with_selected_DAS:
            self.axes.get_figure().set_figwidth(self.parent.heatmaps_figure_geometry_list[0])
            self.axes.get_figure().set_figheight(self.parent.heatmaps_figure_geometry_list[1])

        self.data = self.SVDGF_reconstructed_data.astype(float)
        if update_with_selected_DAS:
            self.data = self.SVDGF_reconstructed_data_selected_DAS.astype(float)
        self.base_filename = os.path.splitext(os.path.basename(self.filename))[0]
        self.time_index = self.time_delays.index(str(self.start_time))
        self.time_delays = self.time_delays[self.time_index:]

        self.num_ticks = 10
        self.label_format = '{:.2f}'

        # the index of the position of self.yticks
        self.yticks = np.linspace(0, len(self.wavelengths) - 1, self.num_ticks, dtype=np.int)
        self.xticks = np.linspace(0, len(self.time_delays) - 1, self.num_ticks, dtype=np.int)
        # the content of labels of these self.yticks
        self.yticklabels = [float(self.wavelengths[idx]) for idx in self.yticks]
        self.xticklabels = [float(self.time_delays[idx]) for idx in self.xticks]

        self.yticklabels = [self.label_format.format(x) for x in self.yticklabels]
        self.xticklabels = [self.label_format.format(x) for x in self.xticklabels]

        try:
            cmap_name = self.colormaps_dict["Fit"]
            if cmap_name == "default":
                self.cm = sns.diverging_palette(220, 20, s=300, as_cmap=True)
            else:
                self.cm = sns.color_palette(cmap_name, as_cmap=True)
        except (ValueError, KeyError):
            print("Could not assign the selected colormap. Using a default one. Try to change the colormaps via button.")
            # default to this cmap
            self.cm = sns.diverging_palette(320, 20, s=300, as_cmap=True)

        sns.heatmap(self.data, ax = self.axes, cbar_kws={'label': 'amplitude'}, cmap=self.cm)

        self.axes.set_yticks(self.yticks)
        self.axes.set_yticklabels(self.yticklabels, fontsize=14)
        self.axes.set_xticks(self.xticks)
        self.axes.set_xticklabels(self.xticklabels, rotation=30, fontsize=14)

        self.axes.set_ylabel("wavelengths", fontsize=16)
        self.axes.set_xlabel("time since overlap", fontsize=16)

        title_string = self.base_filename+" SVDGF data, fit comps: " + str(self.components_list) + " DAS: " + str(self.indeces_for_DAS_matrix)
        if self.use_user_defined_fit_function:
            title_string = "user defined fit function was used\n"  + title_string
        if update_with_selected_DAS:
            title_string = r"updated! $\tau_i$ ="+str(['{:.4f}'.format(float(self.user_selected_decay_times[x])) for x in self.indeces_for_DAS_matrix])+"\n"  + title_string
        self.axes.set_title(title_string)

        self.notebook_container_SVDGF.figs[self.tab_idx].tight_layout()

        return None

    def make_difference_plot(self, update_with_selected_DAS=False):
        sns.set(font_scale = 1.3, rc={"xtick.bottom" : True, "ytick.left" : True})

        self.axes_difference = self.notebook_container_diff.figs[self.tab_idx_difference].add_subplot(1,1,1)
        # adjust figsize as computed correspondingly to gui size:
        # stupid hack for stupid problem: not done when plot is updated with selected DAS,
        # as that leads to a strange plot size for reasons unknown
        if not update_with_selected_DAS:
            self.axes_difference.get_figure().set_figwidth(self.parent.heatmaps_figure_geometry_list[0])
            self.axes_difference.get_figure().set_figheight(self.parent.heatmaps_figure_geometry_list[1])

        self.difference_data = self.difference_matrix_selected_DAS.astype(float)

        self.num_ticks = 10
        self.label_format = '{:.2f}'

        # the index of the position of self.yticks
        self.yticks = np.linspace(0, len(self.wavelengths) - 1, self.num_ticks, dtype=np.int)
        self.xticks = np.linspace(0, len(self.time_delays) - 1, self.num_ticks, dtype=np.int)
        # the content of labels of these self.yticks
        self.yticklabels = [float(self.wavelengths[idx]) for idx in self.yticks]
        self.xticklabels = [float(self.time_delays[idx]) for idx in self.xticks]

        self.yticklabels = [self.label_format.format(x) for x in self.yticklabels]
        self.xticklabels = [self.label_format.format(x) for x in self.xticklabels]

        try:
            cmap_name = self.colormaps_dict["Fit_diff"]
            if cmap_name == "default":
                self.cm = sns.diverging_palette(220, 20, s=300, as_cmap=True)
            else:
                self.cm = sns.color_palette(cmap_name, as_cmap=True)
        except (ValueError, KeyError):
            print("Could not assign the selected colormap. Using a default one. Try to change the colormaps via button.")
            # default to this cmap
            self.cm = sns.diverging_palette(320, 20, s=300, as_cmap=True)

        sns.heatmap(self.difference_data, ax = self.axes_difference, cbar_kws={'label': 'amplitude'}, cmap=self.cm)

        self.axes_difference.set_yticks(self.yticks)
        self.axes_difference.set_yticklabels(self.yticklabels, fontsize=14)
        self.axes_difference.set_xticks(self.xticks)
        self.axes_difference.set_xticklabels(self.xticklabels, rotation=30, fontsize=14)

        self.axes_difference.set_ylabel("wavelengths", fontsize=16)
        self.axes_difference.set_xlabel("time since overlap", fontsize=16)

        title_string = self.base_filename+" diff: orig - SVDGF "+str(self.components_list)+ " DAS: " + str(self.indeces_for_DAS_matrix)
        if self.use_user_defined_fit_function:
            title_string = "user defined fit function was used\n"  + title_string
        if update_with_selected_DAS:
            title_string = r"updated! $\tau_i$ ="+str(['{:.4f}'.format(float(self.user_selected_decay_times[x])) for x in self.indeces_for_DAS_matrix])+"\n" + title_string
        self.axes_difference.set_title(title_string)

        self.notebook_container_diff.figs[self.tab_idx_difference].tight_layout()

        return None

    # this is done in main gui thread.
    def make_canvas(self):
        self.make_reconstruction_plot()
        self.make_difference_plot()

        self.toolbar_SVDGF = SmallToolbar.SmallToolbar(self.notebook_container_SVDGF.figs[self.tab_idx].canvas, self.notebook_container_SVDGF.figure_frames[self.tab_idx], pack_toolbar=False)
        self.toolbar_SVDGF.grid(row=0, column=99)

        self.toolbar_diff = SmallToolbar.SmallToolbar(self.notebook_container_diff.figs[self.tab_idx_difference].canvas, self.notebook_container_diff.figure_frames[self.tab_idx_difference], pack_toolbar=False)
        self.toolbar_diff.grid(row=0, column=4)

        self.btn_save_data = tk.Button(self.notebook_container_SVDGF.figure_frames[self.tab_idx], text=f"save data", fg=self.parent.violet, command=self.save_data_to_file)
        self.ttp_btn_save_data = ToolTip.CreateToolTip(self.btn_save_data, \
        'This also saves the corresponding difference heatmap and data. ')
        self.btn_save_data.grid(row=1, column=0, sticky="sw")

        self.btn_update_with_DAS = tk.Button(self.notebook_container_SVDGF.figure_frames[self.tab_idx], text="update with:", fg=self.parent.violet, command=lambda: self.update_canvases_with_selected_DAS(self.checkbutton_vars))
        self.ttp_btn_update_with_DAS = ToolTip.CreateToolTip(self.btn_update_with_DAS, \
        'This updates this plot and the difference plot with data computed using only the selected DAS. '
        'It also opens up a dialog field, where the decay times for the DAS decays could be changed', optional_y_direction_bump=60, optional_x_direction_bump=50)
        self.btn_update_with_DAS.grid(row=1, column=1, sticky="s")

        self.make_DAS_checkbuttons()

        self.btn_delete_attrs = tk.Button(self.notebook_container_SVDGF.figure_frames[self.tab_idx], text=f"remove tab", fg=self.parent.violet, command=lambda: self.remove_SVDGF_and_difference_tabs(self.notebook_container_SVDGF.tab_control, self.notebook_container_diff.tab_control))
        self.ttp_btn_delete_attrs = ToolTip.CreateToolTip(self.btn_delete_attrs, \
        'This also removes the corresponding difference tab. ')
        self.btn_delete_attrs.grid(row=1, column=2+len(self.components_list), sticky="se")

        # set dimensions of figure frame as computed correspondingly to gui size
        self.configure_figure_frame_size(self.notebook_container_SVDGF, self.tab_idx)

        self.notebook_container_SVDGF.canvases[self.tab_idx].get_tk_widget().grid(row=0, column=0, sticky="nsew", columnspan=3+len(self.components_list))

        self.btn_compare_rightSVs_with_fit = tk.Button(self.notebook_container_diff.figure_frames[self.tab_idx_difference], text="rightSVs vs fit", fg=self.parent.violet, command=self.compare_rightSVs_with_fit)
        self.ttp_btn_compare_rightSVs_with_fit = ToolTip.CreateToolTip(self.btn_compare_rightSVs_with_fit, \
        'Open a window to compare the right singular vectors of original data matrix with their reconstruction via fit.', optional_y_direction_bump=100)
        self.btn_compare_rightSVs_with_fit.grid(row=1, column=0, sticky="sw")

        self.btn_inspect_diff_matrix = tk.Button(self.notebook_container_diff.figure_frames[self.tab_idx_difference], text="inspect matrix", fg=self.parent.violet, command=self.inspect_difference_matrix_via_toplevel)
        self.ttp_btn_inspect_diff_matrix = ToolTip.CreateToolTip(self.btn_inspect_diff_matrix, \
        'Open a window to inspect this difference matrix row-by-row and column-by-column.', optional_y_direction_bump=100)
        self.btn_inspect_diff_matrix.grid(row=1, column=1, sticky="se")

        # set dimensions of figure frame as computed correspondingly to gui size
        self.configure_figure_frame_size(self.notebook_container_diff, self.tab_idx_difference)

        self.notebook_container_diff.canvases[self.tab_idx_difference].get_tk_widget().grid(row=0, column=0, sticky="nsew", columnspan=2)

        return None

    def configure_figure_frame_size(self, nbContainer, tab_idx):
        """ like this, a frame gets resized. """
        nbContainer.figure_frames[tab_idx].configure(width=self.parent.heatmaps_geometry_list[0])
        nbContainer.figure_frames[tab_idx].configure(height=self.parent.heatmaps_geometry_list[1])
        nbContainer.figure_frames[tab_idx].grid_propagate(False)

        return None

    def compare_rightSVs_with_fit(self):
        if not self.use_user_defined_fit_function:
            compareWindow = CompareRightSVsWithFit_Toplevel.CompareWindow(self.parent, self.use_user_defined_fit_function, self.tab_idx_difference, self.components_list, self.time_delays, self.retained_rSVs, self.retained_singular_values, self.fit_result_decay_times_as_dict, self.fit_result_amplitudes, self.filename, self.full_path_to_final_dir, start_time=self.start_time, matrix_bounds_dict=self.matrix_bounds_dict)
        else:
            compareWindow = CompareRightSVsWithFit_Toplevel.CompareWindow(self.parent, self.use_user_defined_fit_function, self.tab_idx_difference, self.components_list, self.time_delays, self.retained_rSVs, self.retained_singular_values, self.fit_result_decay_times_as_dict, self.fit_result_amplitudes, self.filename, self.full_path_to_final_dir, self.parsed_summands_of_user_defined_fit_function, start_time=self.start_time, matrix_bounds_dict=self.matrix_bounds_dict)

        compareWindow.run()

        return None

    def inspect_difference_matrix_via_toplevel(self):
        data_dict_for_toplevel = {"type": "fit_data", "time_delays": self.time_delays, "wavelengths": self.wavelengths, "data_matrix": self.difference_matrix_selected_DAS, "DAS_indeces": self.indeces_for_DAS_matrix, "save_dir": self.full_path_to_final_dir, "data_file": self.filename}
        Kinetics_Spectrum_Toplevel.Kinetics_Spectrum_Window(self.parent, self.tab_idx_difference, data_dict_for_toplevel)

        return None

    def make_DAS_checkbuttons(self):
        self.nr_of_checkbuttons = len(self.components_list)
        self.checkbutton_vars = [tk.IntVar(0) for _ in range(self.nr_of_checkbuttons)]

        for i in range(self.nr_of_checkbuttons):
            self.checkbutton_vars[i].set(1)

        self.checkbuttons = [tk.Checkbutton(self.notebook_container_SVDGF.figure_frames[self.tab_idx], text=self.indeces_for_DAS_matrix[checkbox], variable=self.checkbutton_vars[checkbox], onvalue=1, offvalue=0) for checkbox in range(self.nr_of_checkbuttons)]

        for checkbox in range(self.nr_of_checkbuttons):
            self.checkbuttons[checkbox].grid(row=1, column=checkbox+2, sticky='sew')

        return None

    def update_canvases_with_selected_DAS(self, int_vars):
        self.DAS_to_update_with = []
        self.indeces_for_DAS_matrix = []
        for i, checkbox in enumerate(range(len(int_vars))):
            if int_vars[checkbox].get() == 1:
                self.DAS_to_update_with.append(self.components_list[i])
                self.indeces_for_DAS_matrix.append(i)

        try:
            if self.DAS_to_update_with == []:
                raise ValueError('You did not select any components for the plot you want to see!')
            # get the new decay times if user assigns new ones:
            self.how_to_continue = self.display_toplevel_to_change_decay_times_used_for_DAS()

            if self.how_to_continue == "compute with old decay times":
                self.SVDGF_reconstructed_data_selected_DAS = get_SVDGF_reconstructed_data.run(self.DAS[:,self.indeces_for_DAS_matrix], [self.user_selected_decay_times[x] for x in self.indeces_for_DAS_matrix], self.time_delays, self.wavelengths, self.indeces_for_DAS_matrix, self.start_time)
            if self.how_to_continue == "compute with new decay times":
                self.SVDGF_reconstructed_data_selected_DAS = get_SVDGF_reconstructed_data.run(self.DAS[:,self.indeces_for_DAS_matrix], [self.user_selected_decay_times[x] for x in self.indeces_for_DAS_matrix], self.time_delays, self.wavelengths, self.indeces_for_DAS_matrix, self.start_time)

            self.difference_matrix_selected_DAS = self.data_matrix.astype(float) - self.SVDGF_reconstructed_data_selected_DAS.astype(float)

        except (ValueError, FloatingPointError) as error:
            tk.messagebox.showerror("Warning, an exception occurred!", f"Exception {type(error)} message: \n"+ str(error)
                                    +"\nif FloatingPointError: probably happened in "+ str(os.path.basename(get_SVDGF_reconstructed_data.__file__)))
            return None

        # draw new figures after clearing old ones
        self.axes.get_figure().clear()
        self.axes_difference.get_figure().clear()

        self.make_reconstruction_plot(update_with_selected_DAS=True)
        self.make_difference_plot(update_with_selected_DAS=True)

        # draw new figures on canvases
        self.notebook_container_SVDGF.canvases[self.tab_idx].draw_idle()
        self.notebook_container_diff.canvases[self.tab_idx_difference].draw_idle()

        return None

    def handle_new_decay_times_assignement(self, user_selected_decay_times):
        self.user_selected_decay_times = user_selected_decay_times

        return None

    def display_toplevel_to_change_decay_times_used_for_DAS(self):
        self.new_times_toplevel = new_decay_times_Toplevel.new_decay_times_Window(self.parent, self.resulting_SVDGF_fit_parameters, self.components_list, self.indeces_for_DAS_matrix, self.tab_idx, self.handle_new_decay_times_assignement, self.user_selected_decay_times)
        # this lets the program wait and execute further only once the toplevel has been closed
        self.parent.wait_window(self.new_times_toplevel)

        if self.user_selected_decay_times is None:
            self.user_selected_decay_times = ['{:.2f}'.format(self.resulting_SVDGF_fit_parameters['tau_component%i' % (j)].value) for j in self.components_list]
            print(f'\n user has continued without changing decay times, continue computation with old decay times!\n')
            return "compute with old decay times"

        # user has put in useable decay times
        print(f"\nuser has put in useable new decay times! {self.user_selected_decay_times=}")
        return "compute with new decay times"

    def get_summands_of_user_defined_fit_function_from_file(self, target_model_configuration_file):
        try:
            with open(target_model_configuration_file, mode='r') as dict_file:
                summands_of_user_defined_fit_function = ast.literal_eval(dict_file.read().strip())
        except (SyntaxError, FileNotFoundError):
            raise ValueError("getting the user defined summands for fit function from file failed, or the dict was empty.\n"
                            +"Check the file!\n"
                            +"computation is discontinued!")

        return summands_of_user_defined_fit_function

    def parse_summands_of_user_defined_fit_function_to_actual_code(self, all_summands_dict: dict):
        parsed_summands_list = []

        selected_components_summands_dict = {}
        for component in self.components_list:
            selected_components_summands_dict[f"summand_component{component}"] = all_summands_dict[f"summand_component{component}"]

        for summand_str in selected_components_summands_dict.values():
            parsed_summands_list.append(self.parse_summand(summand_str))

        return parsed_summands_list

    def parse_summand(self, summand_str: str):
        if summand_str == "":
            return "0"
        summand_str_with_time_delays_parsed = summand_str.replace("t", "time_delays")
        summand_str_with_decay_constants_parsed = summand_str_with_time_delays_parsed
        list_of_ks_in_summand_str = re.findall(r'k\d+', summand_str_with_time_delays_parsed)
        for k_str in list_of_ks_in_summand_str:
            summand_str_with_decay_constants_parsed = re.sub(r'k\d+', f"taus[\"component{k_str[1:]}\"]", summand_str_with_decay_constants_parsed, count=1)

        summand_str_with_brackets_added = "(" +summand_str_with_decay_constants_parsed+ ")"

        return summand_str_with_brackets_added

    # this is done in thread separate from gui main thread.
    def make_data(self):
        # compute the SVDGF data for plot. the needed data (SVDGF_reconstructed_data, time_delays and wavelengths) are assigned to self
        try:
            self.data_matrix_complete, self.time_delays, self.wavelengths = get_TA_data_after_start_time.run(self.filename, "-999999")
            if not self.matrix_bounds_dict == {}:
                self.data_matrix = self.data_matrix_complete[self.min_wavelength_index:self.max_wavelength_index+1, self.min_time_delay_index:self.max_time_delay_index+1]
                self.time_delays = self.time_delays[self.min_time_delay_index:self.max_time_delay_index+1]
                self.wavelengths = self.wavelengths[self.min_wavelength_index:self.max_wavelength_index+1]
            else:
                self.data_matrix = self.data_matrix_complete

            # set start time to the actual time delay that is closest to user input (is used in tab title)
            self.start_time = self.time_delays[0]

            # already set paths to which data from this data object is to be saved - this way the path stays the same
            # and can also be used in corresponding Toplevel classes!
            # i can not do this in __init__, as there the start time is not corrected yet!
            self.date_dir, self.final_dir = saveData.get_directory_paths(self.start_time, self.tab_idx, components=self.components_list)
            self.base_directory = os.getcwd()
            self.full_path_to_final_dir = saveData.get_final_path(self.base_directory, self.date_dir, "/SVDGF_reconstruction_data/", self.final_dir, self.filename)

        except ValueError as error:
            tk.messagebox.showerror("Warning,", "an exception occurred!""\nProbably due to a problem with the entered start time!\n"+
                                    f"Exception {type(error)} message: \n"+ str(error)+"\n")

            self.return_gui_to_initial_state()
            return None

        # get the selected rSVs, singular values and lSVs - input is TA data after time and self.components_list
        self.retained_rSVs, self.retained_lSVs, self.retained_singular_values = get_retained_rightSVs_leftSVs_singularvs.run(self.data_matrix, self.components_list)

        # get the parsed summands of user defined fit function, if the corresponding checkbox in main gui is checked:
        self.parsed_summands_of_user_defined_fit_function = []
        if self.use_user_defined_fit_function:
            try:
                self.summands_of_user_defined_fit_function = self.get_summands_of_user_defined_fit_function_from_file(self.target_model_configuration_file)
                self.parsed_summands_of_user_defined_fit_function = self.parse_summands_of_user_defined_fit_function_to_actual_code(self.summands_of_user_defined_fit_function)
            except (ValueError, KeyError) as error:
                tk.messagebox.showerror("Warning,", "an exception occurred!""\nProbably due to a problem with the user defined fit function file!\n"+
                                    f"Exception {type(error)} message: \n"+ str(error)+"\n")

                self.return_gui_to_initial_state()
                return None

        # do the fit: input: selected rSVs and singular values, self.temp_resolution, self.components_list - output: decay constants, amplitudes
        try:
            self.fit_result, self.resulting_SVDGF_fit_parameters = get_SVDGFit_parameters.run(self.retained_rSVs, self.retained_singular_values, self.components_list, self.time_delays, self.start_time, self.initial_fit_parameter_values, self.time_zero, self.temp_resolution, parsed_user_defined_summands=self.parsed_summands_of_user_defined_fit_function, fit_method_name=self.fit_method_name)
        except (ValueError,TypeError) as error:
            if str(error) == "":
                tk.messagebox.showerror("Warning, an exception occurred!", f"Exception {type(error)} message: \n"+ str(error)+ "\n"+
                                        "\nProbably due to a ValueError occurring in fit down the line, \ni.e.: the fit might not have converged. "
                                        +"\n\nMaybe try it with another fit method (Fit method menu) or changed initial fit parameter values (button in bottom left corner),"
                                        +" or another start time-value or another set of components ...")
            else: tk.messagebox.showerror("Warning, an exception occurred!", f"Exception {type(error)} message: \n"+ str(error))

            self.return_gui_to_initial_state()
            return None

        # get the DAS: input: selected lSVs and resulting amplitudes
        self.DAS = get_DAS_from_lSVs_res_amplitudes.run(self.retained_lSVs, self.resulting_SVDGF_fit_parameters, self.components_list, self.wavelengths, self.filename, self.start_time)

        # get the SVD-GFit reconstructed data: inputs: DAS, resulting decay consts
        try:
            self.fit_result_decay_times = ['{:.9f}'.format(self.resulting_SVDGF_fit_parameters['tau_component%i' % (j)].value) for j in self.components_list]
            self.fit_result_amplitudes = {}
            self.fit_result_decay_times_as_dict = {}
            for component in self.components_list:
                self.fit_result_decay_times_as_dict[f"tau_component{component}"] = self.resulting_SVDGF_fit_parameters[f"tau_component{component}"].value
                for component_index in range(len(self.components_list)):
                    self.fit_result_amplitudes[f"amp_rSV{component_index}_component{component}"] = self.resulting_SVDGF_fit_parameters[f"amp_rSV{component_index}_component{component}"].value

            self.SVDGF_reconstructed_data = get_SVDGF_reconstructed_data.run(self.DAS[:,self.indeces_for_DAS_matrix], [self.fit_result_decay_times[x] for x in self.indeces_for_DAS_matrix], self.time_delays, self.wavelengths, self.indeces_for_DAS_matrix, self.start_time)
        except (ValueError,FloatingPointError) as error:
            tk.messagebox.showerror("Warning, an exception occurred!", f"Exception {type(error)} message: \n"+ str(error)
                                    +"\nif FloatingPointError: probably happened in "+ str(os.path.basename(get_SVDGF_reconstructed_data.__file__))
                                    +"\n\nLikely due to some error in fit procedure which lead to very small fitted decay constants in course of which we get numbers like exp(-bigNumber),"
                                    +" which underflows a float."
                                    +f"\n{self.fit_result_decay_times=}"
                                    +"\n\nMaybe try it with another fit method (Fit method Menu) or changed initial fit parameter values (button in bottom left corner),"
                                    +" or another set of components or another start time-value...")
            self.return_gui_to_initial_state()
            return None

        # the difference matrix between full reconstruction data and original data
        self.difference_matrix = self.data_matrix.astype(float) - self.SVDGF_reconstructed_data.astype(float)
        # the difference matrix between reconstruction data using only selected DAS and original data
        # is used in Kinetics_Spectrum_Toplevel class, thus i set it here already
        self.difference_matrix_selected_DAS = self.difference_matrix

        return None

    def save_data_to_file(self):
        print(f"\nsaving data: SVDGF reconstruction object at tab: {self.tab_idx+1}\n")

        # check if directory exists:
        if not os.path.exists(self.full_path_to_final_dir):
            os.makedirs(self.full_path_to_final_dir)

        # save data
        self.notebook_container_SVDGF.figs[self.tab_idx].savefig(self.full_path_to_final_dir+"/reconstruction_heatmap_DAS"+str(self.indeces_for_DAS_matrix)+".png")
        self.notebook_container_diff.figs[self.tab_idx_difference].savefig(self.full_path_to_final_dir+"/difference_heatmap_DAS"+str(self.indeces_for_DAS_matrix)+".png")
        saveData.make_log_file(self.full_path_to_final_dir, filename=self.filename, start_time=self.start_time, components=self.components_list, matrix_bounds_dict=self.matrix_bounds_dict, use_user_defined_fit_function=self.use_user_defined_fit_function)
        self.result_data_to_save = {"retained_sing_values": self.retained_singular_values, "DAS": self.DAS, "fit_report_complete": lmfit.fit_report(self.fit_result), "time_delays": self.time_delays, "wavelengths": self.wavelengths, "retained_left_SVs": self.retained_lSVs, "retained_right_SVs": self.retained_rSVs}
        if self.parsed_summands_of_user_defined_fit_function: # if dictionary with parsed user defined fit function exists, add it to data to be saved.
            self.result_data_to_save["parsed_summands_of_user_defined_fit_function"] = self.parsed_summands_of_user_defined_fit_function
        saveData.save_result_data(self.full_path_to_final_dir, self.result_data_to_save)

        # save data matrices
        self.data_matrices_to_save = {"SVDGF_reconstruction_matrix": self.SVDGF_reconstructed_data.T, "difference_matrix": self.difference_data.T, "data_matrix": self.data_matrix.T, "difference_matrix_selected_DAS"+str(self.indeces_for_DAS_matrix): self.difference_matrix_selected_DAS.T}
        saveData.save_formatted_data_matrix_after_time(self.full_path_to_final_dir, self.time_delays, self.wavelengths, self.data_matrices_to_save)

        return None

    # to delete instance attributes to free up memory. is called when tab is removed.
    def delete_attributes(self):
        attr_lst = list(vars(self))
        for attr in attr_lst:
            delattr(self, attr)

        del attr_lst
        del self

        gc.collect()

        return None

    # remove the tabs with plot from gui
    def remove_SVDGF_and_difference_tabs(self, nb_SVDGF, nb_difference):
        nb_SVDGF.forget("current")
        self.parent.remove_correct_tab_from_difference_nb(self.tab_idx_difference + 1)

        if nb_SVDGF.index(tk.END) == 0:
            nb_SVDGF.grid_remove()

        if nb_difference.index(tk.END) == 0:
            nb_difference.grid_remove()

        for checkbox in range(self.nr_of_checkbuttons):
            self.checkbuttons[checkbox].grid_remove()
        self.btn_update_with_DAS.grid_remove()
        self.btn_delete_attrs.grid_remove()
        self.btn_save_data.grid_remove()
        self.btn_inspect_diff_matrix.grid_remove()
        self.btn_compare_rightSVs_with_fit.grid_remove()
        self.toolbar_SVDGF.grid_remove()
        self.toolbar_diff.grid_remove()

        self.axes.get_figure().clear()
        self.axes_difference.get_figure().clear()

        self.notebook_container_SVDGF.figure_frames[self.tab_idx].grid_propagate(True)
        self.notebook_container_diff.figure_frames[self.tab_idx_difference].grid_propagate(True)
        self.notebook_container_SVDGF.canvases[self.tab_idx].get_tk_widget().configure(height=0, width=0)
        self.notebook_container_diff.canvases[self.tab_idx].get_tk_widget().configure(height=0, width=0)


        self.delete_attributes()

        return None
