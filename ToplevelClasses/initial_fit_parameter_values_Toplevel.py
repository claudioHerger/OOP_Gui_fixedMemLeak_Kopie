import tkinter as tk
import ast
import os

from SupportClasses import ToolTip

class initial_fit_parameters_Window(tk.Toplevel):
    def __init__(self, parent, file_name, current_values):
        """a toplevel window to see and change the values used as initial values in the SVDGF procedure.
        Whenever these values are changed, the new ones will be used for each fit until the user selects to change them again.
        In order to reuse these selected values once the user quits and restarts the program, the values are written to a file.
        From there they are again read when the user starts the program again.

        Args:
            parent (tk.Frame): the root window.
            file_name (str): file to write new initial fit parameter values in
            current_values (dict): dictionary of currently used initial fit parameter values
        """
        super().__init__(parent)
        self.parent = parent
        self.old_initial_fit_parameter_values = current_values
        self.file_name = file_name

        self.title('Set the initial fit parameter values - used for each fit.')

        self.btn_ignore_and_quit = tk.Button(self, text="Hit Enter: Ignore and quit", command=lambda: self.ignore_and_quit())
        ttp_btn_ignore_and_quit = ToolTip.CreateToolTip(self.btn_ignore_and_quit, \
        'Quit this window and use the last saved fit parameters. ')
        self.btn_ignore_and_quit.grid(padx=10, pady=10, sticky="se", row=3, column=3)

        self.display_fit_parameters_labels_and_entries()

        self.btn_assign_new_fit_parameter_values = tk.Button(self, text="use entered values", command=self.assign_new_values_if_correct_format)
        self.btn_assign_new_fit_parameter_values.grid(padx=10, pady=10, sticky="se", row=3, column=0)

        self.grab_set()         # to keep the window in front of application until it gets closed
        self.focus_set()
        self.bind("<Return>", lambda x: self.ignore_and_quit())

    def display_fit_parameters_labels_and_entries(self):
        self.column_labels = [tk.Label(self, text="old values:"), tk.Label(self, text="new values:")]
        for i in range(len(self.old_initial_fit_parameter_values)):
            self.column_labels[i].grid(padx=10, sticky="nsew", row=0, column=i+1)

        self.row_labels = [tk.Label(self, text="time constants:"), tk.Label(self, text="amplitudes:")]
        for i in range(len(self.old_initial_fit_parameter_values)):
            self.row_labels[i].grid(padx=10, sticky="nsew", row=i+1, column=0)

        self.old_values_labels = [tk.Label(self, text=str(self.old_initial_fit_parameter_values["time_constants"])), tk.Label(self, text=str(self.old_initial_fit_parameter_values["amplitudes"]))]
        for i in range(len(self.old_initial_fit_parameter_values)):
            self.old_values_labels[i].grid(padx=10, sticky="nsew", row=i+1, column=1)

        self.new_values_entries = []
        for i in range(len(self.old_initial_fit_parameter_values)):
            self.new_values_entries.append(tk.Entry(self, width=100, justify=tk.RIGHT))
            self.new_values_entries[i].insert(0, self.old_values_labels[i]["text"])
            self.new_values_entries[i].grid(sticky="nsew", row=i+1, column=2)

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

        for (i, key) in enumerate(self.old_initial_fit_parameter_values.keys()):
            try:
                curr_list = ast.literal_eval(self.new_values_entries[i].get())
            except (ValueError, SyntaxError):
                self.new_initial_fit_parameter_values = "invalid"
                break

            curr_list_contains_non_numeric_string = False
            for nr_string in self.traverse_list(curr_list):
                if not self.string_is_number(str(nr_string)):
                    curr_list_contains_non_numeric_string = True
            if not curr_list_contains_non_numeric_string:
                self.new_initial_fit_parameter_values[key] = curr_list
            else:
                # if the parsing of one user entered values fails, i do not want to use any of them!
                self.new_initial_fit_parameter_values = "invalid"
                break

        return None

    def string_is_number(self, some_string):
        try:
            if some_string.lower() in ("nan", "-nan", "-inf", "inf"):
                return False
            float(some_string.lstrip("0"))      # lstrip("0") removes leading "0"s. i think at some point python uses octal numeral system (base 8) (if i did not remove leading "0"s)
            return True
        except ValueError:
            return False

    def assign_new_values_if_correct_format(self):
        self.entries_contain_number_strings_only()

        if self.new_initial_fit_parameter_values == "invalid":
            tk.messagebox.showwarning(title="Warning: parsing error.", message=f"Your entered values could not be successfully parsed to floats!")

            return None

        # write user entered values to file, then assign them to parent object
        with open(file=self.file_name, mode="w") as file:
            file.write(str(self.new_initial_fit_parameter_values))

        self.parent.initial_fit_parameter_values = self.new_initial_fit_parameter_values

        self.ignore_and_quit()

    def ignore_and_quit(self):
        self.destroy()
