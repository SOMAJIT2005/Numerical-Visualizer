import matplotlib
matplotlib.use('TkAgg')
import tkinter as tk
from tkinter import ttk
from config import COLORS
from home_tab import HomeTab
from root_tab import RootFindingTab
from matrix_tab import LinearSystemsTab

class NumericalSuite(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Numerical Suite — Dashboard Edition')
        self.geometry('1440x900')
        self.configure(bg=COLORS.bg)
        
        style = ttk.Style()
        style.theme_use('default')
        style.layout('TNotebook.Tab', [])
        style.configure('TNotebook', background=COLORS.bg, borderwidth=0)
        style.configure("Treeview", background=COLORS.card, foreground=COLORS.text_primary, fieldbackground=COLORS.card, borderwidth=0)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.home_tab = HomeTab(self.notebook, self.notebook)
        self.root_tab = RootFindingTab(self.notebook, lambda: self.notebook.select(0))
        self.matrix_tab = LinearSystemsTab(self.notebook, lambda: self.notebook.select(0))

        self.notebook.add(self.home_tab)
        self.notebook.add(self.root_tab)
        self.notebook.add(self.matrix_tab)
        self.bind('<Key>', self._route_keypress)

    # ── FIXED KEY ROUTING ──
    def _route_keypress(self, event):
        idx = self.notebook.index("current")
        if idx == 1: 
            self.root_tab.handle_keypress(event)
        elif idx == 2: 
            self.matrix_tab.handle_keypress(event)

if __name__ == '__main__':
    NumericalSuite().mainloop()