import tkinter as tk
import tkinter.ttk as ttk

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)

class NotebookContainer():
    """a class to contain all the notebook frames, figures, FigureCanvasTkAgg and data_objects as needed\n
    to display a type of plot in the TA analysis GUI
    """

    def __init__(self, parent, parent_frame, max_nr_of_tabs, figsize=(10,5), dpi=50):
        """initialize the notebook and all the frames, figures and canvases needed.
        Also initalizes a list for the data objects as None Types.

        Args:
            parent (GuiAppTAAnalysis): the gui app. to have access to file vars etc.
            parent_frame (tk.Frame): the frame on which the notebook will be displayed.
            max_nr_of_tabs (int): the maximum number of tabs this notebook shall have.
            figsize (2tuple(width, height)): a two-tuple defining the width and height of figures to be made. Default = (10,5).
            dpi (int): and integer defining \"dots per inches\", somewhat the resolution of the figures. Default = 50. Must not be 0!
        """
        self.parent = parent
        self.parent_frame = parent_frame
        self.nr_of_tabs = max_nr_of_tabs
        self.figsize = figsize
        self.dpi = dpi

        self.make_notebook()

    def make_notebook(self):
        self.tab_control = ttk.Notebook(self.parent_frame)

        self.figure_frames = [tk.Frame(bg="lavender") for _ in range(self.nr_of_tabs)]

        for i in range(self.nr_of_tabs):
            self.figure_frames[i].columnconfigure(0, weight=1)
            self.figure_frames[i].rowconfigure(0, weight=1)

        # figures to put on canvases. The axes with data are created and cleared in plot class.
        self.figs = [Figure(figsize=self.figsize, dpi=self.dpi) for _ in range(self.nr_of_tabs)]

        self.canvases = [FigureCanvasTkAgg(self.figs[i], self.figure_frames[i]) for i in range(self.nr_of_tabs)]

        # initialize list with None types.
        # To be filled with actual data objects, e.g. SVD_reconstruction.SVD_Heatmap once these objects are instantiated in GUI.
        self.data_objs = [None for _ in range(self.nr_of_tabs)]

        return None

    def add_indexed_tab(self, tab_idx, title=""):
        """adds a new tab to the notebook, inserts it at the position as given by tab_idx, and gives focus to that tab.

        Args:
            tab_idx (int): the position of the new tab in the notebook.
            title (String): String to be added to tab text. Default is empty String.
        """
        # you should NOT change the text string of these tabs!
        # the method get_next_tab_index depends on its layout!!
        self.tab_control.add(self.figure_frames[tab_idx], text=f'{tab_idx+1}: ' + title)

        self.tab_control.insert(tab_idx, self.figure_frames[tab_idx])
        self.tab_control.select(tab_idx)

        return None