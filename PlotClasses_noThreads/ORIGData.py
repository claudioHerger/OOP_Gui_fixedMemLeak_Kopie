#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" A module used to show the heatmap of an input (TA) data file value on the Gui. \n\n
"""
import gc
import numpy as np
import seaborn as sns
import matplotlib
matplotlib.use("TkAgg")
import tkinter as tk
import os

# my own modules
from FunctionsUsedByPlotClasses import get_TA_data_after_start_time
from SupportClasses import saveData, ToolTip, SmallToolbar
from ToplevelClasses import SVD_inspection_Toplevel, Kinetics_Spectrum_Toplevel

class ORIGData_Heatmap():
    def __init__(self, parent, tab_idx, filename, matrix_bounds_dict, tab_title_filename, colormaps_dict):
        """A class used to create a heatmap of a data matrix read from a file. \n
        The plot will be put on a tab of a ttk notebook.

        Args:
            parent (GuiAppTAAnalysis): the Gui App that creates the instance of this class\
            tab_idx (int): the index of the tab that is added to the ttk notebook.
            filename (String): the full path to the datafile
            matrix_bounds_dict (dict): contains the indeces that dictate the which part of complete data matrix to use
            tab_title_filename (string): filename possibly truncated so that tab titles do not become too large
            colormaps_dict (dict): dictionary containing the colormap names for the heatmaps
        """

        self.parent = parent
        self.notebook_container = self.parent.nbCon_orig
        self.filename = filename
        self.matrix_bounds_dict = matrix_bounds_dict
        if not self.matrix_bounds_dict == {}:
            self.min_wavelength_index = self.matrix_bounds_dict["min_wavelength_index"]
            self.max_wavelength_index = self.matrix_bounds_dict["max_wavelength_index"]
            self.min_time_delay_index = self.matrix_bounds_dict["min_time_delay_index"]
            self.max_time_delay_index = self.matrix_bounds_dict["max_time_delay_index"]
        self.tab_idx = tab_idx
        self.tab_title_filename = tab_title_filename
        self.colormaps_dict = colormaps_dict

        return None

    def make_plot(self):
        sns.set(font_scale = 1.3, rc={"xtick.bottom" : True, "ytick.left" : True})

        # create axes on parent.figure with correct index:
        self.axes = self.notebook_container.figs[self.tab_idx].add_subplot(1,1,1)

        # adjust figsize as computed correspondingly to gui size:
        self.axes.get_figure().set_figwidth(self.parent.heatmaps_figure_geometry_list[0])
        self.axes.get_figure().set_figheight(self.parent.heatmaps_figure_geometry_list[1])

        self.data = self.data_matrix.astype(float)
        self.base_filename = os.path.basename(self.filename)
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
            cmap_name = self.colormaps_dict["ORIG"]
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

        self.axes.set_title(self.base_filename+" original data")

        self.notebook_container.figs[self.tab_idx].tight_layout()

        return None

    # this is done in main gui thread.
    def make_canvas(self):
        self.make_plot()

        self.toolbar_orig = SmallToolbar.SmallToolbar(self.notebook_container.figs[self.tab_idx].canvas, self.notebook_container.figure_frames[self.tab_idx], pack_toolbar=False)
        self.toolbar_orig.grid(row=0, column=4)

        self.tab_title = '{:,.1f}'.format(float(self.start_time)) + " " + self.tab_title_filename
        self.notebook_container.set_tab_title(self.notebook_container.tab_control.index("current"), title=f'{self.tab_idx+1}: ' + self.tab_title)

        self.btn_delete_attrs = tk.Button(self.notebook_container.figure_frames[self.tab_idx], text="remove tab", fg=self.parent.violet, command=lambda: self.remove_tab(self.notebook_container))
        self.btn_delete_attrs.grid(row=1, column=3, sticky="se")

        self.btn_inspect_SVD_components = tk.Button(self.notebook_container.figure_frames[self.tab_idx], text="inspect SVD", fg=self.parent.violet, command=self.make_SVD_inspection_toplevel)
        self.ttp_btn_inspect_SVD_components = ToolTip.CreateToolTip(self.btn_inspect_SVD_components, \
        'This opens a window to inspect the SVD components of this data matrix.')
        self.btn_inspect_SVD_components.grid(row=1, column=1, sticky="s")

        self.btn_save_data = tk.Button(self.notebook_container.figure_frames[self.tab_idx], text="save data", fg=self.parent.violet, command=self.save_data_to_file)
        self.btn_save_data.grid(row=1, column=0, sticky="sw")

        self.btn_inspect_data_matrix = tk.Button(self.notebook_container.figure_frames[self.tab_idx], text="inspect matrix", fg=self.parent.violet, command=self.inspect_data_matrix_via_toplevel)
        self.ttp_btn_inspect_data_matrix = ToolTip.CreateToolTip(self.btn_inspect_data_matrix, \
        'Open a window to inspect this data matrix row-by-row and column-by-column.')
        self.btn_inspect_data_matrix.grid(row=1, column=2, sticky="se", padx=5)

        # set dimensions of figure frame as computed correspondingly to gui size
        self.configure_figure_frame_size(self.notebook_container, self.tab_idx)

        self.notebook_container.canvases[self.tab_idx].get_tk_widget().grid(row=0, column=0, sticky="nsew", columnspan=4)

        return None

    def configure_figure_frame_size(self, nbContainer, tab_idx):
        """ like this, a frame gets resized. """
        nbContainer.figure_frames[tab_idx].configure(width=self.parent.heatmaps_geometry_list[0])
        nbContainer.figure_frames[tab_idx].configure(height=self.parent.heatmaps_geometry_list[1])
        nbContainer.figure_frames[tab_idx].grid_propagate(False)

        return None

    # this is done in thread separate from gui main thread.
    def make_data(self):
        # get the data
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
            self.date_dir, self.final_dir = saveData.get_directory_paths(self.start_time, self.tab_idx)
            self.base_directory = os.getcwd()
            self.full_path_to_final_dir = saveData.get_final_path(self.base_directory, self.date_dir, "/Original_data/", self.final_dir, self.filename)

        except ValueError as error:
            tk.messagebox.showerror("Warning,", "an exception occurred!""\nMaybe due to the entered start time or data file format!\n"+
                                    f"Exception {type(error)} message: \n"+ str(error)+"\n")


            # return gui to initial state if above data preparation failed
            self.parent.return_some_gui_widgets_to_initial_state(button=self.parent.btn_show_orig_data_heatmap, label=self.parent.lbl_reassuring_orig, tab_control=self.notebook_container.tab_control)
            self.delete_attributes()

            return None

        return None

    def save_data_to_file(self):
        print(f"\nsaving data: original reconstruction object at tab: {self.tab_idx+1}\n")

        # check if directory exists:
        if not os.path.exists(self.full_path_to_final_dir):
            os.makedirs(self.full_path_to_final_dir)

        # save data
        self.notebook_container.figs[self.tab_idx].savefig(self.full_path_to_final_dir+"/originalData.png")

        saveData.make_log_file(self.full_path_to_final_dir, filename=self.filename, start_time=self.start_time, matrix_bounds=self.matrix_bounds_dict)

        self.result_data_to_save = {"time_delays": self.time_delays, "wavelengths": self.wavelengths}
        saveData.save_result_data(self.full_path_to_final_dir, self.result_data_to_save)

        # save data matrices
        self.data_matrices_to_save = {"data_matrix": self.data_matrix.T}
        saveData.save_formatted_data_matrix_after_time(self.full_path_to_final_dir, self.time_delays, self.wavelengths, self.data_matrices_to_save)

        return None

    def make_SVD_inspection_toplevel(self):
        SVD_inspection_Toplevel.SVD_inspection_Window(self.parent, self.tab_idx, self)

        return None

    def inspect_data_matrix_via_toplevel(self):
        data_dict_for_toplevel = {"type": "original data", "time_delays": self.time_delays, "wavelengths": self.wavelengths, "data_matrix": self.data_matrix, "save_dir": self.full_path_to_final_dir, "data_file": self.filename}
        Kinetics_Spectrum_Toplevel.Kinetics_Spectrum_Window(self.parent, self.tab_idx, data_dict_for_toplevel)

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

    # remove the tab with plot from gui
    def remove_tab(self, nbContainer):
        nbContainer.tab_control.forget("current")

        if nbContainer.tab_control.index(tk.END) == 0:       # nb.index(tkinter.END) is like a len() method for a ttk.notebook widget.
            nbContainer.tab_control.grid_remove()

        # remove figure and button from canvas when tab is removed. This is merely for aesthetic reasons.
        self.btn_delete_attrs.grid_remove()
        self.btn_save_data.grid_remove()
        self.btn_inspect_data_matrix.grid_remove()
        self.btn_inspect_SVD_components.grid_remove()
        self.toolbar_orig.grid_remove()

        # clear figure when tab is removed
        self.axes.get_figure().clear()
        nbContainer.figure_frames[self.tab_idx].grid_propagate(True)
        nbContainer.canvases[self.tab_idx].get_tk_widget().configure(height=0, width=0)

        # delete instance attributes and call garbage collector
        self.delete_attributes()

        return None