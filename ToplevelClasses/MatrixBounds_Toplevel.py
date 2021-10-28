import tkinter as tk
import gc

from SupportClasses import ToolTip

class MatrixBoundsWindow(tk.Toplevel):
    def __init__(self, parent, time_delays, wavelengths, assign_method):

        super().__init__(parent)
        self.parent = parent
        self.time_delays = time_delays
        self.wavelengths = wavelengths

        self.make_labels_and_entries()
        self.display_labels_and_entries()

        self.btn_assign_these_values = tk.Button(self, text="use these bounds", command=self.check_entered_bounds)
        self.btn_assign_these_values.grid(row=3, column=0)

        self.btn_quit = tk.Button(self, text="Quit", command=self.delete_attrs_and_destroy)
        self.btn_quit.grid(row=3, column=0)


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

    def check_entered_bounds(self):




        # finally
        if values == "valid":

            return values

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