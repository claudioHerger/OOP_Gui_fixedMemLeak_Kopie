import os
import gc

import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure

# OO backend (Tkinter) tkagg() function:
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import tkinter as tk
import tkinter.ttk as ttk

from SupportClasses import ToolTip


class Kinetics_Spectrum_Window(tk.Toplevel):
    def __init__(self, parent, tab_index, data_dict):
        """a class to make a toplevel with two plots on it. \n
        The plots can be used to inspect the kinetics of a certain wavelength / the spectrum at a certain time delay of a TA data matrix.\n

        Args:
            parent (GUIApp): parent is the Gui App that creates the instance of this class.
            tab_index (int): used in title of Toplevel, so that one knows to which tab this toplevel belongs.
            data_dict (dict): contains identifier string 'type' to differentiate between fitted data and non-fitted data, and all necessary data from data_obj to which to be inspected data matrix belongs.

        Returns:
            None
        """
        super().__init__(parent)

        self.parent = parent
        self.data_dict = data_dict
        self.full_path_to_final_dir = self.data_dict["save_dir"]

        self.geometry(f'{1200}x{470}+{100}+{100}')

        self.frm_inspection_figure = tk.Frame(self)
        self.frm_inspection_figure.columnconfigure(0, weight=1)
        self.frm_inspection_figure.rowconfigure(0, weight=1)
        self.frm_inspection_figure.grid(row=0, columnspan=2)

        self.filename = os.path.basename(self.data_dict["data_file"])
        if self.data_dict["type"] == "original data":
            self.title_start = 'Wavelength kinetics and spectra at times for original data tab: '
        else:
            self.title_start = 'Wavelength kinetics and spectra at times for difference matrix tab: '
        self.title(self.title_start + str(tab_index + 1) + " - data file: "+ self.filename)

        self.btn_close = tk.Button(self, text='Close', fg=self.parent.violet, command=self.destroy_self)
        self.ttp_btn_close = ToolTip.CreateToolTip(self.btn_close, \
        'This might destroy the universe! ')
        self.btn_close.grid(padx=3, pady=5, sticky="se", column=1, row=2)

        self.btn_save_current_figures = tk.Button(self, text='save current figures', fg=self.parent.violet, command=self.save_current_figures_to_file)
        self.ttp_btn_save_current_figures = ToolTip.CreateToolTip(self.btn_save_current_figures, \
        'This saves the current figures to the same file as saving the data of the SVDGF / SVD tab buttons does. ')
        self.btn_save_current_figures.grid(padx=3, pady=5, sticky="sw", column=0, row=2)

        # some styling for plots
        matplotlib.style.use("seaborn")
        matplotlib.rcParams.update({'axes.labelsize': 12.0, 'axes.titlesize': 14.0, 'xtick.labelsize':10, 'ytick.labelsize':12.0, "axes.edgecolor":"black", "axes.linewidth":1})
        self.cmap = matplotlib.cm.get_cmap('rainbow')

        self.get_data()
        self.set_wavelength_kinetics(0)
        self.set_spectrum_at_time_delay(0)
        self.make_wavelength_kinetics_plot()
        self.make_spectrum_at_time_delay_plot()

        return None

    def get_data(self):
        self.time_delays = self.data_dict["time_delays"]
        self.wavelengths = self.data_dict["wavelengths"]
        self.data = self.data_dict["data_matrix"]

        if self.data_dict["type"] == "fit_data":
            self.selected_DAS = self.data_dict["DAS_indeces"]

        # unnecessary things to have "correct" linecolors in wavelength_kinetics plot
        self.wavelengths_are_ascending = self.is_ascending(self.wavelengths)

        return None

    def is_ascending(self, arr):
        arr = [float(nr) for nr in arr]
        previous = arr[0]
        for number in arr:
            if number < previous:
                return False
            previous = number

        return True

    def make_wavelength_kinetics_plot(self):
        self.wavelength_kinetics_fig = Figure(figsize=(6,4))

        self.wavelength_kinetics_axes = self.wavelength_kinetics_fig.add_subplot(1,1,1)

        self.num_ticks = 10
        self.label_format = '{:,.3f}'

        # the index of the position of self.yticks
        self.xticks = np.linspace(0, len(self.time_delays) - 1, self.num_ticks, dtype=np.int)
        # the content of labels of these self.yticks
        self.xticklabels = [float(self.time_delays[idx]) for idx in self.xticks]

        self.xticklabels = [self.label_format.format(x) for x in self.xticklabels]

        self.wavelength_kinetics_axes.set_xticks(self.xticks)
        self.wavelength_kinetics_axes.set_xticklabels(self.xticklabels, fontsize=10, rotation=30)

        self.wavelength_kinetics_axes.set_title('wavelength = ' + self.wavelengths[self.nr_of_wavelength] + " [nm]")
        self.wavelength_kinetics_axes.set_xlabel("Time delays [ps]")
        self.wavelength_kinetics_axes.set_ylabel("amplitude")

        # unnecessary things to have "correct" linecolors in wavelength_kinetics plot
        if self.wavelengths_are_ascending:
            self.wavelength_kinetics_axes.plot(self.time_delays, self.wavelength_kinetics, color=self.cmap(0))
        else:
            self.wavelength_kinetics_axes.plot(self.time_delays, self.wavelength_kinetics, color=self.cmap(len(self.wavelengths)))

        self.wavelength_kinetics_fig.tight_layout()

        self.wavelength_kinetics_canvas = FigureCanvasTkAgg(self.wavelength_kinetics_fig, self.frm_inspection_figure)
        self.wavelength_kinetics_canvas.get_tk_widget().grid(row=0, column=0)

        self.make_wavelength_slider()

        return None

    def make_spectrum_at_time_delay_plot(self):
        self.spectrum_at_time_delay_fig = Figure(figsize=(6,4))

        self.spectrum_at_time_delay_axes = self.spectrum_at_time_delay_fig.add_subplot(1,1,1)

        # the index of the position of self.yticks
        self.spectrum_at_time_delay_xticks = np.linspace(0, len(self.wavelengths) - 1, self.num_ticks, dtype=np.int)
        # the content of labels of these self.yticks
        self.spectrum_at_time_delay_xticklabels = [float(self.wavelengths[idx]) for idx in self.spectrum_at_time_delay_xticks]

        self.spectrum_at_time_delay_xticklabels = [self.label_format.format(x) for x in self.spectrum_at_time_delay_xticklabels]

        self.spectrum_at_time_delay_axes.set_xticks(self.spectrum_at_time_delay_xticks)
        self.spectrum_at_time_delay_axes.set_xticklabels(self.spectrum_at_time_delay_xticklabels, fontsize=10, rotation=30)

        self.spectrum_at_time_delay_axes.set_title('time delay = ' + self.time_delays[self.nr_of_time_delay] + " [ps]")
        self.spectrum_at_time_delay_axes.set_xlabel("Wavelengths [nm]")
        self.spectrum_at_time_delay_axes.set_ylabel("amplitude")

        self.spectrum_at_time_delay_axes.plot(self.wavelengths, self.spectrum_at_time_delay, color="cornflowerblue")

        self.spectrum_at_time_delay_fig.tight_layout()

        self.spectrum_at_time_delay_canvas = FigureCanvasTkAgg(self.spectrum_at_time_delay_fig, self.frm_inspection_figure)
        self.spectrum_at_time_delay_canvas.get_tk_widget().grid(row=0, column=3)

        self.make_time_delay_slider()

        return None

    def make_wavelength_slider(self):
        self.current_wavelength_index = tk.IntVar()

        self.slider_wavelengths = ttk.Scale(
            master = self.frm_inspection_figure,
            from_=0,
            to=len(self.wavelengths)-1,
            length=400,
            orient='horizontal',
            variable=self.current_wavelength_index,
            command=lambda x: self.update_wavelength_kinetics_plot()    # need to call it with lambda as otherwise i get an error
        )

        self.slider_wavelengths.grid(row=3, pady=3)

        self.lbl_slider_wavelenths = tk.Label(self.frm_inspection_figure, text="wavelength: ")
        self.lbl_slider_wavelenths.grid(row=3, column=0, sticky="w", pady=3)

        return None

    def make_time_delay_slider(self):
        self.current_time_delay_index = tk.IntVar()

        self.slider_time_delays = ttk.Scale(
            master = self.frm_inspection_figure,
            from_=0,
            to=len(self.time_delays)-1,
            length=400,
            orient='horizontal',
            variable=self.current_time_delay_index,
            command=lambda x: self.update_spectrum_at_time_delay_plot()    # need to call it with lambda as otherwise i get an error
        )

        self.slider_time_delays.grid(row=3, column=3, pady=3)

        self.lbl_slidertime_delays = tk.Label(self.frm_inspection_figure, text="time delay: ")
        self.lbl_slidertime_delays.grid(row=3, column=3, sticky="w", pady=3)

        return None

    def update_spectrum_at_time_delay_plot(self):
        # set new data
        self.nr_of_time_delay = self.current_time_delay_index.get()
        self.set_spectrum_at_time_delay(self.nr_of_time_delay)

        # make new plot
        self.spectrum_at_time_delay_axes.clear()
        self.spectrum_at_time_delay_axes.set_xticks(self.spectrum_at_time_delay_xticks)
        self.spectrum_at_time_delay_axes.set_xticklabels(self.spectrum_at_time_delay_xticklabels, fontsize=10, rotation=30)

        self.spectrum_at_time_delay_axes.set_title('time delay = ' + self.time_delays[self.nr_of_time_delay] + " [ps]")
        self.spectrum_at_time_delay_axes.set_xlabel("Wavelengths [nm]")
        self.spectrum_at_time_delay_axes.set_ylabel("amplitude")

        self.spectrum_at_time_delay_axes.plot(self.wavelengths, self.spectrum_at_time_delay, color="cornflowerblue")

        self.spectrum_at_time_delay_fig.canvas.draw_idle()

        return None

    def update_wavelength_kinetics_plot(self):
        # set new data
        self.nr_of_wavelength = self.current_wavelength_index.get()
        self.set_wavelength_kinetics(self.nr_of_wavelength)

        # make new plot
        self.wavelength_kinetics_axes.clear()
        self.wavelength_kinetics_axes.set_xticks(self.xticks)
        self.wavelength_kinetics_axes.set_xticklabels(self.xticklabels, fontsize=10, rotation=30)
        self.wavelength_kinetics_axes.set_title('wavelength = ' + self.wavelengths[self.nr_of_wavelength]  + " [nm]")
        self.wavelength_kinetics_axes.set_xlabel("Time delays [ps]")
        self.wavelength_kinetics_axes.set_ylabel("amplitude")

        # unnecessary things to have "correct" linecolors in wavelength_kinetics plot
        if self.wavelengths_are_ascending:
            self.wavelength_kinetics_axes.plot(self.time_delays, self.wavelength_kinetics, color=self.cmap(self.nr_of_wavelength/len(self.wavelengths)))
        else:
            self.wavelength_kinetics_axes.plot(self.time_delays, self.wavelength_kinetics, color=self.cmap((len(self.wavelengths) - self.nr_of_wavelength)/len(self.wavelengths)))

        self.wavelength_kinetics_fig.canvas.draw_idle()

        return None

    def set_spectrum_at_time_delay(self, nr_of_time_delay):
        self.nr_of_time_delay = nr_of_time_delay
        self.spectrum_at_time_delay = self.data[:,self.nr_of_time_delay].astype(float)

        return None

    def set_wavelength_kinetics(self, nr_of_wavelength):
        self.nr_of_wavelength = nr_of_wavelength
        self.wavelength_kinetics = self.data[self.nr_of_wavelength,:].astype(float)

        return None

    def save_current_figures_to_file(self):
        print("\nsaving current wavelength kinetics and spectrum at time delay figures to file!")

        # check if directory exists:
        if not os.path.exists(self.full_path_to_final_dir):
            os.makedirs(self.full_path_to_final_dir)

        # save current figures:
        if self.data_dict["type"] == "fit_data":
            self.wavelength_kinetics_fig.savefig(self.full_path_to_final_dir+"/wavelength_"+'{:,.3f}'.format(float(self.wavelengths[self.nr_of_wavelength]))+"[nm]_kinetics_with_selected_DAS"+str(self.selected_DAS)+".png")
            self.spectrum_at_time_delay_fig.savefig(self.full_path_to_final_dir+"/time_delay_"+'{:,.3f}'.format(float(self.time_delays[self.nr_of_time_delay]))+"[ps]_spectra_with_selected_DAS"+str(self.selected_DAS)+".png")

        else:
            self.wavelength_kinetics_fig.savefig(self.full_path_to_final_dir+"/wavelength_"+'{:,.3f}'.format(float(self.wavelengths[self.nr_of_wavelength]))+"[nm]_kinetics.png")
            self.spectrum_at_time_delay_fig.savefig(self.full_path_to_final_dir+"/time_delay_"+'{:,.3f}'.format(float(self.time_delays[self.nr_of_time_delay]))+"[ps]_spectra.png")

        return None

    def destroy_self(self):

        # purely for asthetic reasons when toplevel is closed:
        self.btn_close.grid_remove()
        self.btn_save_current_figures.grid_remove()
        self.frm_inspection_figure.grid_remove()

        self.destroy()
        self.delete_attributes()

        # puts main window to front again if it is not "behind" this toplevel for some reason
        self.parent.parent.lift()

        return None

    def delete_attributes(self):
        attr_lst = list(vars(self))
        attr_lst.remove('parent')
        for attr in attr_lst:
            delattr(self, attr)

        del attr_lst

        gc.collect()

        return None