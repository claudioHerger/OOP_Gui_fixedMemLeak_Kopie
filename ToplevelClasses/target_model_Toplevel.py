import tkinter as tk
import os
import ast
import re

from SupportClasses import ToolTip

class target_model_Window(tk.Toplevel):
    def __init__(self, parent, components, file_name):
        """ a toplevel to enter a user definde fit function. It will be parsed, and if successful, can be used
            in fit procedure instead of the general fit function for a given set of components.

        Args:
            parent (tk.Frame): the root window.
            components (list of integers): the currently checked components to be used in fit.
            depending on the number of components, this window will display different entries.
            file_name (str): not sure yet whether any kind of persistence over program end can be achieved, as
            model function needs the same number of components
        """

        super().__init__(parent)
        self.parent = parent
        self.components = components
        self.file_name = file_name

        self.title('Define a fit function.')

        self.lbl_short_how_to = tk.Label(self, text="use \"k1\" as decay constant of component 1, \"t\" for time, \"exp()\" for exponential, only use \"()\" as brackets. get more info =>")
        self.lbl_short_how_to.grid(padx=10, sticky="nsew", row=0, columnspan=3)
        self.btn_display_help_text = tk.Button(self, text="more info", command=self.display_help_window)
        ttp_btn_display_help_text = ToolTip.CreateToolTip(self.btn_display_help_text, text="displays a window with some additional information")
        self.btn_display_help_text.grid(padx=10, pady=10, sticky="w", row=0, column=3)

        self.btn_ignore_and_quit = tk.Button(self, text="Hit Enter: Ignore and quit", command=lambda: self.ignore_and_quit())
        ttp_btn_ignore_and_quit = ToolTip.CreateToolTip(self.btn_ignore_and_quit, \
        'Quit this window and do not change the user defined fit function. ')
        self.btn_ignore_and_quit.grid(padx=10, pady=10, sticky="se", row=99, column=3)

        self.btn_parse_from_entries = tk.Button(self, text="check parsing from entries", command=self.parse_new_summands_from_entries)
        ttp_btn_parse_from_entries = ToolTip.CreateToolTip(self.btn_parse_from_entries, \
        'The program will try to parse what you have entered, and will display a window to show what the '
        'parsed fit function would look like in code.')
        self.btn_parse_from_entries.grid(padx=10, pady=10, sticky="sw", row=99, column=0)
        self.parsed_new_summands_labels = []

        self.get_old_summands_from_file()
        self.display_summand_labels_and_entries()

        self.grab_set()         # to keep the window in front of application until it gets closed
        self.focus_set()
        self.bind("<Return>", lambda x: self.ignore_and_quit())

        return None

    def display_help_window(self):
        helpful_information = """given a set of selected components, there will be a set of right singular vectors (rSV) V_i to fit.
        so for each V_i there will be a fit function f_i.\n
        the default fit function f_i has a set of amplitudes and decay constants as parameters:
        there are #components decay constants, which are global fit parameters, i.e. the same in all fit functions f_i.
        the decay constant of component 3 is denoted in the fit parameters object as \"tau_component3\".
        there are (#rSVs * #components) amplitudes, they are not global fit parameters, so in each f_i different amplitude parameters are used.
        the amplitudes are denoted in the fit parameters object as \"amp_rSV#rSV_component#component\"
        i.e. for the 1st rSV V_1 (=> fit function f_1) and component 2 the amplitude is called amp_1_2.

        as i do not want you to have to write actual code here, i will parse your entries:
        as indicated, \"k1\" will be parsed to the fit parameter for the decay constant of the first component.
        each summand will be multiplied with an amplitude parameter, for more info on that, check how your entries are parsed via button.

        The parsing is not very sophisticated, so if you e.g. miss a bracket, the fit procedure may fail.
        """
        tk.messagebox.showinfo(title="hopefully helpful information window", message=re.sub('^[ \t]*',"",helpful_information, flags=re.MULTILINE), parent=self, default = "ok", )
        return None

    def get_old_summands_from_file(self):
        try:
            with open(self.file_name, mode='r') as dict_file:
                self.old_summands_dict_from_file = ast.literal_eval(dict_file.read().strip())
        except (SyntaxError, FileNotFoundError) as error:
            tk.messagebox.showwarning(title="Warning, problem with target model fit function file!",
                                    message=f"{os.path.basename(self.file_name)} can not be evaluated correctly!\n\n"
                                    +f"error: {error}"
                                    +"\n\nDoes the file even exist..?\n"
                                    +"If it does, it should contain only one python dictionary with strings as values and keys and nothing else!\nMaybe have a look at it..?\n\n"
                                    +"If you enter a fit function that can be successfully parsed, a new file will be written.")
            self.old_summands_dict_from_file = {}

    def display_summand_labels_and_entries(self):
        self.summand_labels = []
        self.parsed_old_summand_labels = []
        self.summand_entries = []
        for i in range(len(self.components)):
            self.summand_labels.append(tk.Label(self, text=f"summand {i}:", justify=tk.RIGHT))
            self.parsed_old_summand_labels.append(tk.Label(self, justify=tk.RIGHT))
            self.summand_entries.append(tk.Entry(self, width=50, justify=tk.RIGHT))
            if f"summand {i}" in self.old_summands_dict_from_file.keys():
                self.parsed_old_summand_labels[i]["text"] = self.old_summands_dict_from_file[f"summand {i}"]
                self.summand_entries[i].insert(0, self.old_summands_dict_from_file[f"summand {i}"])
            else:
                self.summand_entries[i].insert(0, "0")
            self.summand_labels[i].grid(padx=10, sticky="e", row=i+2, column=0)
            self.parsed_old_summand_labels[i].grid(padx=10, sticky="nsew", row=i+2, column=1)
            # some key-binding for user experience.
            if i+1 < len(self.components):
                self.summand_entries[i].bind("<Key-Down>", lambda event, idx=i: self.handle_down_key_press(event, idx))
            if i > 0:
                self.summand_entries[i].bind("<Key-Up>", lambda event, idx=i: self.handle_up_key_press(event, idx))
            self.summand_entries[i].grid(sticky="nsew", row=i+2, column=2)

        return None

    def handle_up_key_press(self, event, index):
        self.summand_entries[index-1].focus()
        self.summand_entries[index-1].icursor(tk.END)
        return None

    def handle_down_key_press(self, event, index):
        self.summand_entries[index+1].focus()
        self.summand_entries[index+1].icursor(tk.END)
        return None

    def parse_new_summands_from_entries(self):
        # disable any new input into entries until user says they are not happy with how it has been parsed:
        for entry in self.summand_entries:
            entry['state'] = 'disabled'

        self.parsed_new_summands_from_entries = {}
        for i in range(len(self.summand_entries)):
            parsed_summand = self.parse_entry(self.summand_entries[i].get())
            self.parsed_new_summands_from_entries[f"summand {i}"] = parsed_summand

        self.display_parsed_new_summands_on_window(self.parsed_new_summands_from_entries)

        return self.parsed_new_summands_from_entries

    def display_parsed_new_summands_on_window(self, parsed_new_summands: dict):
        colors=["navyblue", "darkmagenta"]

        self.lbl_fit_function = tk.Label(self, text="i-th fit function is: ")
        self.lbl_fit_function.grid(row=self.btn_ignore_and_quit.grid_info()["row"]+1, column=0, sticky="ew")

        self.lbl_right_singular_vector_i = tk.Label(self, text="right singular vector i = ")
        self.lbl_right_singular_vector_i.grid(row=self.btn_ignore_and_quit.grid_info()["row"]+2, sticky="e")

        # destroy labels if they exist already
        if len(self.parsed_new_summands_labels) != 0:
            for label in self.parsed_new_summands_labels:
                label.destroy()
        self.parsed_new_summands_labels = []

        nr_of_summands = len(self.components)
        for i, (component, summand) in enumerate(zip(self.components, parsed_new_summands.values())):
            summand_text = f"amp_i_{component} * {summand} "
            if i+1 != nr_of_summands: summand_text = summand_text + "+ "
            self.parsed_new_summands_labels.append(tk.Label(self, text=summand_text, fg=colors[i%2]))
            self.parsed_new_summands_labels[i].grid(column=1, sticky="w", row=self.btn_ignore_and_quit.grid_info()["row"]+i+2, columnspan=4)

        self.display_save_or_rewrite_summands_buttons()

        return None

    def parse_entry(self, entry_text):
        if entry_text == "":
            return "0"
        parsed_time_delays = entry_text.replace("t", "time_delays")
        parsed_decay_constants = parsed_time_delays
        k_list = re.findall(r'k\d+', parsed_time_delays)
        for k_str in k_list:
            parsed_decay_constants = re.sub(r'k\d+', f"taus[component{k_str[1:]}]", parsed_decay_constants, count=1)

        parsed_np_exp = parsed_decay_constants.replace("exp", "np.exp")
        parsed_with_brackets = "(" +parsed_np_exp+ ")"

        return parsed_with_brackets

    def display_save_or_rewrite_summands_buttons(self):
        self.btn_use_parsed_summands = tk.Button(self, text="use these summands", command=self.write_parsed_summands_to_file)
        ttp_btn_use_parsed_summands = ToolTip.CreateToolTip(self.btn_use_parsed_summands, \
        'If you are happy with the parsing of your summands, this will save them to a file.\n'
        'If additionally the checkbox on the right of the \"Define fit function\" Button is checked, '
        'then this fit function will be used for each fit until you uncheck the checkbox. '
        'If the checkbox is unchecked, the general fit function will be used again.')
        self.btn_rewrite_summands = tk.Button(self, text="rewrite summands", command=self.rewrite_summands)
        ttp_btn_rewrite_summands = ToolTip.CreateToolTip(self.btn_rewrite_summands, \
        'If you are NOT happy with the parsing of your summands, this will enable you to rewrite them')
        self.btn_use_parsed_summands.grid(padx=10, pady=10, sticky="sw", column=0)
        self.btn_rewrite_summands.grid(padx=10, pady=10, sticky="se", column=3, row = self.btn_use_parsed_summands.grid_info()["row"])

        self.lbl_warning_because_of_eval = tk.Label(self, text="Warning: your fit function will be evaluated via \"asteval\",\n so if you write in code to e.g. delete all files, this might just get executed!", font=("Helvetica", 14))
        self.lbl_warning_because_of_eval.grid(columnspan=10)

        return None

    def write_parsed_summands_to_file(self):
        self.parent.checkbox_use_target_model["state"] = tk.ACTIVE
        self.parent.checkbox_var_use_target_model.set(1)  # set the checkbox so that the user defined fit function will be used

        for i, entry in enumerate(self.summand_entries):
            self.old_summands_dict_from_file[f"summand {i}"] = str(entry.get())
        with open(self.file_name, mode="w") as file:
            file.write(str(self.old_summands_dict_from_file))

        return None

    def rewrite_summands(self):
        self.btn_use_parsed_summands.destroy()
        self.btn_rewrite_summands.destroy()
        self.lbl_warning_because_of_eval.destroy()

        for entry in self.summand_entries:
            entry["state"] = "normal"

        return None

    def ignore_and_quit(self):
        self.destroy()
