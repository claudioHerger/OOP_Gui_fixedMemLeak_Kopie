import tkinter as tk
import tkinter.scrolledtext as scrolledtext
import os

class FitResult_Window(tk.Toplevel):
    def __init__(self, parent, tab_index, fit_report, filename):
        super().__init__(parent)
        self.parent = parent
        self.mapped = True
        self.geometry(f'900x400')

        self.filename = os.path.basename(filename)
        self.title('SVDGF fit results for tab: ' + str(tab_index + 1) + " - file: "+self.filename)

        self.scrtxt = scrolledtext.ScrolledText(self, undo=True, height=20, width=100)
        self.scrtxt.grid(sticky='', pady=5, padx=3)
        self.scrtxt.insert(tk.END, fit_report)

        self.btn_close = tk.Button(self, text='Close', fg=self.parent.violet, command=self.destroy_and_give_focus_to_other_toplevel)
        self.btn_close.grid(padx=3, pady=5, sticky="se")

        self.btn_close_all = tk.Button(self, text='Close all', fg=self.parent.violet, command=self.destroy_all)
        self.btn_close_all.grid(padx=3, pady=5, sticky="sw", row=self.btn_close.grid_info()["row"])

        return None

    def destroy_all(self):
        for toplevel in self.parent.fit_report_toplevels:
            toplevel.destroy()
        self.parent.fit_report_toplevels = []
        self.parent.focus_set()

        return None

    def destroy_and_give_focus_to_other_toplevel(self):
        self.destroy()
        self.mapped = False
        self.parent.fit_report_toplevels.remove(self)

        # keep other still existing toplevels in focus
        if self.parent.fit_report_toplevels != []:
            for toplevel in self.parent.fit_report_toplevels:
                if toplevel.mapped:
                    toplevel.lift()

        return None
