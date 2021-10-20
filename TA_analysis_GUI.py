#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
import tkinter.ttk as ttk

import matplotlib
matplotlib.use('TkAgg')         # to be able to use plt.close() without the gui closing too! - and/or some other things
import platform
import os
import traceback
import collections              # e.g. to check whether an object is iterable, has size attribute etc
import lmfit
import ast

# threading
import threading

# PlotClasses - used to create plots on gui
from PlotClasses_noThreads import ORIGData, SVDGF_reconstruction, SVD_reconstruction

# SupportClasses - used to e.g. explain functionality of widget in gui
from SupportClasses import ToolTip, NotebookContainer
from ToplevelClasses import FitResult_Toplevel, DAS_Toplevel, initial_fit_parameter_values_Toplevel, target_model_Toplevel, ChooseColorMaps_Toplevel

class GuiAppTAAnalysis(tk.Frame):

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent

        # the directory from where program is started
        self.base_directory = os.getcwd()        # Leads to Error if program is not started from directory where it is in
        self.config_files_directory = self.base_directory + "/configFiles/"
        self.target_model_fit_function_file = self.config_files_directory + "/target_model_summands.txt"

        self.read_initial_fit_parameter_values_from_file()
        self.read_currently_used_cmaps_from_file()

        # which files the user can select in the tk.filedialog.askopenfilename
        self.ftypes = [('txt files', '*.txt'), ('All files', '*.txt; *.csv'), ('CSV files', '*.csv')]

        # set initial data file variable etc.
        self.curr_reconstruct_data_file_strVar = tk.StringVar()
        self.curr_reconstruct_data_file_strVar.set("no file selected")
        # self.curr_reconstruct_data_file_strVar.set(self.base_directory+"/DataFiles/simulatedTAData_formatted.txt")
        self.curr_reconstruct_data_file_strVar.set(self.base_directory+"/DataFiles/data_full_0.txt")
        self.curr_reconstruct_data_file_strVar.trace_add("write", self.update_filename_in_title_and_truncated_filename_for_tab_header_callback)
        self.curr_reconstruct_data_start_time_value = tk.DoubleVar()
        self.curr_reconstruct_data_start_time_value.trace_add("write", self.update_filename_in_title_and_truncated_filename_for_tab_header_callback)
        self.curr_reconstruct_data_start_time_value.set(-999.0)
        self.curr_reconstruct_data_start_time_value.set(0.0)

        # determine the number of tabs possible for all the different notebooks:
        self.NR_OF_TABS = 6    # this should really be left below 50!
        self.NR_OF_DIFFERENCE_TABS = 2 * self.NR_OF_TABS

        # some styling variables
        self.blue = "cornflowerblue"
        self.gold = "#ffd700"
        self.orange = "orange"
        self.complementary_blue = "#0028FF"
        self.violet = "darkmagenta"
        self.grey = "lavender"
        self.flashwidgetcolor = "navyblue"

        # self.blue = "#01949a" # teal
        # self.gold = "#e5ddc8" # sanddollar
        # self.orange = "orange"
        # self.complementary_blue = "#0028FF"
        # self.violet = "#004369" # navyblue
        # self.grey = "lavender"
        # self.flashwidgetcolor = "navyblue"

        self.ttk_Notebook_style = ttk.Style()
        self.ttk_Notebook_style.theme_settings("default", settings={
            "TNotebook":    {"configure": {"background": self.grey, }},
            "TNotebook.Tab":    {
                "configure":    {"background": self.blue, },
                "map":          {"background": [("selected", self.gold)]}}})
        self.ttk_Notebook_style.theme_use("default")

        # geometry, title etc of window
        self.parent.config(bg=self.violet)
        self.update_filename_in_title_and_truncated_filename_for_tab_header_callback("","","")
        self.make_window_fullscreen()
        root.update_idletasks()         # has to be done before checking the widget dimensions with winfo_.. as it else returns 1!
        root.minsize(1000, 550)
        self.last_window_dimensions = (root.winfo_width(), root.winfo_height())
        self.set_heatmaps_frame_size_depending_on_root_size()

        # initializing gui
        self.initialize_GUI()

        # only becomes necessary due to fit result toplevel... strange!
        # so that one can take the main gui into focus again while toplevels are open
        self.parent.bind("<Button-1>", lambda event: self.parent.lift())

        self.parent.bind("<Configure>", lambda _: self.update_heatmaps_frame_size_if_root_window_resized())

        return None

    def read_currently_used_cmaps_from_file(self):
        self.colormaps_dict_file = self.config_files_directory + "/colormaps_for_heatmaps.txt"

        # if user has for some reason deleted the file, set default colormaps:
        if not os.path.exists(self.colormaps_dict_file):
            self.currently_used_cmaps_dict = {"ORIG": "", "SVD": "", "Fit": "", "SVD_diff": "", "Fit_diff": ""}
            with open(self.colormaps_dict_file, mode='w') as dict_file:
                dict_file.write(str(self.currently_used_cmaps_dict))

        else:
            try:
                with open(self.colormaps_dict_file, mode='r') as dict_file:
                    self.currently_used_cmaps_dict = ast.literal_eval(dict_file.read().strip())
            except SyntaxError as error:
                tk.messagebox.showwarning(title="Warning, problem with cmaps config file!",
                                        message="cmaps config file can not be evaluated correctly!\n\n"
                                        +f"error: {error}"
                                        +"\n\nIt should contain only one python dictionary and nothing else!"
                                        +"\n\nProgram will use default cmap!")
                self.currently_used_cmaps_dict = {"ORIG": "", "SVD": "", "Fit": "", "SVD_diff": "", "Fit_diff": ""}

        return None

    def read_initial_fit_parameter_values_from_file(self):
        self.initial_fit_parameter_values_file = self.config_files_directory + "/Initial_fit_parameter_values.txt"

        # if user has for some reason deleted the file that stores initial fit parameter dictionary, set default fit parameter values:
        if not os.path.exists(self.initial_fit_parameter_values_file):
            self.initial_fit_parameter_values = {"time_constants": [50], "amps_rSV0": [0.7]}
            with open(self.initial_fit_parameter_values_file, mode='w') as dict_file:
                dict_file.write(str(self.initial_fit_parameter_values))

        else:
            try:
                with open(self.initial_fit_parameter_values_file, mode='r') as dict_file:
                    self.initial_fit_parameter_values = ast.literal_eval(dict_file.read().strip())
            except SyntaxError as error:
                tk.messagebox.showwarning(title="Warning, problem with fit parameters file!",
                                        message="initial fit parameter values file can not be evaluated correctly!\n\n"
                                        +f"error: {error}"
                                        +"\n\nIt should contain only one python dictionary and nothing else!"
                                        +"\n\nProgram will use default values: {'time_constants': [50], 'amps_rSV0': [0.7]}")
                self.initial_fit_parameter_values = {"time_constants": [50], "amps_rSV0": [0.7]}


        return None

    def make_window_fullscreen(self):
        """ depending on OS different command"""
        # check the operating system:
        self.operating_system = platform.system()

        # Windows:
        if self.operating_system == 'Windows':
            root.wm_state('zoomed')

        # Linux:
        if self.operating_system == 'Linux':
            # possibly:
            root.attributes('-fullscreen', True)

        # Mac:
        if self.operating_system == 'Darwin':
            root.wm_attributes('-fullscreen', 'true')

        return None

    """ callback methods """
    def update_filename_in_title_and_truncated_filename_for_tab_header_callback(self, name, idx, mode):
        """
        name = internal variable name of traced variable\n
        idx = list index of traced variable if name is a list variable, else an empty string\n
        mode = tells you which operation triggered the callback\n
        they are apparently necessary to have a correct syntax with trace_add method
        """
        self.truncated_filename = (os.path.basename(self.curr_reconstruct_data_file_strVar.get())[:8] + '..'+ os.path.basename(self.curr_reconstruct_data_file_strVar.get())[-7:-4]) if len(os.path.splitext(os.path.basename(self.curr_reconstruct_data_file_strVar.get()))[0]) > 13 else os.path.splitext(os.path.basename(self.curr_reconstruct_data_file_strVar.get()))[0]
        self.parent.title("time-resolved data analysis gui - current data file: " + os.path.basename(self.curr_reconstruct_data_file_strVar.get()) + ";  approximate start time value: " + str(self.curr_reconstruct_data_start_time_value.get()))

    def test_value_digits_only(self, inStr, acttyp):
        if acttyp == '1': #insert
            if not inStr.isdigit():
                return False
        return True

    def update_heatmaps_frame_size_if_root_window_resized(self):
        """ Runs everytime a <Configure> event is triggered.
            Then calls a function to resize heatmaps if the gui has been significantly resized.
            If it has been significantly resized, the self.last_window_dimensions property is reset
            so that it can be used to check for the next resize event. """
        # if  root window is still the same size as last time configure event was triggered, do nothing:
        root.update_idletasks()
        updated_window_dimensions = (root.winfo_width(), root.winfo_height())
        resize_epsilon = 30     # in pixels
        if abs(updated_window_dimensions[0] - self.last_window_dimensions[0]) <= resize_epsilon and abs(updated_window_dimensions[1] - self.last_window_dimensions[1]) <= resize_epsilon:
            return None
        self.set_heatmaps_frame_size_depending_on_root_size()

        return None

    def set_heatmaps_frame_size_depending_on_root_size(self):
        """
        checks the app dimension and adjusts the size of the figures and frames used for the heatmaps
        """
        root.update_idletasks()     # has to be done before checking the widget dimensions with winfo_.. as it else returns 1!
        self.last_window_dimensions = (root.winfo_width(), root.winfo_height())

        heatmap_frame_width, heatmap_frame_height = 0,0             # in pixels
        heatmap_figure_width, heatmap_figure_height = 0,0           # in inches

        # somewhat arbitrarily chosen cutoffs that determine new widths, heights of figures
        if root.winfo_width() >= 1100:
            heatmap_figure_width = 9
        if root.winfo_width() >= 1236:
            heatmap_figure_width = 10
        if root.winfo_width() >= 1336:
            heatmap_figure_width = 10
        if root.winfo_width() >= 1436:
            heatmap_figure_width = 11
        if root.winfo_width() >= 1536:
            heatmap_figure_width = 11
        if root.winfo_width() >= 1636:
            heatmap_figure_width = 12
        if root.winfo_width() >= 1736:
            heatmap_figure_width = 12
        if root.winfo_width() >= 1836:
            heatmap_figure_width = 13
        # screen width very small:
        if root.winfo_width() < 1100:
            heatmap_figure_width = 5

        if root.winfo_height() >= 600:
            heatmap_figure_height = 5
        if root.winfo_height() >= 700:
            heatmap_figure_height = 6
        if root.winfo_height() >= 800:
            heatmap_figure_height = 6
        if root.winfo_height() >= 900:
            heatmap_figure_height = 7
        if root.winfo_height() >= 1000:
            heatmap_figure_height = 7
        if root.winfo_height() >= 1100:
            heatmap_figure_height = 8
        # screen height very small:
        if root.winfo_height() < 600:
            heatmap_figure_height = 4

        heatmap_frame_height = (root.winfo_height() - 120) / 2
        heatmap_frame_width = (root.winfo_width() - 350) / 2

        self.heatmaps_geometry_list = [heatmap_frame_width, heatmap_frame_height]
        self.heatmaps_figure_geometry_list = [heatmap_figure_width, heatmap_figure_height]

        return None

    def monitor_thread(self, thread_object, data_object, button, label):
        if thread_object.is_alive():
            # check the thread every 100ms
            self.after(100, lambda: self.monitor_thread(thread_object, data_object, button, label))
        else:
            # data has been computed, now make plot and put it on canvas
            try:
                data_object.make_canvas()
            except AttributeError as error:
                print(f"\nAn exception occurred: {type(error)}\n {error}." +
                        "\nThis is likely due to something not working as expected in the above data preparation of that data object.\n"
                        +"\nTraceback:\n")
                traceback.print_tb(error.__traceback__)
            # return Gui to initial state
            button['state'] = tk.NORMAL
            label.grid_remove()

            return None

    def flash_target_model_btn_callback(self):
        if self.checkbox_use_target_model["state"] == tk.DISABLED:
            self.btn_set_target_model_fit_function.flash()

        return None

    """ methods to update and check Gui variables """
    def update_components(self, lis_of_IntVars):
        """ loops through a list of input IntVars (from checkButtons) and returns a binary list that specifies which IntVars are 1 and which zero"""
        components_to_plot = []
        for checkbox in range(len(lis_of_IntVars)):
            components_to_plot.append(lis_of_IntVars[checkbox].get())

        if 1 not in components_to_plot:
            raise ValueError('You did not select any components!\nThat needs to be done for the SVD and SVDGF plots, and also to define a fit function.')

        return components_to_plot

    def get_components_to_use(self):
        try:
            components = self.update_components(self.checkbutton_vars_reconstruct_data)
        except ValueError as error:
            tk.messagebox.showerror("Warning!", error)
            print("\nencountered error with message: " + str(error))
            # do nothing
            return None

        components_to_use = [i for i in range(len(components)) if(components[i]==1)]

        return components_to_use

    def set_curr_fileVar(self, file_var):
        filename = tk.filedialog.askopenfilename(initialdir=self.base_directory+"/DataFiles", title="Select a file to work with", filetypes=self.ftypes)

        if filename != "":
            file_var.set(filename)

    def string_is_number(self, some_string):
        try:
            float(some_string)
            return True
        except ValueError as error:
            tk.messagebox.showerror("Warning,", "an exception occurred!""\nTry entering another start time!\n"+
                                    f"Exception {type(error)} message: \n"+ str(error)+"\n")

            return False

    def set_curr_start_time_value(self):
        start_time_value_candidate = tk.simpledialog.askstring('Enter the start time value',
                                                                'curr entered start time value is approx: \n' + str(self.curr_reconstruct_data_start_time_value.get())
                                                                + "\nThe program will try to use the time delay that is closest to what you entered.", initialvalue=self.curr_reconstruct_data_start_time_value.get())

        # user cancelled: do nothing
        if start_time_value_candidate is None:
            return None

        # user did not cancel: check if i can parse entered start time to float:
        if start_time_value_candidate!=None and self.string_is_number(start_time_value_candidate):
            start_time_value_candidate.lstrip("0")
            self.curr_reconstruct_data_start_time_value.set(float(start_time_value_candidate))

        return None

    def handler_assign_initial_fit_parameter_values(self, new_initial_values_dict_from_toplevel):
        self.initial_fit_parameter_values = new_initial_values_dict_from_toplevel

        return None

    def set_initial_fit_parameter_values(self):
        self.initial_fit_parameter_values_window = initial_fit_parameter_values_Toplevel.initial_fit_parameters_Window(self, self.initial_fit_parameter_values_file, self.initial_fit_parameter_values, self.handler_assign_initial_fit_parameter_values, data_file_name=self.curr_reconstruct_data_file_strVar.get(), target_model_configuration_file=self.target_model_fit_function_file, components_list=self.get_components_to_use())
        self.wait_window(self.initial_fit_parameter_values_window)

        return None

    def define_target_model_fit_function(self):
        self.components_to_use = self.get_components_to_use()
        if (self.components_to_use is None):
            # getting components failed, do nothing
            return None

        self.define_target_model_window = target_model_Toplevel.target_model_Window(self, self.components_to_use, self.target_model_fit_function_file)
        self.wait_window(self.define_target_model_window)

        return None

    def handler_assign_colormaps_for_heatmaps(self, new_colormaps_dict):
        self.currently_used_cmaps_dict = new_colormaps_dict
        return None

    def set_colormaps_for_heatmaps(self):
        self.set_colormaps_window = ChooseColorMaps_Toplevel.SetColorMapWindow(self, self.colormaps_dict_file, self.currently_used_cmaps_dict, self.handler_assign_colormaps_for_heatmaps)

        return None

    def check_curr_fileVar_exists(self, file_var):
        if file_var.get()=="no file selected":
            self.set_curr_fileVar(file_var)
            if file_var.get()=="no file selected":
                # do nothing if user cancelled
                return "Cancelled"

    def get_index_of_next_tab_for_nb(self, notebook, maximum_allowed_nr_of_tabs_on_nb):
        """
        finding the right index of the next tab to be put on the notebook.
        this is a bit complicated, so that the user can delete tabs however they want
        and still get the next tab at a useful position
        """

        if not notebook.winfo_ismapped():
            return 0

        else :
            mapped_tabs = []
            for tab_id in notebook.tabs():
                tab_title_string = notebook.tab(notebook.index(tab_id), "text")
                # print(f'notebook.index(tab_id): {notebook.index(tab_id)}')
                if tab_title_string[1] == ":":
                    mapped_tabs.append(int(tab_title_string[0]))
                else:
                    mapped_tabs.append(int(tab_title_string[0:2]))
            mapped_tabs.sort()
            # print(f'mapped tabs: {mapped_tabs}')

            for nr in range(1, maximum_allowed_nr_of_tabs_on_nb+1):
                if nr in mapped_tabs:
                    continue
                next_tab_idx_on_nb = nr - 1
                break

            return next_tab_idx_on_nb

    def remove_correct_tab_from_difference_nb(self, tab_title_nr):
        """nb.forget the difference tab corresponding/belonging to the SVD or SVDGF data object whose tab is
        removed in the first place

        Args:
            tab_title_nr (int): the number that is at the start of the title of the tab to be forgotten.

        Returns:
            Nonetype: None
        """

        tab_title_nr_as_string = str(tab_title_nr)
        notebook = self.nbCon_difference.tab_control

        if tab_title_nr < 10:
            for tab_id in notebook.tabs():
                tab_title_string = notebook.tab(notebook.index(tab_id), "text")
                if tab_title_string[0] == tab_title_nr_as_string:
                    notebook.forget(tab_id)
                    break
        else:
            for tab_id in notebook.tabs():
                tab_title_string = notebook.tab(notebook.index(tab_id), "text")
                if tab_title_string[0:2] == tab_title_nr_as_string:
                    notebook.forget(tab_id)
                    break
        return None

    def too_many_such_tabs(self, nb, tab_idx_string, maximum_allowed_nr_of_tabs_on_nb):
        if hasattr(self, tab_idx_string) and nb.index(tk.END)+1 > maximum_allowed_nr_of_tabs_on_nb:
            tk.messagebox.showerror("Warning, too many tabs!", f"maximum number of allowed tabs is {maximum_allowed_nr_of_tabs_on_nb}")
            return True
        else:
            return False

    def check_if_tab_with_tab_index_is_mapped_on_nb(self, nb, tab_idx):
        mapped_tabs = []
        for tab_id in nb.tabs():
            tab_title_string = nb.tab(nb.index(tab_id), "text")
            if tab_title_string[1] == ":":
                mapped_tabs.append(int(tab_title_string[0]))
            else:
                mapped_tabs.append(int(tab_title_string[0:2]))
        mapped_tabs.sort()

        if not tab_idx in mapped_tabs:
            tk.messagebox.showerror("Warning!", "Check the tab number for which you want to see the DAS!")
            return None

        return True

    """ methods to clear Gui variables and frames and tabs """
    def remove_frms(self, lis_of_frame):
        if isinstance(lis_of_frame, collections.abc.Iterable):
            for frm in lis_of_frame:
                frm.grid_remove()
        else :
            lis_of_frame.grid_remove()

    def return_some_gui_widgets_to_initial_state(self, button=None, label=None, tab_control=None):
        if button:
            button["state"] = tk.ACTIVE
        if label:
            label.grid_remove()
        if tab_control:
            tab_control.forget("current")

            if tab_control.index(tk.END) == 0:
                tab_control.grid_remove()

        return None

    """ methods to show additional information in tk.Toplevels etc """
    def show_SVDGF_fit_result_toplevel(self, event=None):
        """ event = None is needed because used as callback"""
        if self.ent_show_SVDGF_result_toplevel.get() == "" or self.ent_show_SVDGF_result_toplevel.get() == "0":
            tk.messagebox.showerror("Warning!", "Check the tab number for which you want to see the fit results!")
            return None
        if not self.check_if_tab_with_tab_index_is_mapped_on_nb(self.nbCon_SVDGF.tab_control, int(self.ent_show_SVDGF_result_toplevel.get())):
            return None

        tab_index = int(self.ent_show_SVDGF_result_toplevel.get()) - 1

        try:
            self.fit_report_toplevels.append(FitResult_Toplevel.FitResult_Window(self, tab_index, lmfit.fit_report(self.nbCon_SVDGF.data_objs[tab_index].fit_result), self.nbCon_SVDGF.data_objs[tab_index]))

        except (IndexError, AttributeError) as error:
            tk.messagebox.showerror("Warning, an exception occurred!", f"Exception {type(error)} message: \n"+ str(error)+"\n"
                                    +"\nHave you already computed the fit for that tab?!")

        return None

    def show_DAS_toplevel(self, event=None):
        """ event = None is needed because used as callback"""
        if self.ent_show_DAS_toplevel.get() == "" or self.ent_show_DAS_toplevel.get() == "0":
            tk.messagebox.showerror("Warning!", "Check the tab number for which you want to see the DAS!")
            return None
        if not self.check_if_tab_with_tab_index_is_mapped_on_nb(self.nbCon_SVDGF.tab_control, int(self.ent_show_DAS_toplevel.get())):
            return None

        tab_index = int(self.ent_show_DAS_toplevel.get()) - 1

        try:
            self.DAS_toplevels.append(DAS_Toplevel.DAS_Window(self, tab_index, self.nbCon_SVDGF.data_objs[tab_index]))

        except (IndexError, AttributeError) as error:
            tk.messagebox.showerror("Warning, an exception occurred!", f"Exception {type(error)} message: \n"+ str(error)+"\n"
                                    +"\nHave you already computed the fit for that tab?!")

        return None

    """ methods to make different kind of notebook tabs """
    def show_orig_data_heatmap(self):
        if self.too_many_such_tabs(self.nbCon_orig.tab_control, "next_tab_idx_orig", self.NR_OF_TABS):
            return None

        # check whether a file and start time has been selected at all to create a heatmap from
        file_state = self.check_curr_fileVar_exists(self.curr_reconstruct_data_file_strVar)
        if file_state == "Cancelled":
            return None

        # disable the used button during computation
        self.btn_show_orig_data_heatmap['state'] = tk.DISABLED

        # put a reassuring label on gui because this computation takes some time
        self.lbl_reassuring_orig.grid(row=self.btn_quit.grid_info()["row"], column=self.btn_quit.grid_info()["column"])

        # make tabs with heatmap plots:
        self.next_tab_idx_orig = self.get_index_of_next_tab_for_nb(self.nbCon_orig.tab_control, self.NR_OF_TABS)
        if not self.nbCon_orig.tab_control.winfo_ismapped():
            self.nbCon_orig.tab_control.grid(row=0, column=2, sticky="ne")
        self.nbCon_orig.add_indexed_tab(self.next_tab_idx_orig, title=str(self.curr_reconstruct_data_start_time_value.get()) + " " + self.truncated_filename)

        self.nbCon_orig.data_objs[self.next_tab_idx_orig] = ORIGData.ORIGData_Heatmap(self, self.next_tab_idx_orig, self.curr_reconstruct_data_file_strVar.get(), self.curr_reconstruct_data_start_time_value.get(), self.truncated_filename, self.currently_used_cmaps_dict)
        thread_instance_orig = threading.Thread(target=self.nbCon_orig.data_objs[self.next_tab_idx_orig].make_data)
        thread_instance_orig.start()
        self.monitor_thread(thread_instance_orig, self.nbCon_orig.data_objs[self.next_tab_idx_orig], self.btn_show_orig_data_heatmap, self.lbl_reassuring_orig)

        return None

    def show_SVD_reconstructed_data_heatmap(self):
        if self.too_many_such_tabs(self.nbCon_SVD.tab_control, "next_tab_idx_SVD", self.NR_OF_TABS):
            return None

        # check whether a file and start time has been selected at all to create a heatmap from
        file_state = self.check_curr_fileVar_exists(self.curr_reconstruct_data_file_strVar)
        if file_state == "Cancelled":
            return None

        self.components_to_use = self.get_components_to_use()
        if (self.components_to_use is None):
            # getting components failed, do nothing
            return None

        # disable the used button during computation
        self.btn_show_SVD_reconstructed_data_heatmap['state'] = tk.DISABLED
        # a reassuring label because this computation takes some time
        self.lbl_reassuring_SVD.grid(row=self.btn_quit.grid_info()["row"], column=self.btn_quit.grid_info()["column"])

        # make tabs with heatmap plots:
        self.next_tab_idx_SVD = self.get_index_of_next_tab_for_nb(self.nbCon_SVD.tab_control, self.NR_OF_TABS)
        if not self.nbCon_SVD.tab_control.winfo_ismapped():
            self.nbCon_SVD.tab_control.grid(row=0, column=1, sticky="nw")
        self.nbCon_SVD.add_indexed_tab(self.next_tab_idx_SVD, title=str(self.components_to_use))

        self.next_tab_idx_difference = self.get_index_of_next_tab_for_nb(self.nbCon_difference.tab_control, self.NR_OF_DIFFERENCE_TABS)
        if not self.nbCon_difference.tab_control.winfo_ismapped():
            self.nbCon_difference.tab_control.grid(row=1, column=2, sticky="ne")
        self.nbCon_difference.add_indexed_tab(self.next_tab_idx_difference, title="SVD "+str(self.next_tab_idx_SVD+1))

        self.nbCon_SVD.data_objs[self.next_tab_idx_SVD] = SVD_reconstruction.SVD_Heatmap(self, self.curr_reconstruct_data_file_strVar.get(), self.curr_reconstruct_data_start_time_value.get(), self.components_to_use, self.next_tab_idx_SVD, self.next_tab_idx_difference, self.currently_used_cmaps_dict)
        thread_instance_SVD = threading.Thread(target=self.nbCon_SVD.data_objs[self.next_tab_idx_SVD].make_data)
        thread_instance_SVD.start()
        self.monitor_thread(thread_instance_SVD, self.nbCon_SVD.data_objs[self.next_tab_idx_SVD], self.btn_show_SVD_reconstructed_data_heatmap, self.lbl_reassuring_SVD)

        return None

    def show_SVD_GlobalFit_reconstructed_data_heatmap(self):
        if self.too_many_such_tabs(self.nbCon_SVDGF.tab_control, "next_tab_idx_SVDGF", self.NR_OF_TABS):
            return None

        # check whether a file and start time has been selected at all to create a heatmap from
        file_state = self.check_curr_fileVar_exists(self.curr_reconstruct_data_file_strVar)
        if file_state == "Cancelled":
            return None

        self.components_to_use = self.get_components_to_use()
        if (self.components_to_use is None):
            # getting components failed, do nothing
            return None

        # convolution in fit is not yet implemented!
        self.temporal_resolution_in_ps = int(self.ent_temporal_resolution_in_fs.get())/1000
        self.time_zero_in_ps = int(self.ent_time_zero.get())/1000

        # disable the used button during computation
        self.btn_show_SVDGF_reconstructed_data_heatmap['state'] = tk.DISABLED

        # put a reassuring label on gui because this computation takes some time
        self.lbl_reassuring_SVDGF.grid(row=self.btn_quit.grid_info()["row"], column=self.btn_quit.grid_info()["column"])

        # make tabs with heatmap plots:
        self.next_tab_idx_SVDGF = self.get_index_of_next_tab_for_nb(self.nbCon_SVDGF.tab_control, self.NR_OF_TABS)
        if not self.nbCon_SVDGF.tab_control.winfo_ismapped():
            self.nbCon_SVDGF.tab_control.grid(row=1, column=1, sticky="nw")
        self.nbCon_SVDGF.add_indexed_tab(self.next_tab_idx_SVDGF, title=str(self.components_to_use))

        self.next_tab_idx_difference = self.get_index_of_next_tab_for_nb(self.nbCon_difference.tab_control, self.NR_OF_DIFFERENCE_TABS)
        if not self.nbCon_difference.tab_control.winfo_ismapped():
            self.nbCon_difference.tab_control.grid(row=1, column=2, sticky="ne")
        self.nbCon_difference.add_indexed_tab(self.next_tab_idx_difference, title="SVDGF "+str(self.next_tab_idx_SVDGF+1))

        self.nbCon_SVDGF.data_objs[self.next_tab_idx_SVDGF] = SVDGF_reconstruction.SVDGF_Heatmap(self, self.curr_reconstruct_data_file_strVar.get(), self.curr_reconstruct_data_start_time_value.get(), self.components_to_use, self.temporal_resolution_in_ps, self.time_zero_in_ps, self.next_tab_idx_SVDGF, self.next_tab_idx_difference, self.initial_fit_parameter_values, bool(self.checkbox_var_use_target_model.get()), self.currently_used_cmaps_dict, self.target_model_fit_function_file)
        thread_instance_SVDGF = threading.Thread(target=self.nbCon_SVDGF.data_objs[self.next_tab_idx_SVDGF].make_data)
        thread_instance_SVDGF.start()
        self.monitor_thread(thread_instance_SVDGF, self.nbCon_SVDGF.data_objs[self.next_tab_idx_SVDGF], self.btn_show_SVDGF_reconstructed_data_heatmap, self.lbl_reassuring_SVDGF)

        return None

    """ set up Gui """
    def initialize_main_frame(self):
        """
        sets up the main frame on self.parent
        """
        self.frm_main = tk.Frame(self.parent, bg=self.grey)

        # configuring the main frames in tabs and placing tabs
        self.frm_main.rowconfigure(0, weight=1)                                  # weight determines how much space the row/col takes proportionally to other rows/cols
        self.frm_main.columnconfigure((0,4), weight=0)
        self.frm_main.columnconfigure((1,2), weight=1)

        self.parent.rowconfigure(0, weight=1)
        self.parent.columnconfigure(0, weight=1)

        self.frm_main.grid(row=0, column=0, sticky="nsew")

    def initialize_tab1(self):
        """ widgets for original data heatmap generation """
        self.frm_orig_data_tab1 = tk.Frame(self.frm_main, bg=self.gold,)
        self.frm_orig_data_tab1.grid(row=0, column=4, sticky="nse", rowspan=2)

        self.btn_show_orig_data_heatmap = tk.Button(self.frm_orig_data_tab1, text="show original data", command=self.show_orig_data_heatmap)
        self.btn_show_orig_data_heatmap.grid(row=0, column=0, padx=3, pady=5, sticky="ew")

        # self.lbl_reassuring_orig = tk.Label(self.frm_orig_data_tab1, text="patience, padawan")
        self.lbl_reassuring_orig = tk.Label(self.parent, text="patience, padawan - still computing")

        # Notebook, Frame, Figure, Axes and Canvas Container
        self.nbCon_orig = NotebookContainer.NotebookContainer(self, self.frm_main, self.NR_OF_TABS, figsize=(10,5))

        """ buttons to change data file and start time value """
        self.btn_update_curr_reconstruct_data_file_strVar = tk.Button(self.frm_orig_data_tab1, text="change data file", command=lambda x=self.curr_reconstruct_data_file_strVar: self.set_curr_fileVar(x))
        self.btn_update_curr_reconstruct_data_file_strVar.grid(row=1, column=0, padx=3, pady=5, sticky="ew")

        self.btn_change_reconstruct_start_time_value = tk.Button(self.frm_orig_data_tab1, text="change start time value", command=self.set_curr_start_time_value)
        self.btn_change_reconstruct_start_time_value.grid(row=2, column=0, padx=3, pady=5, sticky="ew")

        """ widgets for SVD_reconstruction data heatmap generation """
        self.frm_update_reconstruct_data_tab1 = tk.Frame(self.frm_main, bg=self.gold,)
        self.frm_update_reconstruct_data_tab1.grid_propagate(1)                                   # 0 fixes the frame size, no matter what widgets it contains
        self.frm_update_reconstruct_data_tab1.grid(row=0, column=0, sticky="nsw", rowspan=2)

        # a label to explain how ticked components are used
        self.lbl_select_components = tk.Label(self.frm_update_reconstruct_data_tab1, text="Select components", fg=self.violet)
        self.lbl_select_components.grid(sticky='', pady=5, padx=3)
        ttp_lbl_select_components = ToolTip.CreateToolTip(self.lbl_select_components, \
        'Components are used for SVD or SVDGlobalFit reconstruction. '
        'SVD_Reconstructed data = '
        'Sum_over_components: leftSVs * singular values * rightSVs. '
        'SVD_GF_Reconstructed data = '
        'Sum_over_components: DAS_i(lambda)*exp(-t/decay_constant_i). '
        'The DAS_i and the decay_constants_i are '
        'results of the global fit. ')

        # listing component checkbuttons and placing them
        nr_checkboxes_reconstruct_data = 10
        self.checkbutton_vars_reconstruct_data = [tk.IntVar(0) for _ in range(nr_checkboxes_reconstruct_data)]

        # set some checkbuttons as checked -- for convenience when testing
        for i in range(nr_checkboxes_reconstruct_data-8):
            self.checkbutton_vars_reconstruct_data[i].set(1)

        checkbuttons = [tk.Checkbutton(self.frm_update_reconstruct_data_tab1, text="component "+str(checkbox), variable=self.checkbutton_vars_reconstruct_data[checkbox], onvalue=1, offvalue=0) for checkbox in range(nr_checkboxes_reconstruct_data)]

        for checkbox in range(nr_checkboxes_reconstruct_data):
            checkbuttons[checkbox].grid(row=checkbox+1, column=0, sticky='sew', padx=3)

        self.btn_show_SVD_reconstructed_data_heatmap = tk.Button(self.frm_update_reconstruct_data_tab1, text="show SVD components data", command=self.show_SVD_reconstructed_data_heatmap)
        self.btn_show_SVD_reconstructed_data_heatmap.grid(column=0, padx=3, pady=5, sticky="ew")

        # self.lbl_reassuring_SVD = tk.Label(self.frm_update_reconstruct_data_tab1, text="patience, padawan")
        self.lbl_reassuring_SVD = tk.Label(self.parent, text="patience, padawan - still computing")

        # notebook container for SVD reconstruction heatmap
        self.nbCon_SVD = NotebookContainer.NotebookContainer(self, self.frm_main, self.NR_OF_TABS, figsize=(10,5))

        """ widgets for SVD_GlobalFit_reconstruction heatmap generation, this reconstruction also uses widgets and variables for SVD_reconstruction! """
        self.lbl_temporal_resolution = tk.Label(self.frm_update_reconstruct_data_tab1, text="set temporal res [fs]: ", fg=self.violet)
        self.ent_temporal_resolution_in_fs = tk.Entry(self.frm_update_reconstruct_data_tab1, width=6, fg=self.violet, validate="key", justify=tk.RIGHT, validatecommand=(self.register(self.test_value_digits_only),'%P','%d'))
        self.ent_temporal_resolution_in_fs.insert(0, 0)
        ttp_lbl_temporal_resolution = ToolTip.CreateToolTip(self.lbl_temporal_resolution, \
        'NOT USED AT THE MOMENT!\n'
        'Might be Used for SVDGF reconstruction: '
        'Entered value will be internally reformatted to [ps], e.g.: 500 fs => 0.5 ps. '
        'The reformatted value is used by the fit function for the convolution. '
        'The value corresponds to the instrument response function\'s FWHM.')

        self.lbl_temporal_resolution.grid(padx=3, pady=5, sticky="w")
        grid_info_lbl_temporal_resolution = self.lbl_temporal_resolution.grid_info()
        self.ent_temporal_resolution_in_fs.grid(row=grid_info_lbl_temporal_resolution["row"], padx=3, pady=5, sticky="e")

        self.lbl_time_zero = tk.Label(self.frm_update_reconstruct_data_tab1, text="time zero [fs]: ", fg=self.violet)
        self.ent_time_zero = tk.Entry(self.frm_update_reconstruct_data_tab1, width=6, fg=self.violet, validate="key", justify=tk.RIGHT, validatecommand=(self.register(self.test_value_digits_only),'%P','%d'))
        self.ent_time_zero.insert(0, 0)
        ttp_lbl_time_zero = ToolTip.CreateToolTip(self.lbl_time_zero, \
        'NOT USED AT THE MOMENT!\n'
        'Might be Used for SVDGF reconstruction: '
        'Entered value will be internally reformatted to [ps], e.g.: 500 fs => 0.5 ps. '
        'The reformatted value is used by the fit function for the convolution.')

        self.lbl_time_zero.grid(padx=3, pady=5, sticky="w")
        self.ent_time_zero.grid(row=self.lbl_time_zero.grid_info()["row"], padx=3, pady=5, sticky="e")

        self.btn_show_SVDGF_reconstructed_data_heatmap = tk.Button(self.frm_update_reconstruct_data_tab1, text="show SVD fit data", command=self.show_SVD_GlobalFit_reconstructed_data_heatmap)
        self.btn_show_SVDGF_reconstructed_data_heatmap.grid(column=0, padx=3, pady=5, sticky="ew")

        # self.lbl_reassuring_SVDGF = tk.Label(self.frm_update_reconstruct_data_tab1, text="patience, padawan")
        self.lbl_reassuring_SVDGF = tk.Label(self.parent, text="patience, padawan - still computing")

        # notebook container for SVDGF reconstruction heatmap
        self.nbCon_SVDGF = NotebookContainer.NotebookContainer(self, self.frm_main, self.NR_OF_TABS, figsize=(10,5))

        # to show SVDGF fit results in tk.Toplevel
        self.fit_report_toplevels = []
        self.lbl_show_SVDGF_result_toplevel = tk.Label(self.frm_update_reconstruct_data_tab1, text="fit results for tabnr?", fg=self.violet)
        ttp_lbl_show_SVDGF_result_toplevel = ToolTip.CreateToolTip(self.lbl_show_SVDGF_result_toplevel, \
        'Enter an number of an existing SVDGF tab and hit return!')
        self.ent_show_SVDGF_result_toplevel = tk.Entry(self.frm_update_reconstruct_data_tab1, width=6, fg=self.violet, validate="key", validatecommand=(self.register(self.test_value_digits_only),'%P','%d'), justify=tk.RIGHT)

        self.lbl_show_SVDGF_result_toplevel.grid(column=0, sticky='sw', pady=5, padx=3)
        self.ent_show_SVDGF_result_toplevel.grid(row=self.lbl_show_SVDGF_result_toplevel.grid_info()["row"], padx=3, pady=5, sticky="se")
        self.ent_show_SVDGF_result_toplevel.bind("<Return>", self.show_SVDGF_fit_result_toplevel)

        # to show DAS of SVDGF fit data object in tk.Toplevel:
        self.DAS_toplevels = []
        self.lbl_show_DAS_toplevel = tk.Label(self.frm_update_reconstruct_data_tab1, text="DAS for tabnr?", fg=self.violet)
        ttp_lbl_show_DAS_toplevel = ToolTip.CreateToolTip(self.lbl_show_DAS_toplevel, \
        'Enter an number of an existing SVDGF tab and hit return!')
        self.ent_show_DAS_toplevel = tk.Entry(self.frm_update_reconstruct_data_tab1, width=6, fg=self.violet, validate="key", validatecommand=(self.register(self.test_value_digits_only),'%P','%d'), justify=tk.RIGHT)

        self.lbl_show_DAS_toplevel.grid(column=0, sticky='sw', pady=5, padx=3)
        self.ent_show_DAS_toplevel.grid(row=self.lbl_show_DAS_toplevel.grid_info()["row"], padx=3, pady=5, sticky="se")
        self.ent_show_DAS_toplevel.bind("<Return>", self.show_DAS_toplevel)

        """ notebook for difference matrices """
        self.nbCon_difference = NotebookContainer.NotebookContainer(self, self.frm_main, self.NR_OF_DIFFERENCE_TABS, figsize=(10,5))

        """ widgets for user defined target model fit function """
        self.btn_set_target_model_fit_function = tk.Button(self.frm_update_reconstruct_data_tab1, text="Define fit function", command=self.define_target_model_fit_function, activebackground=self.flashwidgetcolor)
        ttp_btn_set_target_model_fit_function = ToolTip.CreateToolTip(self.btn_set_target_model_fit_function, \
        'Open a window to define a target model fit function '
        'which, if it is  successfully parsed, can be used in fit procedure.',
        optional_y_direction_bump=90, optional_x_direction_bump=10)
        self.btn_set_target_model_fit_function.grid(sticky="sw", padx=10, pady=5, ipady=2, ipadx=5, column=0)
        self.frm_update_reconstruct_data_tab1.rowconfigure(self.btn_set_target_model_fit_function.grid_info()["row"], weight=1)   # so that the new button is at the bottom of frame

        self.checkbox_var_use_target_model = tk.IntVar(0)
        self.checkbox_use_target_model = tk.Checkbutton(self.frm_update_reconstruct_data_tab1, text="", bg=self.gold, activebackground=self.gold, variable=self.checkbox_var_use_target_model, onvalue=1, offvalue=0, state=tk.DISABLED)
        ttp_checkbox_use_target_model = ToolTip.CreateToolTip(self.checkbox_use_target_model, \
        'If checked, and the user entered fit function has been successfully parsed,'
        ' the fit procedure will use the entered fit function. \n\n'
        'Is only enabled when a target model has been entered in window (button on the left).',
        optional_y_direction_bump=90, optional_x_direction_bump=10)
        self.checkbox_use_target_model.grid(row=self.btn_set_target_model_fit_function.grid_info()["row"], sticky="se", pady=8, padx=3)
        self.checkbox_use_target_model.bind("<ButtonPress>", lambda x: self.flash_target_model_btn_callback())

        """button to set colormaps for heatmaps"""
        self.btn_set_colormaps = tk.Button(self.frm_orig_data_tab1, text="set colormaps for\n heatmaps", command=self.set_colormaps_for_heatmaps)
        self.btn_set_colormaps.grid(row=3, column=0, padx=3, pady=5, sticky="s")
        self.frm_orig_data_tab1.rowconfigure(self.btn_set_colormaps.grid_info()["row"], weight=1)

        return None

    # Widget layout of GUI
    def initialize_GUI(self):
        # Tabs and frames setup
        self.initialize_main_frame()

        # placing widgets on tab 1
        self.initialize_tab1()

        # button to change initial fit parameter values
        self.btn_set_initial_fit_parameter_values = tk.Button(self.parent, text="Set initial fit parameter values", command=self.set_initial_fit_parameter_values)
        ttp_btn_set_initial_fit_parameter_values = ToolTip.CreateToolTip(self.btn_set_initial_fit_parameter_values, \
        'Open a window to display and possibly change the values that are used '
        'as initial parameter values in SVDGF procedure.'
        '\n\nWhenever these values are changed, the new ones will be used for each fit until the user selects to change them again.'
        '\nTo be able to reuse the latest user selected values when user quits and restarts program, the values are written to a file.',
        optional_y_direction_bump=200, optional_x_direction_bump=150)
        self.btn_set_initial_fit_parameter_values.grid(sticky="sw", padx=0, pady=3, ipady=2, ipadx=0)

        # quit button
        self.btn_quit = tk.Button(self.parent, text="Quit App", command=quit)
        self.btn_quit.grid(sticky="se", padx=5, pady=3, ipady=2, ipadx=5, row=self.btn_set_initial_fit_parameter_values.grid_info()["row"])

if __name__ == '__main__':
    root=tk.Tk()
    app=GuiAppTAAnalysis(root)
    root.mainloop()
