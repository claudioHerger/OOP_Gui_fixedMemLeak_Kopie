import gc

import numpy as np
import seaborn as sns
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure

# OO backend (Tkinter) tkagg() function:
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from SupportClasses import ToolTip

import tkinter as tk

class SetColorMapWindow(tk.Toplevel):

    def __init__(self, parent, colormaps_dict_file, currently_used_colormaps_dict, assignment_handler) -> None:

        super().__init__(parent)
        self.parent = parent
        self.currently_used_colormaps_dict = currently_used_colormaps_dict
        self.assignement_handler = assignment_handler
        self.colormaps_dict_file = colormaps_dict_file

        self.check_if_cmaps_dict_contains_correct_keys()

        self.cmaps_dict = {"default color map": ["default"]}
        self.cmaps_dict['Perceptually Uniform Sequential'] = [
            'viridis', 'plasma', 'inferno', 'magma', 'cividis']
        self.cmaps_dict['Sequential'] = [
                    'Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',
                    'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu',
                    'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn']
        self.cmaps_dict['Sequential (2)'] = [
            'binary', 'gist_yarg', 'gist_gray', 'gray', 'bone', 'pink',
            'spring', 'summer', 'autumn', 'winter', 'cool', 'Wistia',
            'hot', 'afmhot', 'gist_heat', 'copper']
        self.cmaps_dict['Diverging'] = [
            'PiYG', 'PRGn', 'BrBG', 'PuOr', 'RdGy', 'RdBu',
            'RdYlBu', 'RdYlGn', 'Spectral', 'coolwarm', 'bwr', 'seismic']
        self.cmaps_dict['Qualitative'] = [
            'Pastel1', 'Pastel2', 'Paired', 'Accent',
            'Dark2', 'Set1', 'Set2', 'Set3',
            'tab10', 'tab20', 'tab20b', 'tab20c']
        self.cmaps_dict['Miscellaneous'] = [
            'flag', 'prism', 'ocean', 'gist_earth', 'terrain', 'gist_stern',
            'gnuplot', 'gnuplot2', 'CMRmap', 'cubehelix', 'brg',
            'gist_rainbow', 'rainbow', 'jet', 'turbo', 'nipy_spectral',
            'gist_ncar']

        self.title('Select colormaps to be used for heatmap tabs')

        self.make_widgets()

        return None

    def check_if_cmaps_dict_contains_correct_keys(self):
        self.correct_colormaps_dict_keys = ["ORIG", "SVD", "Fit", "SVD_diff", "Fit_diff"]
        dict_has_wrong_keys = False
        for key in self.currently_used_colormaps_dict.keys():
            if key not in self.correct_colormaps_dict_keys:
                dict_has_wrong_keys = True
                break

        if dict_has_wrong_keys:
            tk.messagebox.showwarning("warning!", "the colormaps dictionary contains wrong keys\nIt will be reset to a default dict.")
            self.currently_used_colormaps_dict = {"ORIG": "", "SVD": "", "Fit": "", "SVD_diff": "", "Fit_diff": ""}

        return None

    def make_widgets(self):
        self.make_scrollable_listbox()
        self.figure, self.axes, self.figure_canvas = self.make_frame_figure_and_axes()
        self.btn_quit = tk.Button(self, text="close", command=self.delete_attrs_and_destroy)

        self.update_axes()

        self.make_selection_btns()
        self.figure_canvas.get_tk_widget().grid(row=0, column=0)
        self.btn_quit.grid(row=99, column=99, sticky="se", pady=3)

        return None

    def update_currently_selected_label_text(self, new_dict):
        lbl_str = ""
        for key, item in new_dict.items():
            lbl_str += key +": " + str(item)+ " "
        self.lbl_current_selection_dict["text"] = lbl_str

    def make_selection_btns(self):
        self.lbl_use_cmap_for_what = tk.Label(self, text="use this colormap for:")
        self.lbl_use_cmap_for_what.grid(row=2, column=0, columnspan=2, )

        self.check_button_variables = [tk.IntVar(0) for _ in self.currently_used_colormaps_dict]
        self.check_buttons = [tk.Checkbutton(self, text=key, onvalue=1, offvalue=0, variable=self.check_button_variables[index]) for index, key in enumerate(self.currently_used_colormaps_dict.keys())]
        for index in range(len(self.currently_used_colormaps_dict)):
            self.check_button_variables[index].set(1)
            self.check_buttons[index].grid(row=2, column=index+2, sticky="sw", pady=3)

        self.btn_apply = tk.Button(self, text="apply", command=self.apply_cmap_selection)
        ttp_btn_apply = ToolTip.CreateToolTip(self.btn_apply, text="from now on any newly created heatmaps (from your selection) will be displayed with this colormap")
        self.btn_apply.grid(row=2, column=self.check_buttons[-1].grid_info()['column']+1)

        self.lbl_current_selection = tk.Label(self, text="currently selected:")
        self.lbl_current_selection_dict = tk.Label(self)
        self.update_currently_selected_label_text(self.currently_used_colormaps_dict)

        self.lbl_current_selection.grid(row=3, column=0, columnspan=2)
        self.lbl_current_selection_dict.grid(row=3, column=2, columnspan=7)

    def make_scrollable_listbox(self):
        self.listbox = tk.Listbox(self, background='white', width=35, selectbackground="cornflowerblue")
        self.listbox_scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.listbox.config(yscrollcommand=self.listbox_scrollbar.set)
        self.listbox_scrollbar.configure(command=self.listbox.yview)

        for cmap_type in self.cmaps_dict:
            self.listbox.insert(tk.END, "---"+cmap_type+"---")
            self.listbox.itemconfig(tk.END, bg="lightgrey", selectbackground="grey")
            for cmap in self.cmaps_dict[cmap_type]:
                self.listbox.insert(tk.END, cmap)

        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        self.listbox.grid(row=0, sticky="w")
        self.listbox_scrollbar.grid(row=0, column=1, sticky="ns")

        self.listbox.select_set(1)

        return None

    def apply_cmap_selection(self):
        for checkbtn, checkbtn_variable in zip(self.check_buttons, self.check_button_variables):
            if checkbtn_variable.get() == 1:
                self.currently_used_colormaps_dict[checkbtn["text"]] = self.listbox.get(self.listbox.curselection()[0])

        self.assignement_handler(self.currently_used_colormaps_dict)

        with open(file=self.colormaps_dict_file, mode="w") as file:
                file.write(str(self.currently_used_colormaps_dict))

        self.update_currently_selected_label_text(self.currently_used_colormaps_dict)

        return None

    def on_select(self, event):
        event_widget = event.widget
        if str(event_widget.get(event_widget.curselection()[0]))[0] == "-":
            self.listbox.itemconfigure(event_widget.curselection()[0], selectbackground="red")
            self.after(400, self.return_listbox_item_selectbackground_to_original_color, self.listbox, event_widget.curselection()[0])
        else:
            self.update_axes(event_widget.get(event_widget.curselection()[0]))

    def return_listbox_item_selectbackground_to_original_color(self, listbox, listbox_item_index):
        listbox.itemconfigure(listbox_item_index, selectbackground="lightgrey")
        listbox.selection_clear(0, tk.END)
        listbox.activate(listbox_item_index+1)
        listbox.select_set(listbox_item_index+1)
        self.update_axes(listbox.get(listbox.curselection()[0]))

    def make_frame_figure_and_axes(self):
        frm_figure = tk.Frame(self)
        frm_figure.grid(row=0, column=2, columnspan=99)

        fig = Figure(figsize=(7,2))
        axes = fig.add_subplot(1,1,1)
        canvas = FigureCanvasTkAgg(fig, frm_figure)

        return fig, axes, canvas

    def update_axes(self, colormap_name="default"):
        self.axes.clear()

        gradient = np.linspace(0, 1, 256)
        gradient = np.vstack((gradient, gradient))

        if colormap_name == "default":
            default_cmap = sns.diverging_palette(220, 20, s=300, as_cmap=True)
            self.axes.imshow(gradient, aspect='auto', cmap=default_cmap)
        else:
            self.axes.imshow(gradient, aspect='auto', cmap=matplotlib.cm.get_cmap(colormap_name))

        self.axes.set_title(colormap_name, fontsize=12)

        self.axes.set_axis_off()

        # actually draw the plot
        self.figure.canvas.draw_idle()

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
