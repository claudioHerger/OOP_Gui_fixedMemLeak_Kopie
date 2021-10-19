import tkinter as tk
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

class SmallToolbar(NavigationToolbar2Tk):
    def __init__(self, canvas, window, *, pack_toolbar=False):
        self.toolitems = (
            ('Home', 'Reset', 'home', 'home'),
            ('Back', 'Back to  previous view', 'back', 'back'),
            ('Forward', 'Forward to next view', 'forward', 'forward'),
            (None, None, None, None),
            ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
            ('Zoom', 'Zoom', 'zoom_to_rect', 'zoom'),
            (None, None, None, None),
            ('Subplots', 'Configure subplots', 'subplots', 'configure_subplots'),
            ('Save', 'Save the figure', 'filesave', 'save_figure'),
            )
        # only display the home and zoom btns
        self.toolitems = [t for t in self.toolitems if t[0] in ('Home', 'Zoom')]
        super().__init__(canvas, window, pack_toolbar=pack_toolbar)


    # override _Button() to re-pack the toolbar button in vertical direction
    def _Button(self, text, image_file, toggle, command):
        b = super()._Button(text, image_file, toggle, command)
        b.pack(side=tk.TOP) # re-pack button in vertical direction
        return b

    # override _Spacer() to create vertical separator
    def _Spacer(self):
        s = tk.Frame(self, width=0, bg="DarkGray", padx=0)
        s.pack(side=tk.TOP, pady=0) # pack in vertical direction
        return s

    # disable showing mouse position in toolbar
    def set_message(self, s):
        pass
