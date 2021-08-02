import tkinter as tk

from SupportClasses import ToolTip

class new_decay_times_Window(tk.Toplevel):
    def __init__(self, parent, fit_results, components_list, indeces_for_DAS_matrix, tab_idx, assign_method, decay_times_used=None):
        super().__init__(parent)
        self.parent = parent
        self.fit_results = fit_results
        self.decay_times_used = decay_times_used
        self.components_list = components_list
        self.indeces_for_DAS_matrix = indeces_for_DAS_matrix
        self.nr_of_components = len(components_list)
        self.tab_idx = tab_idx

        self.assign_method = assign_method

        self.title('adjust decay times for DAS of SVDGF tab: ' + str(self.tab_idx + 1) )

        self.extract_resulting_fit_decay_constants()

        self.display_labels_with_fit_result_decay_constants()

        self.display_labels_and_entries_with_decay_constants_to_be_used()

        self.btn_apply_new_decay_times = tk.Button(self, text="use entered decay times!", command=lambda: self.assign_entered_decay_times())
        self.btn_apply_new_decay_times.grid(padx=10, pady=10, sticky="sw", column=0)

        self.btn_ignore_and_quit = tk.Button(self, text="Hit Enter: Ignore and quit", command=lambda: self.ignore_and_quit())
        ttp_btn_ignore_and_quit = ToolTip.CreateToolTip(self.btn_ignore_and_quit, \
        'Quit this window and use the last saved decay times for the DAS decays. '
        'That means that if you have changed the decay times for this tab\\data object already, they will be used. '
        'If you want to use the original fit result decay times, you need to copy them into the entries.')
        self.btn_ignore_and_quit.grid(padx=10, pady=10, sticky="se", column=3, row=self.btn_apply_new_decay_times.grid_info()["row"])

        self.grab_set()         # to keep the window in front of application until it gets closed
        self.focus_set()
        self.bind("<Return>", lambda x: self.ignore_and_quit())

        return None


    def extract_resulting_fit_decay_constants(self):
        self.decay_constants_from_fit = ['{:,.2f}'.format(self.fit_results['tau_component%i' % (j)].value) for j in self.components_list]

        return None

    def display_labels_with_fit_result_decay_constants(self):
        labels = [tk.Label(self, text="fit results:")]
        for i in range(self.nr_of_components):
            labels.append(tk.Label(self, text=f"component {self.components_list[i]}: decay time: {self.decay_constants_from_fit[i]}"))

        for i in range(len(labels)):
            labels[i].grid(padx=10, sticky="nsew")

        return None

    def display_labels_and_entries_with_decay_constants_to_be_used(self):
        to_be_used_label = tk.Label(self, text="user chosen decay times:")
        to_be_used_label.grid(column=1, row=0, padx=10, sticky="nsew")
        new_decay_times_labels = []
        self.new_decay_times_entries = []
        for i in range(self.nr_of_components):
            new_decay_times_labels.append(tk.Label(self, text=f"DAS {self.components_list[i]}: new decay time:"))
            self.new_decay_times_entries.append(tk.Entry(self, width=10))


        for i in range(self.nr_of_components):
            new_decay_times_labels[i].grid(column=1, row=i+1, padx=10, sticky="nsew")
            if self.decay_times_used is not None:
                # user has already changed the decay times to be used at least once!
                self.new_decay_times_entries[i].insert(0, self.decay_times_used[i])
            else:
                self.new_decay_times_entries[i].insert(0, self.decay_constants_from_fit[i])
            self.new_decay_times_entries[i].grid(column=2, row=i+1, padx=10, sticky="nsew")

        return None

    def ignore_and_quit(self):
        self.assign_method(None)
        self.destroy()

    def assign_entered_decay_times(self):
        # get the decay times from entries
        self.new_decay_times = self.get_new_decay_times_from_entries()

        # now assign the decay times in main class
        self.assign_method(self.new_decay_times)

        self.destroy()

    def get_new_decay_times_from_entries(self):
        self.new_decay_times = []
        for i in range(len(self.new_decay_times_entries)):
            if self.string_is_number(self.new_decay_times_entries[i].get().replace(',', '')):
                self.new_decay_times.append(self.new_decay_times_entries[i].get().replace(',', ''))
            else:
                # if the parsing of one user entered decay time fails, i do not want to use any of them!
                self.new_decay_times = "invalid"
                break

        # print(f'after extraction: {self.new_decay_times=}')
        return self.new_decay_times

    def string_is_number(self, some_string):
        try:
            if some_string.lower() == "nan":
                return False
            float(some_string)
            return True
        except ValueError:
            return False
