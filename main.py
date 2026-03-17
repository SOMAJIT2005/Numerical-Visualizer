import matplotlib
matplotlib.use('TkAgg')
import tkinter as tk
from tkinter import ttk
from config import COLORS, resource_path
from home_tab import HomeTab
from root_tab import RootFindingTab
from matrix_tab import LinearSystemsTab

import license_manager
from license_gate import LicenseGate


class NumericalSuite(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Numerical Suite — Dashboard Edition')
        self.geometry('1440x900')
        self.configure(bg=COLORS.bg)

        # ── ADD ICON LOGIC ──
        try:
            # This ensures the icon is found inside the bundled EXE
            icon_path = resource_path('app_icon.ico')
            self.iconbitmap(icon_path)
        except Exception as e:
            print(f"Icon not found: {e}")
        # ────────────────────
        
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
        
        is_unlocked, remaining_seconds = license_manager.get_status()

        if not is_unlocked and remaining_seconds <= 0:
            self.withdraw() # Hide the main dashboard
            # Pass deiconify so the dashboard reappears on success
            LicenseGate(self, self.deiconify)
        elif not is_unlocked:
            # Optional: Show a small "Trial" label on the dashboard
            hours_left = int(remaining_seconds // 3600)
            self.title(f"Numerical Suite — {hours_left}h Trial Remaining")

    # ── FIXED KEY ROUTING ──
    def _route_keypress(self, event):
        idx = self.notebook.index("current")
        if idx == 1: 
            self.root_tab.handle_keypress(event)
        elif idx == 2: 
            self.matrix_tab.handle_keypress(event)

if __name__ == '__main__':
    NumericalSuite().mainloop()