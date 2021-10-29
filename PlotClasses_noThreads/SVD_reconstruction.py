#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" A module to produce a plot of SVD-reconstructed data on the GUI"""

import gc
import numpy as np
import seaborn as sns
import tkinter as tk
import os

# my own modules
from FunctionsUsedByPlotClasses import get_TA_data_after_start_time, get_SVD_reconstructed_data_for_GUI, get_retained_rightSVs_leftSVs_singularvs, get_retained_rightSVs_leftSVs_singularvs
from SupportClasses import ToolTip, saveData, SmallToolbar
from ToplevelClasses import Kinetics_Spectrum_Toplevel

class SVD_Heatmap():
    def __init__(self, parent, filename, matrix_bounds_dict, components_list, tab_idx, tab_idx_difference, colormaps_dict):
        """ A class to produce a plot of SVD-reconstructed data on the GUI:\n\n
            * parent is the Gui App that creates the instance of this class\n
            * filename is the full path of the datafile to be reconstructed\n
            * matrix_bounds_dict (dict): contains the indeces that dictate the which part of complete data matrix to use\n
            * components_list is a list of integers that represent the SVD components to be used for the reconstruction\n
            * tab_idx is used to put the plot on the correct that of the ttk notebook of the GUI\n
            * tab_idx_difference is the the same as tab_idx but used with the difference notebook\n
            * colormaps_dict (dict): dictionary containing the colormap names for the heatmaps\n\n
        """
        self.parent = parent
        self.notebook_container_SVD = self.parent.nbCon_SVD
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
        self.colormaps_dict = colormaps_dict

        return None

    def make_SVD_reconstruction_plot(self):
        sns.set(font_scale = 1.3, rc={"xtick.bottom" : True, "ytick.left" : True})

        self.axes = self.notebook_container_SVD.figs[self.tab_idx].add_subplot(1,1,1)
        # adjust figsize as computed correspondingly to gui size:
        self.axes.get_figure().set_figwidth(self.parent.heatmaps_figure_geometry_list[0])
        self.axes.get_figure().set_figheight(self.parent.heatmaps_figure_geometry_list[1])

        self.data = self.SVD_reconstructed_data.astype(float)
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
            cmap_name = self.colormaps_dict["SVD"]
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

        self.axes.set_title(self.base_filename+" SVD reconstructed data "+str(self.components_list))

        self.notebook_container_SVD.figs[self.tab_idx].tight_layout()

        return None

    def make_difference_plot(self):
        sns.set(font_scale = 1.3, rc={"xtick.bottom" : True, "ytick.left" : True})

        self.axes_difference = self.notebook_container_diff.figs[self.tab_idx_difference].add_subplot(1,1,1)
        # adjust figsize as computed correspondingly to gui size:
        self.axes_difference.get_figure().set_figwidth(self.parent.heatmaps_figure_geometry_list[0])
        self.axes_difference.get_figure().set_figheight(self.parent.heatmaps_figure_geometry_list[1])

        self.difference_data = self.difference_matrix.astype(float)

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
            cmap_name = self.colormaps_dict["SVD_diff"]
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

        self.axes_difference.set_title(self.base_filename+" diff: orig - SVD "+str(self.components_list))

        self.notebook_container_diff.figs[self.tab_idx_difference].tight_layout()

        return None

    # this is done in main gui thread.
    def make_canvas(self):
        self.make_SVD_reconstruction_plot()
        self.make_difference_plot()

        self.toolbar_SVD = SmallToolbar.SmallToolbar(self.notebook_container_SVD.figs[self.tab_idx].canvas, self.notebook_container_SVD.figure_frames[self.tab_idx], pack_toolbar=False)
        self.toolbar_SVD.grid(row=0, column=4)

        self.toolbar_diff = SmallToolbar.SmallToolbar(self.notebook_container_diff.figs[self.tab_idx_difference].canvas, self.notebook_container_diff.figure_frames[self.tab_idx_difference], pack_toolbar=False)
        self.toolbar_diff.grid(row=0, column=4)

        self.btn_delete_attrs = tk.Button(self.notebook_container_SVD.figure_frames[self.tab_idx], text=f"remove tab", fg=self.parent.violet, command=lambda: self.remove_SVD_and_difference_tabs(self.notebook_container_SVD.tab_control, self.notebook_container_diff.tab_control))
        self.ttp_btn_delete_attrs = ToolTip.CreateToolTip(self.btn_delete_attrs, \
        'This also removes the corresponding difference tab. ')
        self.btn_delete_attrs.grid(row=1, column=1, sticky="se")

        self.btn_save_data = tk.Button(self.notebook_container_SVD.figure_frames[self.tab_idx], text=f"save data", fg=self.parent.violet, command=self.save_data_to_file)
        self.ttp_btn_save_data = ToolTip.CreateToolTip(self.btn_save_data, \
        'This also saves the corresponding difference heatmap and data. ')
        self.btn_save_data.grid(row=1, column=0, sticky="sw")

        # set dimensions of figure frame as computed correspondingly to gui size
        self.configure_figure_frame_size(self.notebook_container_SVD, self.tab_idx)

        self.notebook_container_SVD.canvases[self.tab_idx].get_tk_widget().grid(row=0, column=0, sticky="nsew", columnspan=2)

        self.btn_inspect_diff_matrix = tk.Button(self.notebook_container_diff.figure_frames[self.tab_idx_difference], text="inspect matrix", fg=self.parent.violet, command=self.inspect_difference_matrix_via_toplevel)
        self.ttp_btn_inspect_diff_matrix = ToolTip.CreateToolTip(self.btn_inspect_diff_matrix, \
        'Open a window to inspect this difference matrix row-by-row and column-by-column.', optional_y_direction_bump=100)
        self.btn_inspect_diff_matrix.grid(row=1, column=0, sticky="se")

        # set dimensions of figure frame as computed correspondingly to gui size
        self.configure_figure_frame_size(self.notebook_container_diff, self.tab_idx_difference)

        self.notebook_container_diff.canvases[self.tab_idx_difference].get_tk_widget().grid(row=0, column=0, sticky="nsew")

        return None

    def configure_figure_frame_size(self, nbContainer, tab_idx):
        """ like this, a frame gets resized. """
        nbContainer.figure_frames[tab_idx].configure(width=self.parent.heatmaps_geometry_list[0])
        nbContainer.figure_frames[tab_idx].configure(height=self.parent.heatmaps_geometry_list[1])
        nbContainer.figure_frames[tab_idx].grid_propagate(False)

        return None

    def inspect_difference_matrix_via_toplevel(self):
        data_dict_for_toplevel = {"type": "SVD data", "time_delays": self.time_delays, "wavelengths": self.wavelengths, "data_matrix": self.difference_matrix, "save_dir": self.full_path_to_final_dir, "data_file": self.filename}
        Kinetics_Spectrum_Toplevel.Kinetics_Spectrum_Window(self.parent, self.tab_idx_difference, data_dict_for_toplevel)

        return None

    # this is done in thread separate from gui main thread.
    def make_data(self):
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
            self.full_path_to_final_dir = saveData.get_final_path(self.base_directory, self.date_dir, "/SVD_reconstruction_data/", self.final_dir, self.filename)

        except ValueError as error:
            tk.messagebox.showerror("Warning,", "an exception occurred!""\nProbably due to a problem with the entered start time!\n"+
                                    f"Exception {type(error)} message: \n"+ str(error)+"\n")

            # return gui to initial state if above data preparation failed
            self.parent.return_some_gui_widgets_to_initial_state(button=self.parent.btn_show_SVD_reconstructed_data_heatmap, label=self.parent.lbl_reassuring_SVD, tab_control=self.notebook_container_SVD.tab_control)
            self.parent.return_some_gui_widgets_to_initial_state(tab_control=self.notebook_container_diff.tab_control)

            self.delete_attributes()
            return None

        # get the selected rSVs, singular values and lSVs - input is TA data after time and self.components_list
        self.retained_rSVs, self.retained_lSVs, self.retained_singular_values = get_retained_rightSVs_leftSVs_singularvs.run(self.data_matrix, self.components_list)

        self.SVD_reconstructed_data, self.singular_values, self.U_matrix, self.VT_matrix = get_SVD_reconstructed_data_for_GUI.run(self.data_matrix, self.components_list)

        self.difference_matrix = self.data_matrix.astype(float) - self.SVD_reconstructed_data.astype(float)

        return None

    def save_data_to_file(self):
        print(f"\nsaving data: SVD reconstruction object at tab: {self.tab_idx+1}\n")

        # check if directory exists:
        if not os.path.exists(self.full_path_to_final_dir):
            os.makedirs(self.full_path_to_final_dir)

        # save data
        self.notebook_container_SVD.figs[self.tab_idx].savefig(self.full_path_to_final_dir+"/SVD_reconstruction_heatmap.png")
        self.notebook_container_diff.figs[self.tab_idx_difference].savefig(self.full_path_to_final_dir+"/SVD_difference_heatmap.png")

        saveData.make_log_file(self.full_path_to_final_dir, filename=self.filename, start_time=self.start_time, components=self.components_list, matrix_bounds=self.matrix_bounds_dict)

        self.result_data_to_save = {"time_delays": self.time_delays, "wavelengths": self.wavelengths, "singular_values": self.singular_values, "U_matrix": self.U_matrix, "VT_matrix": self.VT_matrix, "retained_right_SVs": self.retained_rSVs, "retained_left_SVs": self.retained_lSVs, "retained_sing_values": self.retained_singular_values,}
        saveData.save_result_data(self.full_path_to_final_dir, self.result_data_to_save)

        # save data matrices
        self.data_matrices_to_save = {"SVD_reconstruction_matrix": self.SVD_reconstructed_data.T, "difference_matrix": self.difference_data.T, "data_matrix": self.data_matrix.T}
        saveData.save_formatted_data_matrix_after_time(self.full_path_to_final_dir, self.time_delays, self.wavelengths, self.data_matrices_to_save)

        return None

    # to delete instance attributes to free up memory.
    def delete_attributes(self):
        attr_lst = list(vars(self))
        for attr in attr_lst:
            delattr(self, attr)

        del attr_lst
        del self

        gc.collect()

        return None

    def remove_SVD_and_difference_tabs(self, nb_SVD, nb_difference):
        nb_SVD.forget("current")
        self.parent.remove_correct_tab_from_difference_nb(self.tab_idx_difference + 1)

        if nb_SVD.index(tk.END) == 0:
            nb_SVD.grid_remove()

        if nb_difference.index(tk.END) == 0:
            nb_difference.grid_remove()

        self.btn_delete_attrs.grid_remove()
        self.btn_save_data.grid_remove()
        self.btn_inspect_diff_matrix.grid_remove()
        self.toolbar_SVD.grid_remove()
        self.toolbar_diff.grid_remove()

        self.axes.get_figure().clear()
        self.axes_difference.get_figure().clear()

        self.notebook_container_SVD.figure_frames[self.tab_idx].grid_propagate(True)
        self.notebook_container_diff.figure_frames[self.tab_idx_difference].grid_propagate(True)
        self.notebook_container_SVD.canvases[self.tab_idx].get_tk_widget().configure(height=0, width=0)
        self.notebook_container_diff.canvases[self.tab_idx].get_tk_widget().configure(height=0, width=0)

        self.delete_attributes()

        return None
