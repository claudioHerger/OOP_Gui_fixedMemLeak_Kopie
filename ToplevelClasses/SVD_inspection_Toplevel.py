import os
import gc

import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure

# OO backend (Tkinter) tkagg() function:
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import tkinter as tk

# own classes
from SupportClasses import ToolTip
from FunctionsUsedByPlotClasses import get_retained_rightSVs_leftSVs_singularvs

class SVD_inspection_Window(tk.Toplevel):
    def __init__(self, parent, tab_index, data_obj):
        """a class to make a toplevel with three plots on it. \n
        The plots can be used to inspect the singular values and vectors of a TA data matrix.\n

        Args:
            parent (GUIApp): parent is the Gui App that creates the instance of this class.
            tab_index (int): used in title of Toplevel, so that one knows to which tab this toplevel belongs.
            data_obj (ORIG data Plot instance): the instance of the data object to which the to be inspected data matrix belongs.

        Returns:
            None
        """
        super().__init__(parent)

        self.parent = parent
        self.data_obj = data_obj
        self.full_path_to_final_dir = self.data_obj.full_path_to_final_dir

        self.geometry(f'{1050}x{720}+{100}+{50}')

        self.frm_sing_values_figure = tk.Frame(self)
        self.frm_sing_values_figure.columnconfigure(0, weight=1)
        self.frm_sing_values_figure.rowconfigure(0, weight=1)
        self.frm_sing_values_figure.grid(row=0, rowspan=2)

        self.frm_rightSVs_figure = tk.Frame(self)
        self.frm_rightSVs_figure.grid(row=0, column=1, columnspan=21)
        self.frm_leftSVs_figure = tk.Frame(self)
        self.frm_leftSVs_figure.grid(row=1, column=1, columnspan=21)

        self.filename = os.path.basename(self.data_obj.filename)
        self.title('Singular values and vectors for ORIG data tab: ' + str(tab_index + 1) + " - data file: "+self.filename)

        self.lbl_nr_of_sing_values = tk.Label(self, text="nr of singular values?", fg=self.parent.violet)
        self.ent_nr_of_sing_values = tk.Entry(self, width=6, fg=self.parent.violet, validate="key", justify=tk.RIGHT, validatecommand=(self.register(self.test_value_digits_only),'%P','%d'))

        self.lbl_nr_of_sing_values.grid(column=0, row=2, sticky='sw', pady=5, padx=3)
        self.ent_nr_of_sing_values.grid(row=self.lbl_nr_of_sing_values.grid_info()["row"], padx=150, pady=5, sticky="sw")
        self.ent_nr_of_sing_values.bind("<Return>", self.update_sing_values_plot)
        self.ent_nr_of_sing_values.insert(0, 10)

        self.max_nr_of_sing_vectors = 11        # set this to a higher number if you want to be able to inspect even less significant singular vectors
        self.max_nr_of_sing_values = 51         # set this to a higher number if you want to be able to inspect even less significant singular values

        # set which singular vectors are to be displayed when initially opening the window
        self.leftSVs_components_list = [0,1,2]
        self.rightSVs_components_list = [0,1,2]

        self.make_checkbuttons()

        self.btn_close = tk.Button(self, text='Close', fg=self.parent.violet, command=self.destroy_self)
        self.btn_close.grid(padx=3, pady=5, sticky="se", column=self.max_nr_of_sing_vectors+1, row=99)

        self.btn_save_current_figures = tk.Button(self, text='save current figures', fg=self.parent.violet, command=self.save_current_figures_to_file)
        self.ttp_btn_save_current_figures = ToolTip.CreateToolTip(self.btn_save_current_figures, \
        'This saves the current figures to the same file as saving the data of the ORIG data tab buttons does. ')
        self.btn_save_current_figures.grid(padx=3, pady=5, sticky="sw", column=0, row=99)

        # some styling for plots
        matplotlib.style.use("default")
        matplotlib.rcParams.update({'axes.labelsize': 12.0, 'axes.titlesize': 14.0, 'xtick.labelsize':10, 'ytick.labelsize':12.0, "axes.edgecolor":"black", "axes.linewidth":1, "axes.grid":True, "grid.linestyle":"--"})

        self.get_data()
        self.make_all_figures_and_axes()

        self.update_sing_values_plot(event=None)

        self.update_leftSVs_plot()
        self.update_rightSVs_plot()

        return None

    def make_checkbuttons(self):
        self.leftSVs_checkbutton_vars = [tk.IntVar() for _ in range(self.max_nr_of_sing_vectors)]
        self.rightSVs_checkbutton_vars = [tk.IntVar() for _ in range(self.max_nr_of_sing_vectors)]

        for i in range(self.max_nr_of_sing_vectors):
            if i in self.leftSVs_components_list:
                self.leftSVs_checkbutton_vars[i].set(1)
                self.rightSVs_checkbutton_vars[i].set(1)
            else:
                self.leftSVs_checkbutton_vars[i].set(0)
                self.rightSVs_checkbutton_vars[i].set(0)

        self.leftSVs_checkbuttons = [tk.Checkbutton(self, text=checkbox, variable=self.leftSVs_checkbutton_vars[checkbox], onvalue=1, offvalue=0) for checkbox in range(self.max_nr_of_sing_vectors)]
        self.rightSVs_checkbuttons = [tk.Checkbutton(self, text=checkbox, variable=self.rightSVs_checkbutton_vars[checkbox], onvalue=1, offvalue=0) for checkbox in range(self.max_nr_of_sing_vectors)]

        for checkbox in range(self.max_nr_of_sing_vectors):
            self.rightSVs_checkbuttons[checkbox].grid(row=2, column=checkbox+1)
            self.leftSVs_checkbuttons[checkbox].grid(row=3, column=checkbox+1)

        self.btn_update_rightSVs_plot = tk.Button(self, text='update rightSVs plot', fg=self.parent.violet, command=self.update_rightSVs_components_list)
        self.btn_update_rightSVs_plot.grid(padx=3, pady=5, sticky="se", column=self.rightSVs_checkbuttons[-1].grid_info()["column"]+1, row=2)

        self.btn_update_leftSVs_plot = tk.Button(self, text='update leftSVs plot', fg=self.parent.violet, command=self.update_leftSVs_components_list)
        self.btn_update_leftSVs_plot.grid(padx=3, pady=5, sticky="se", column=self.leftSVs_checkbuttons[-1].grid_info()["column"]+1, row=3)

        return None

    def get_data(self):
        self.data = self.data_obj.data_matrix
        self.time_delays = self.data_obj.time_delays
        self.wavelengths = self.data_obj.wavelengths

        self.rightSVs, self.leftSVs, self.singValues = get_retained_rightSVs_leftSVs_singularvs.run(self.data, [i for i in range(self.max_nr_of_sing_values)])

        self.leftSVs_scaled = np.zeros((len(self.wavelengths), self.max_nr_of_sing_vectors))
        self.rightSVs_scaled = np.zeros((self.max_nr_of_sing_vectors, len(self.time_delays)))
        for i in range(self.max_nr_of_sing_vectors):
            sing_value = self.singValues[i]
            self.leftSVs_scaled[:, i] = sing_value*self.leftSVs[:, i]
            self.rightSVs_scaled[i, :] = sing_value*self.rightSVs[i, :]

        return None

    def test_value_digits_only(self, inStr, acttyp):
        if acttyp == '1': #insert
            if not inStr.isdigit():
                return False
        return True

    def make_all_figures_and_axes(self):
        self.sing_values_fig = Figure(figsize=(5,6))
        self.sing_values_axes = self.sing_values_fig.add_subplot(1,1,1)
        self.sing_values_canvas = FigureCanvasTkAgg(self.sing_values_fig, self.frm_sing_values_figure)
        self.sing_values_canvas.get_tk_widget().grid(row=0, column=0)

        self.rightSVs_fig = Figure(figsize=(5,3))
        self.rightSVs_axes = self.rightSVs_fig.add_subplot(1,1,1)
        self.rightSVs_canvas = FigureCanvasTkAgg(self.rightSVs_fig, self.frm_rightSVs_figure)
        self.rightSVs_canvas.get_tk_widget().grid(row=0, column=0)

        self.leftSVs_fig = Figure(figsize=(5,3))
        self.leftSVs_axes = self.leftSVs_fig.add_subplot(1,1,1)
        self.leftSVs_canvas = FigureCanvasTkAgg(self.leftSVs_fig, self.frm_leftSVs_figure)
        self.leftSVs_canvas.get_tk_widget().grid(row=0, column=0)
        self.leftSVs_fig.canvas.draw_idle()

        return None

    def update_leftSVs_components_list(self):
        self.leftSVs_components_list = []
        for i in range(len(self.leftSVs_checkbutton_vars)):
            if self.leftSVs_checkbutton_vars[i].get() == 1:
                self.leftSVs_components_list.append(i)

        self.update_leftSVs_plot()

    def update_rightSVs_components_list(self):
        self.rightSVs_components_list = []
        for i in range(len(self.rightSVs_checkbutton_vars)):
            if self.rightSVs_checkbutton_vars[i].get() == 1:
                self.rightSVs_components_list.append(i)

        self.update_rightSVs_plot()

    def update_leftSVs_plot(self):
        self.leftSVs_axes.clear()

        self.leftSVs_xaxis = self.wavelengths

        self.leftSVs_num_ticks = 5
        self.leftSVs_label_format = '{:.1f}'
        self.leftSVs_xticks = np.linspace(0, len(self.leftSVs_xaxis) - 1, self.leftSVs_num_ticks, dtype=np.int)
        self.leftSVs_xticklabels = [float(self.leftSVs_xaxis[idx]) for idx in self.leftSVs_xticks]
        self.leftSVs_xticklabels = [self.leftSVs_label_format.format(x) for x in self.leftSVs_xticklabels]

        for i in range(len(self.leftSVs_components_list)):
            self.leftSVs_axes.plot(self.leftSVs_xaxis, self.leftSVs_scaled[:,self.leftSVs_components_list[i]], label=f'comp: {self.leftSVs_components_list[i]}')

        self.leftSVs_axes.set_xticks(self.leftSVs_xticks)
        self.leftSVs_axes.set_xticklabels(self.leftSVs_xticklabels, rotation=0)
        self.leftSVs_axes.set_title("left singular vectors * singular value")
        self.leftSVs_axes.set_xlabel("wavelengths")
        self.leftSVs_axes.set_ylabel("amplitude a.u.")
        self.leftSVs_axes.legend(fontsize=8)

        self.leftSVs_fig.tight_layout()

        # actually draw the plot
        self.leftSVs_fig.canvas.draw_idle()

    def update_rightSVs_plot(self):
        self.rightSVs_axes.clear()

        self.rightSVs_xaxis = self.time_delays

        self.rightSVs_num_ticks = 5
        self.rightSVs_label_format = '{:.1f}'
        self.rightSVs_xticks = np.linspace(0, len(self.rightSVs_xaxis) - 1, self.rightSVs_num_ticks, dtype=np.int)
        self.rightSVs_xticklabels = [float(self.rightSVs_xaxis[idx]) for idx in self.rightSVs_xticks]
        self.rightSVs_xticklabels = [self.rightSVs_label_format.format(x) for x in self.rightSVs_xticklabels]

        for i in range(len(self.rightSVs_components_list)):
            self.rightSVs_axes.plot(self.rightSVs_xaxis, self.rightSVs_scaled[self.rightSVs_components_list[i],:], label=f'comp: {self.rightSVs_components_list[i]}')

        self.rightSVs_axes.set_xticks(self.rightSVs_xticks)
        self.rightSVs_axes.set_xticklabels(self.rightSVs_xticklabels, rotation=0)
        self.rightSVs_axes.set_title("right singular vectors * singular value")
        self.rightSVs_axes.set_xlabel("time delay")
        self.rightSVs_axes.set_ylabel("amplitude a.u.")
        self.rightSVs_axes.legend(fontsize=8)

        self.rightSVs_fig.tight_layout()

        # actually draw the plot
        self.rightSVs_fig.canvas.draw_idle()

    def update_sing_values_plot(self, event=None):
        """ event = None is needed because used as callback"""
        nr_of_singular_values_to_plot = int(self.ent_nr_of_sing_values.get())

        # check if user wants to plot more singular values than are stored or if they want to plot 0 singular values
        if (nr_of_singular_values_to_plot <= 0 or nr_of_singular_values_to_plot >= self.max_nr_of_sing_values):
            tk.messagebox.showerror("Warning, ", f"please enter a number larger than 0 and lower than {self.max_nr_of_sing_values}.")
            self.lift()
            return None

        self.sing_values_axes.clear()

        self.num_xticks = nr_of_singular_values_to_plot if (nr_of_singular_values_to_plot<10) else 10
        self.sing_values_xaxis = [i for i in range(nr_of_singular_values_to_plot)]
        self.sing_values_xticks = np.linspace(0, nr_of_singular_values_to_plot-1, self.num_xticks, dtype=np.int)


        self.sing_values_axes.plot(self.sing_values_xaxis, self.singValues[:nr_of_singular_values_to_plot], marker="o", linewidth=0, markersize=10)

        self.sing_values_axes.set_yscale("log")
        self.sing_values_axes.set_ylabel("log(singular value)")
        self.sing_values_axes.set_xlabel("singular value index")
        self.sing_values_axes.set_xticks(self.sing_values_xticks)
        self.sing_values_axes.set_title("singular values")

        if nr_of_singular_values_to_plot <= 12:
            label_format = '{:,.2f}'
            value_labels = [label_format.format(x) for x in self.singValues[:nr_of_singular_values_to_plot]]
            text_str = "values: "+ str(value_labels[0])
            for label in value_labels[1:]:
                text_str += "\n"+" "*10 + str(label)
            self.sing_values_axes.text(0.8,0.6,text_str, fontsize=12, horizontalalignment='center', verticalalignment='center', transform=self.sing_values_axes.transAxes, bbox={"facecolor": "cornflowerblue", "alpha":0.5, "pad": 4})

        self.sing_values_fig.tight_layout()

        # actually draw the plot
        self.sing_values_fig.canvas.draw_idle()

        return None

    def save_current_figures_to_file(self):
        print("saving current singular values and vectors figures to file!")

        # check if directory exists:
        if not os.path.exists(self.full_path_to_final_dir):
            os.makedirs(self.full_path_to_final_dir)

        # save current figures:
        self.sing_values_fig.savefig(self.full_path_to_final_dir+"/singular_values_"+str(self.ent_nr_of_sing_values.get())+".png")
        self.leftSVs_fig.savefig(self.full_path_to_final_dir+"/leftSVs_"+str(self.leftSVs_components_list)+".png")
        self.rightSVs_fig.savefig(self.full_path_to_final_dir+"/rightSVs_"+str(self.rightSVs_components_list)+".png")

        return None

    def destroy_self(self):

        # purely for asthetic reasons when toplevel is closed:
        self.btn_close.grid_remove()
        self.btn_save_current_figures.grid_remove()
        self.frm_sing_values_figure.grid_remove()
        self.frm_leftSVs_figure.grid_remove()
        self.frm_rightSVs_figure.grid_remove()
        self.ent_nr_of_sing_values.grid_remove()
        self.lbl_nr_of_sing_values.grid_remove()

        for checkbox in range(self.max_nr_of_sing_vectors):
            self.leftSVs_checkbuttons[checkbox].grid_remove()
            self.rightSVs_checkbuttons[checkbox].grid_remove()

        self.destroy()
        self.delete_attributes()

        # puts main window to front again if it is not "behind" this toplevel for some reason
        # self.parent.parent.lift()

        return None

    def delete_attributes(self):
        attr_lst = list(vars(self))
        attr_lst.remove('parent')
        attr_lst.remove('data_obj')
        for attr in attr_lst:
            delattr(self, attr)

        del attr_lst

        gc.collect()

        return None