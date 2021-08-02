#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" A module to produce a plot showing the singular values of some data on the GUI.
"""

import gc
import matplotlib.pyplot as plt
import numpy as np
import tkinter as tk
import os
import scipy

# my own modules
from FunctionsUsedByPlotClasses import get_TA_data_after_start_time, get_closest_nr_from_array_like
from SupportClasses import saveData


class SingularValues_Plot():
    def __init__(self, parent, filename, start_time, tab_idx, nr_of_singular_values):
        """A class used to compute, store and display on the GUI the singular values of a dataFile:
        The plot will be put on a tab of a ttk notebook.

        Args:
            parent (GuiAppTAAnalysis): parent is the Gui App that creates the instance of this class.
            filename (String): filename is the full path of the datafile.
            start_time (float): start_time is the value of the start time starting from which the data will be used for the plot.
            tab_idx (int): tab_idx is the index of the tab that is added to the ttk notebook.
            nr_of_singular_values(int): the number of singular values to be plotted.
        """

        self.parent = parent
        self.filename = filename
        self.start_time = start_time
        self.tab_idx = tab_idx
        self.nr_of_sing_values = nr_of_singular_values

        return None

    # compute the data and assign it to self.
    # this is done in thread outside of Gui mainloop.
    def make_data(self):
        try:
            self.TA_data_after_time, self.time_delays, self.wavelengths = get_TA_data_after_start_time.run(self.filename, self.start_time)
            # update start time to the actual time delay that is closest to user input
            self.start_time = str(get_closest_nr_from_array_like.run(self.time_delays, float(self.start_time)))
            if (self.start_time == self.time_delays[-1]):
                raise ValueError("The start time you entered was above the last time delay. Thus it was moved to the last time delay.\n"+
                                "However, an SVD wont work in that case.")
            # already set paths to which data from this data object is to be saved - this way the path stays the same
            # and can also be used in corresponding Toplevel classes!
            # i can not do this in __init__, as there the start time is not corrected yet!
            self.date_dir, self.final_dir = saveData.get_directory_paths(self.start_time, self.tab_idx)
            self.base_directory = os.getcwd()
            self.full_path_to_final_dir = saveData.get_final_path(self.base_directory, self.date_dir, "/SingularValues_Data/", self.final_dir, self.filename)

        except ValueError as error:
            tk.messagebox.showerror("Warning,", "an exception occurred!""\nProbably due to a problem with the entered start time!\n"+
                                    f"Exception {type(error)} message: \n"+ str(error)+"\n")

            # return gui to initial state if above data preparation failed
            self.parent.return_some_gui_widgets_to_initial_state(button=self.parent.btn_show_singular_values, label=self.parent.lbl_reassuring_singValues, tab_control=self.parent.nbCon_singValues.tab_control)

            self.delete_attributes()
            return None

        U, sigma, VT = scipy.linalg.svd(self.TA_data_after_time)

        self.retained_singular_values = sigma[:self.nr_of_sing_values]

        return None

    # make the plot with self.data, put it on Figure as indexed by tab index.
    # done in main gui loop.
    def make_singValues_plot(self):
        plt.style.use("seaborn")
        plt.rcParams.update({'axes.labelsize': 20.0, 'axes.titlesize': 22.0, 'legend.fontsize':20, 'xtick.labelsize':18, 'ytick.labelsize':18, "axes.edgecolor":"black", "axes.linewidth":1})

        # create axes on parent.figure with correct index:
        self.axes = self.parent.nbCon_singValues.figs[self.tab_idx].add_subplot(1,1,1)

        self.xaxis = [i+1 for i in range(self.nr_of_sing_values)]

        self.axes.plot(self.xaxis, self.retained_singular_values, marker="o", linewidth=0, markersize=10)

        self.axes.set_yscale("log")
        self.axes.set_ylabel("log(singular value)")
        self.axes.set_xlabel("singular value index")
        self.axes.set_xticks(self.xaxis)
        self.axes.set_title("singular values of " + str(os.path.basename(self.filename))+"\n")

        if len(self.retained_singular_values) <= 12:
            label_format = '{:,.2f}'
            value_labels = [label_format.format(x) for x in self.retained_singular_values]
            text_str = "values: "+ str(value_labels[0])
            for label in value_labels[1:]:
                text_str += "\n"+" "*10 + str(label)
            self.axes.text(0.8,0.5,text_str, fontsize=18, horizontalalignment='center', verticalalignment='center', transform=self.axes.transAxes, bbox={"facecolor": "cornflowerblue", "alpha":0.5, "pad": 4})

        self.parent.nbCon_singValues.figs[self.tab_idx].tight_layout()

        return None

    # update the Canvas in gui as indexed by tab index.
    # this is done in main gui thread.
    def make_canvas(self):
        try:
            self.make_singValues_plot()
        except ValueError as error:
            tk.messagebox.showerror("Warning, an exception occurred!", f"Exception {type(error)} message: \n"+ str(error)+"\n"
                                    +"\nProbably due to a too large number of singular values to be plotted!\n"+
                                    "Or something else....")

            # return gui to initial state if above data preparation failed
            self.parent.return_some_gui_widgets_to_initial_state_when_plot_class_fails(self.parent.btn_show_singular_values, self.parent.lbl_reassuring_singValues, self.parent.nbCon_singValues.tab_control)

            self.delete_attributes()


        self.btn_delete_attrs = tk.Button(self.parent.nbCon_singValues.figure_frames[self.tab_idx], text=f"remove this tab", fg=self.parent.violet, command=lambda: self.remove_tab(self.parent.nbCon_singValues.tab_control))
        self.btn_delete_attrs.grid(row=1, column=1, sticky="se")

        self.btn_save_data = tk.Button(self.parent.nbCon_singValues.figure_frames[self.tab_idx], text=f"save this data", fg=self.parent.violet, command=self.save_data_to_file)
        self.btn_save_data.grid(row=1, column=0, sticky="sw")

        self.parent.nbCon_singValues.canvases[self.tab_idx].get_tk_widget().grid(row=0, column=0, sticky="nsew", columnspan=2)
        self.parent.nbCon_singValues.canvases[self.tab_idx].draw()

    def save_data_to_file(self):
        print(f"\nsaving data: Singular values object at tab: {self.tab_idx+1}\n")

        # check if directory exists:
        if not os.path.exists(self.full_path_to_final_dir):
            os.makedirs(self.full_path_to_final_dir)

        # save data
        self.parent.nbCon_singValues.figs[self.tab_idx].savefig(self.full_path_to_final_dir+"/sing_values_plot.png")
        saveData.make_log_file(self.full_path_to_final_dir, filename=self.filename, start_time=self.start_time)
        self.result_data_to_save = {"retained_sing_values": self.retained_singular_values}
        saveData.save_result_data(self.full_path_to_final_dir, self.result_data_to_save)

    # to delete instance attributes to free up memory.
    def delete_attributes(self):
        attr_lst = list(vars(self))
        for attr in attr_lst:
            delattr(self, attr)

        del attr_lst
        del self

        gc.collect()

        return None

    # remove the tab with plot from gui
    def remove_tab(self, notebook):
        notebook.forget("current")

        if notebook.index(tk.END) == 0:
            notebook.grid_remove()

        # remove figure and button from canvas when tab is removed. This is merely for aesthetic reasons.
        self.btn_delete_attrs.grid_remove()
        self.btn_save_data.grid_remove()
        self.parent.nbCon_singValues.canvases[self.tab_idx].get_tk_widget().grid_remove()

        # clear figure when tab is removed
        self.axes.get_figure().clear()

        # delete instance attributes and call garbage collector
        self.delete_attributes()

        return None
