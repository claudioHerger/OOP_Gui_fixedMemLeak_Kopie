import tkinter as tk
import ast
import re
import numpy as np

from SupportClasses import ToolTip

class initial_fit_parameters_Window(tk.Toplevel):
    def __init__(self, parent, file_name, current_values, assign_handler):
        """a toplevel window to see and change the values used as initial values in the SVDGF procedure.
        Whenever these values are changed, the new ones will be used for each fit until the user selects to change them again.
        In order to reuse these selected values once the user quits and restarts the program, the values are written to a file.
        From there they are again read when the user starts the program again.

        Args:
            parent (tk.Frame): the root window.
            file_name (str): file to write new initial fit parameter values in
            current_values (dict): dictionary of currently used initial fit parameter values
            assign_handler (function): method that handles the assignement of new initial fit values in main Gui which instantiates the toplevel.
        """
        super().__init__(parent)
        self.parent = parent
        self.old_initial_fit_parameter_values = current_values
        self.file_name = file_name
        self.assign_handler = assign_handler

        self.title('Set the initial fit parameter values - used for each fit.')

        self.btn_ignore_and_quit = tk.Button(self, text="Hit Enter: Ignore and quit", command=lambda: self.ignore_and_quit())
        ttp_btn_ignore_and_quit = ToolTip.CreateToolTip(self.btn_ignore_and_quit, \
        'Quit this window and use the last saved fit parameters.')
        self.btn_ignore_and_quit.grid(padx=10, pady=10, sticky="se", row=99, column=3)

        self.display_fit_parameters_labels_and_entries()

        self.btn_assign_new_fit_parameter_values = tk.Button(self, text="use entered values", command=self.assign_new_values_if_correct_format)
        ttp_btn_assign_new_fit_parameter_values = ToolTip.CreateToolTip(self.btn_assign_new_fit_parameter_values, \
        'Saves the entered values to file and closes the window.')
        self.btn_assign_new_fit_parameter_values.grid(padx=10, pady=10, sticky="sw", row=99, column=0)

        self.btn_help = tk.Button(self, text="help", command=self.display_help_window)
        ttp_btn_help = ToolTip.CreateToolTip(self.btn_help, \
        'If you are confused by the number of parameters.')
        self.btn_help.grid(padx=10, row=0, column=0)

        self.btn_add_more_parameters = tk.Button(self, text="add more parameters", command=self.add_more_parameters_and_widgets)
        ttp_btn_add_more_parameters = ToolTip.CreateToolTip(self.btn_add_more_parameters, \
        'Adds another entry to write amplitudes into, also adds some default values at the end of the lists in the already existing entries.')
        self.btn_add_more_parameters.grid(padx=10, pady=10, sticky="sw", row=99, column=1)

        self.btn_remove_parameters = tk.Button(self, text="remove last parameters", command=self.remove_last_parameters)
        ttp_btn_remove_parameters = ToolTip.CreateToolTip(self.btn_remove_parameters, \
        'Removes the parameters for the last component.')
        self.btn_remove_parameters.grid(pady=10, sticky="se", row=99, column=2)

        self.grab_set()         # to keep the window in front of application until it gets closed
        self.focus_set()
        self.bind("<Return>", lambda x: self.ignore_and_quit())

    def remove_last_parameters(self):
        try:
            self.row_labels[-1].grid_forget()
            self.row_labels = self.row_labels[0:-1]

            self.new_values_entries[-1].grid_forget()
            self.new_values_entries = self.new_values_entries[0:-1]
        except IndexError:
            tk.messagebox.showwarning(title="Warning", message=f"No more parameters to remove!")
            return None

        try:
            for entry_index, entry in enumerate(self.new_values_entries):
                curr_list = ast.literal_eval(self.new_values_entries[entry_index].get())
                entry.delete(0, len(str(curr_list)))
                curr_list = curr_list[0:-1]
                entry.insert(0, str(curr_list))
        except SyntaxError:
            tk.messagebox.showwarning(title="Warning.", message=f"One of your remaining entered lists could not be evaluated to a list.")
            return None

        self.add_up_and_down_key_bindings_to_entries()

        return None

    def add_more_parameters_and_widgets(self):
        self.row_labels.append(tk.Label(self))
        self.row_labels[-1]["text"] = f"amps_rSV{len(self.row_labels)-2}"
        self.old_values_labels.append(tk.Label(self, text="did not exist yet"))
        self.new_values_entries.append(tk.Entry(self, width=50, justify=tk.RIGHT))
        self.new_values_entries[-1].insert(0, self.new_values_entries[1].get())

        self.row_labels[-1].grid(padx=10, sticky="nsew", row=self.row_labels[-2].grid_info()["row"]+1, column=0)
        self.old_values_labels[-1].grid(padx=10, sticky="nsew", row=self.old_values_labels[-2].grid_info()["row"]+1, column=1)
        self.new_values_entries[-1].grid(sticky="nsew", row=self.new_values_entries[-2].grid_info()["row"]+1, column=2)

        for entry_index, entry in enumerate(self.new_values_entries):
            if entry_index == 0:
                entry.insert(len(entry.get())-1, ", 50")
            else:
                entry.insert(len(entry.get())-1, ", 0.7")

        self.add_up_and_down_key_bindings_to_entries()

        return None

    def display_help_window(self):
        helpful_information = """given a set of selected components, there will be a corresponding set of right singular vectors (rSV) V_i to fit.
        For each V_i there will be an individual fit function f_i.\n
        The generic fit function has nrOfSelectedComponents decay constants and
        nrOfSelectedComponents * nrOfSelectedComponents amplitudes.
        So all in all there are nrOfSelectedComponents * (nrOfSelectedComponents+1) parameters.

        The parameter lists in the entries each need to contain at least as many values as the maximum component nr + 1.
        I.e. if the selected components are [0,1,3]: each parameter list needs to contain at least 4 values,
        as the fit procedure tries to access these lists at the indeces corresponding to the selected componets list, e.g. [0,1,3].

        If that condition is not fulfilled, the fit procedure will use default parameters and inform you about the error.

        Pressing the 'use entered values' button attempts to parse the values to floats, if it fails you will be informed.
        """
        tk.messagebox.showinfo(title="hopefully helpful information window", message=re.sub('^[ \t]*',"",helpful_information, flags=re.MULTILINE), parent=self, default = "ok", )
        return None

    def add_up_and_down_key_bindings_to_entries(self):
        for i in range(len(self.new_values_entries)):
            if i+1 < len(self.new_values_entries):
                self.new_values_entries[i].bind("<Key-Down>", lambda event, idx=i: self.handle_down_key_press(event, idx))
            if i > 0:
                self.new_values_entries[i].bind("<Key-Up>", lambda event, idx=i: self.handle_up_key_press(event, idx))

        return None

    def display_fit_parameters_labels_and_entries(self):
        self.column_labels = [tk.Label(self, text="old values:"), tk.Label(self, text="new values:")]
        self.components_label = tk.Label(self, text="comp0, 1, 2, ...")
        self.components_label2 = tk.Label(self, text="comp0, 1, 2, ...")
        for index,col_label in enumerate(self.column_labels):
            col_label.grid(padx=10, sticky="nsew", row=0, column=index+1)
        self.components_label.grid(padx=10, sticky="nsew", row=1, column=1)
        self.components_label2.grid(padx=10, sticky="nsew", row=1, column=2)

        self.row_labels = []
        self.old_values_labels = []
        self.new_values_entries = []
        for i, (key, values) in enumerate(self.old_initial_fit_parameter_values.items()):
            self.row_labels.append(tk.Label(self, text=key))
            self.old_values_labels.append(tk.Label(self, text=str(values)))
            self.new_values_entries.append(tk.Entry(self, width=50, justify=tk.RIGHT))
            self.row_labels[i].grid(padx=10, sticky="nsew", row=i+2, column=0)
            self.old_values_labels[i].grid(padx=10, sticky="nsew", row=i+2, column=1)
            self.new_values_entries[i].insert(0, self.old_values_labels[i]["text"])
            self.new_values_entries[i].grid(sticky="nsew", row=i+2, column=2)

        self.add_up_and_down_key_bindings_to_entries()

        return None

    def handle_up_key_press(self, event, index):
        self.new_values_entries[index-1].focus()
        self.new_values_entries[index-1].icursor(tk.END)
        return None

    def handle_down_key_press(self, event, index):
        self.new_values_entries[index+1].focus()
        self.new_values_entries[index+1].icursor(tk.END)
        return None

    def traverse_list(self, data_item):
        if isinstance(data_item, list):
            for value in data_item:
                for subvalue in self.traverse_list(value):
                    yield subvalue
        else:
            yield data_item

    def entries_contain_number_strings_only(self):
        self.new_initial_fit_parameter_values = {}

        for i, label in enumerate(self.row_labels):
            try:
                curr_list = ast.literal_eval(self.new_values_entries[i].get())
            except (ValueError, SyntaxError):
                self.new_initial_fit_parameter_values = "invalid"
                break

            curr_list_contains_non_numeric_string = False

            # if there are nested lists in entries, break
            if (len(np.array(curr_list).shape) != 1):
                self.new_initial_fit_parameter_values = "invalid"
                break
            for nr_string in self.traverse_list(curr_list):
                if not self.string_is_number(str(nr_string)):
                    curr_list_contains_non_numeric_string = True
            if not curr_list_contains_non_numeric_string:
                self.new_initial_fit_parameter_values[label["text"]] = curr_list
            else:
                # if the parsing of one user entered values fails, i do not want to use any of them!
                self.new_initial_fit_parameter_values = "invalid"
                break

        return self.new_initial_fit_parameter_values

    def string_is_number(self, some_string):
        try:
            if some_string.lower() in ("nan", "-nan", "-inf", "inf"):
                return False
            float(some_string.lstrip("0"))      # lstrip("0") removes leading "0"s. i think at some point python uses octal numeral system (base 8) (if i did not remove leading "0"s)
            return True
        except ValueError:
            return False

    def assign_new_values_if_correct_format(self):
        self.new_initial_fit_parameter_values = self.entries_contain_number_strings_only()

        if self.new_initial_fit_parameter_values == "invalid":
            tk.messagebox.showwarning(title="Warning: parsing error.", message=f"Either your entered values could not be successfully parsed to floats,\n"+
                                                                                "or there is some other ploblem with your entered lists! Check them again.")

            return None

        # write user entered values to file, then assign them to parent object
        with open(file=self.file_name, mode="w") as file:
            file.write(str(self.new_initial_fit_parameter_values))

        self.assign_handler(self.new_initial_fit_parameter_values)

        self.ignore_and_quit()

    def ignore_and_quit(self):
        self.destroy()
