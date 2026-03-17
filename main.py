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

        try:
            icon_path = resource_path('app_icon.ico')
            self.iconbitmap(icon_path)
        except Exception as e:
            pass
        
        self.style = ttk.Style()
        
        is_unlocked, remaining_seconds = license_manager.get_status()

        if not is_unlocked and remaining_seconds <= 0:
            self.withdraw() 
            LicenseGate(self, self.deiconify)
        elif not is_unlocked:
            hours_left = int(remaining_seconds // 3600)
            self.title(f"Numerical Suite — {hours_left}h Trial Remaining")

        # Start the UI Builder
        self._build_ui()

    def _build_ui(self):
        self.configure(bg=COLORS.bg)
        self.style.theme_use('default')
        self.style.layout('TNotebook.Tab', [])
        self.style.configure('TNotebook', background=COLORS.bg, borderwidth=0)
        self.style.configure("Treeview", background=COLORS.card, foreground=COLORS.text_primary, fieldbackground=COLORS.card, borderwidth=0)

        # ── THE WIPE: Destroy everything if we are switching themes ──
        if hasattr(self, 'notebook'):
            self.notebook.destroy()
        if hasattr(self, 'theme_btn'):
            self.theme_btn.destroy()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.home_tab = HomeTab(self.notebook, self.notebook)
        self.root_tab = RootFindingTab(self.notebook, lambda: self.notebook.select(0))
        self.matrix_tab = LinearSystemsTab(self.notebook, lambda: self.notebook.select(0))

        self.notebook.add(self.home_tab)
        self.notebook.add(self.root_tab)
        self.notebook.add(self.matrix_tab)
        self.bind('<Key>', self._route_keypress)
        
        # ── THE TOGGLE BUTTON ──
        btn_text = "☀ Light Mode" if COLORS.mode == 'dark' else "🌙 Dark Mode"
        btn_fg = COLORS.accent_amber if COLORS.mode == 'dark' else COLORS.text_secondary
        
        self.theme_btn = tk.Button(self, text=btn_text, command=self.toggle_theme, 
                                   bg=COLORS.card, fg=btn_fg, bd=0, 
                                   font=("Trebuchet MS", 11, "bold"), cursor="hand2",
                                   activebackground=COLORS.card_hover, activeforeground=COLORS.accent_cyan)
        
        # Place it floating perfectly in the top right corner
        self.theme_btn.place(relx=0.98, rely=0.02, anchor='ne')

    def toggle_theme(self):
        COLORS.toggle()      # Flips the palette
        self._build_ui()     # Erases the app and redraws it in the new colors instantly

    def _route_keypress(self, event):
        try:
            idx = self.notebook.index("current")
            if idx == 1: 
                self.root_tab.handle_keypress(event)
            elif idx == 2: 
                self.matrix_tab.handle_keypress(event)
        except:
            pass

if __name__ == '__main__':
    NumericalSuite().mainloop()