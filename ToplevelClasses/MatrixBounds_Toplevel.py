import tkinter as tk
import gc

from SupportClasses import ToolTip
from FunctionsUsedByPlotClasses import get_closest_nr_from_array_like

class MatrixBoundsWindow(tk.Toplevel):
    def __init__(self, parent, time_delays, wavelengths, assign_method):
        """Toplevel to set new bounds for the data matrix corresponding to currently used data file.

        Args:
            parent (tk.Frame): the root window.
            time_delays (arraylike): arralike of time_delays from currently used data file matrix
            wavelengths (arraylike): arralike of wavelengths from currently used data file matrix
            assign_method (method): handles the assignment of new bounds dict in parent
        """
        super().__init__(parent)
        self.parent = parent
        self.time_delays = time_delays
        self.wavelengths = wavelengths
        self.assign_method = assign_method

        self.bounds_dict = {}

        self.make_labels_and_entries()
        self.display_labels_and_entries()

        self.btn_assign_these_values = tk.Button(self, text="use these bounds", command=self.check_and_possibly_assign_values)
        ttp_btn_assign_these_values = ToolTip.CreateToolTip(self.btn_assign_these_values, text="evaluates values and assigns them if valid", optional_y_direction_bump=-20)
        self.btn_assign_these_values.grid(row=3, column=0, sticky="sw", padx=2, pady=3)

        self.btn_quit = tk.Button(self, text="Cancel", command=self.delete_attrs_and_destroy)
        self.btn_quit.grid(row=3, column=4, sticky="se", padx=2, pady=3)

        self.geometry(f'{450}x{100}+{770}+{70}')

    def make_labels_and_entries(self):
        self.wavelength_labels = [tk.Label(self, text="min wavelength"), tk.Label(self, text="max wavelength")]
        self.time_delay_labels = [tk.Label(self, text="min time delay"), tk.Label(self, text="max time delay")]

        self.wavelength_entries = [tk.Entry(self, width=15, justify=tk.RIGHT), tk.Entry(self, width=15, justify=tk.RIGHT)]
        self.time_delay_entries = [tk.Entry(self, width=15, justify=tk.RIGHT), tk.Entry(self, width=15, justify=tk.RIGHT)]

        self.wavelength_entries[0].insert(tk.END, str(self.wavelengths[0]))
        self.wavelength_entries[-1].insert(tk.END, str(self.wavelengths[-1]))
        self.time_delay_entries[0].insert(tk.END, str(self.time_delays[0]))
        self.time_delay_entries[-1].insert(tk.END, str(self.time_delays[-1]))

        return None

    def display_labels_and_entries(self):
        for w_label, w_entry, t_label, t_entry, index in zip(self.wavelength_labels, self.wavelength_entries, self.time_delay_labels, self.time_delay_entries, range(2)):
            if index == 0:
                w_label.grid(row=1, column=index, padx=5, pady=3)
                w_entry.grid(row=1, column=index+1, padx=5, pady=3)
                t_label.grid(row=2, column=index, padx=5, pady=3)
                t_entry.grid(row=2, column=index+1, padx=5, pady=3)
            else:
                w_label.grid(row=1, column=index+2, padx=5, pady=3)
                w_entry.grid(row=1, column=index+3, padx=5, pady=3)
                t_label.grid(row=2, column=index+2, padx=5, pady=3)
                t_entry.grid(row=2, column=index+3, padx=5, pady=3)

    def check_entered_values(self):

        labels = [self.wavelength_labels[0]["text"], self.wavelength_labels[1]["text"], self.time_delay_labels[0]["text"], self.time_delay_labels[1]["text"]]
        entries = [self.wavelength_entries[0].get(), self.wavelength_entries[1].get(), self.time_delay_entries[0].get(), self.time_delay_entries[1].get()]

        for index, value in enumerate(entries):
            is_valid_number = self.string_is_number(value)
            if not is_valid_number:
                tk.messagebox.showerror("error", f"{labels[index]} got invalid value!")
                return False

        # get the indeces of bounds
        min_wavelength_index = get_closest_nr_from_array_like.get_index(self.wavelengths, float(entries[0]))
        max_wavelength_index = get_closest_nr_from_array_like.get_index(self.wavelengths, float(entries[1]))
        min_time_delay_index = get_closest_nr_from_array_like.get_index(self.time_delays, float(entries[2]))
        max_time_delay_index = get_closest_nr_from_array_like.get_index(self.time_delays, float(entries[3]))

        # # checking if min values are < max values
        if min_wavelength_index >= max_wavelength_index or min_time_delay_index >= max_time_delay_index:
            tk.messagebox.showerror("error", f"min values need to be smaller than max values (at least their corresponding indeces do not comply at the moment)\n"
                                                +"(If you have entered values for min and max that are both larger/less than actual max/min value in time_delays/wavelengths this wont work either!)")
            return False

        self.bounds_dict["min_wavelength_index"] = min_wavelength_index
        self.bounds_dict["max_wavelength_index"] = max_wavelength_index
        self.bounds_dict["min_time_delay_index"] = min_time_delay_index
        self.bounds_dict["max_time_delay_index"] = max_time_delay_index
        return True

    def check_and_possibly_assign_values(self):
        self.are_bounds_valid = self.check_entered_values()
        if self.are_bounds_valid:
            self.assign_bounds(self.bounds_dict)
        else:
            self.lift()
            return None

    def assign_bounds(self, new_bounds_dict):
        start_time_value = self.time_delays[self.bounds_dict["min_time_delay_index"]]
        self.assign_method(new_bounds_dict, start_time_value)
        self.delete_attrs_and_destroy()
        return None

    def string_is_number(self, some_string):
        try:
            if some_string.lower() == "nan" or some_string.lower() == "-nan":
                return False
            float(some_string.lstrip("0"))      # lstrip("0") removes leading "0"s. i think at some point python did use if i did not remove leading "0"s octal numeral system (base 8)
            return True
        except ValueError:
            return False

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