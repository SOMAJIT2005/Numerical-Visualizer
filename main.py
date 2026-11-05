import json
import matplotlib
matplotlib.use('TkAgg')
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from config import COLORS, FONTS, resource_path
from c_bridge import ensure_c_engines_built
from home_tab import HomeTab
from root_tab import RootFindingTab
from matrix_tab import LinearSystemsTab
from errors_tab import ErrorsApproximationsTab
from optimization_tab import OptimizationTab
from interpolation_tab import InterpolationTab
from integration_tab import IntegrationTab
from ode_tab import ODETab


class NumericalSuite(tk.Tk):
    def __init__(self):
        super().__init__()
        ensure_c_engines_built()
        self.title('Numerical Analysis Suite — Complete 6-Unit C-Powered Learning Lab')
        self.geometry('1440x900')
        self.minsize(1180, 740)

        try:
            icon_path = resource_path('app_icon.ico')
            self.iconbitmap(icon_path)
        except Exception:
            pass

        self.style = ttk.Style()
        self._nav_buttons = []
        self._build_ui()

    def _configure_styles(self):
        self.configure(bg=COLORS.bg)
        self.style.theme_use('default')
        self.style.layout('TNotebook.Tab', [])
        self.style.configure('TNotebook', background=COLORS.bg, borderwidth=0)
        self.style.configure(
            "Treeview",
            background=COLORS.card,
            foreground=COLORS.text_primary,
            fieldbackground=COLORS.card,
            borderwidth=0,
            rowheight=26,
            font=FONTS['mono_small']
        )
        self.style.configure(
            "Treeview.Heading",
            background=COLORS.bg_mid,
            foreground=COLORS.accent_cyan,
            font=FONTS['subheading'],
            borderwidth=0,
            relief='flat'
        )
        self.style.map(
            "Treeview",
            background=[('selected', COLORS.card_active)],
            foreground=[('selected', COLORS.accent_cyan)]
        )

    def _build_ui(self, saved_state=None):
        self._configure_styles()

        if hasattr(self, 'top_bar'):
            self.top_bar.destroy()
        if hasattr(self, 'notebook'):
            self.notebook.destroy()

        # ── PERSISTENT TOP NAVIGATION BAR ──
        self.top_bar = tk.Frame(self, bg=COLORS.card, height=48, highlightthickness=1, highlightbackground=COLORS.border)
        self.top_bar.pack(side=tk.TOP, fill=tk.X)
        self.top_bar.pack_propagate(False)

        brand_frame = tk.Frame(self.top_bar, bg=COLORS.card)
        brand_frame.pack(side=tk.LEFT, padx=(16, 10))
        tk.Label(brand_frame, text="⚡", font=("Segoe UI Emoji", 13), bg=COLORS.card, fg=COLORS.accent_cyan).pack(side=tk.LEFT, padx=(0, 5))
        tk.Label(brand_frame, text="Numerical Lab", font=FONTS['subheading'], bg=COLORS.card, fg=COLORS.text_primary).pack(side=tk.LEFT)

        nav_center = tk.Frame(self.top_bar, bg=COLORS.card)
        nav_center.pack(side=tk.LEFT, padx=8)

        self._nav_buttons = []
        nav_items = [
            ("🏠 Home", 0),
            ("🔬 U1: Errors", 3),
            ("📈 U2: Roots", 1),
            ("🧮 U3: Matrices", 2),
            ("🎯 U4: Optim.", 4),
            ("📐 U5: Interp.", 5),
            ("∫ U6A: Integr.", 6),
            ("⚡ U6B: ODEs", 7),
        ]
        for label, idx in nav_items:
            btn = tk.Button(
                nav_center,
                text=label,
                command=lambda i=idx: self.notebook.select(i),
                bg=COLORS.card,
                fg=COLORS.text_secondary,
                font=FONTS['body_small'],
                bd=0,
                padx=10,
                pady=6,
                cursor="hand2",
                activebackground=COLORS.card_hover,
                activeforeground=COLORS.accent_cyan
            )
            btn.pack(side=tk.LEFT, padx=2)
            self._nav_buttons.append((idx, btn))

        btn_text = "☀ Light Mode" if COLORS.mode == 'dark' else "🌙 Dark Mode"
        btn_fg = COLORS.accent_amber if COLORS.mode == 'dark' else COLORS.text_secondary

        self.theme_btn = tk.Button(
            self.top_bar,
            text=btn_text,
            command=self.toggle_theme,
            bg=COLORS.bg_mid,
            fg=btn_fg,
            bd=0,
            padx=10,
            pady=5,
            font=FONTS['body_small'],
            cursor="hand2",
            activebackground=COLORS.card_hover,
            activeforeground=COLORS.accent_cyan
        )
        self.theme_btn.pack(side=tk.RIGHT, padx=(4, 14), pady=8)

        tk.Button(
            self.top_bar,
            text="📂 Load",
            command=self.load_session_json,
            bg=COLORS.bg_mid,
            fg=COLORS.text_secondary,
            bd=0,
            padx=8,
            pady=5,
            font=FONTS['body_small'],
            cursor="hand2",
            activebackground=COLORS.card_hover,
            activeforeground=COLORS.accent_cyan
        ).pack(side=tk.RIGHT, padx=2, pady=8)

        tk.Button(
            self.top_bar,
            text="💾 Save",
            command=self.save_session_json,
            bg=COLORS.bg_mid,
            fg=COLORS.text_secondary,
            bd=0,
            padx=8,
            pady=5,
            font=FONTS['body_small'],
            cursor="hand2",
            activebackground=COLORS.card_hover,
            activeforeground=COLORS.accent_cyan
        ).pack(side=tk.RIGHT, padx=2, pady=8)

        # ── MAIN NOTEBOOK CONTENT ──
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        go_home = lambda: self.notebook.select(0)
        self.home_tab = HomeTab(self.notebook, self.notebook)
        self.root_tab = RootFindingTab(self.notebook, go_home)
        self.matrix_tab = LinearSystemsTab(self.notebook, go_home)
        self.errors_tab = ErrorsApproximationsTab(self.notebook, go_home)
        self.optim_tab = OptimizationTab(self.notebook, go_home)
        self.interp_tab = InterpolationTab(self.notebook, go_home)
        self.integr_tab = IntegrationTab(self.notebook, go_home)
        self.ode_tab = ODETab(self.notebook, go_home)

        self._tabs = [
            self.home_tab,     # 0
            self.root_tab,     # 1 (preserved index)
            self.matrix_tab,   # 2 (preserved index)
            self.errors_tab,   # 3
            self.optim_tab,    # 4
            self.interp_tab,   # 5
            self.integr_tab,   # 6
            self.ode_tab,      # 7
        ]
        for tab in self._tabs:
            self.notebook.add(tab)

        self.notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)
        self.bind('<Key>', self._route_keypress)

        if saved_state:
            for idx_t, tab in enumerate(self._tabs):
                if hasattr(tab, 'set_state') and f'tab_{idx_t}' in saved_state:
                    tab.set_state(saved_state[f'tab_{idx_t}'])
            self.notebook.select(saved_state.get('tab_idx', 0))

        self._update_nav_highlight()

    def _on_tab_changed(self, event=None):
        self._update_nav_highlight()

    def _update_nav_highlight(self):
        try:
            curr_idx = self.notebook.index("current")
        except Exception:
            curr_idx = 0
        for tab_idx, btn in self._nav_buttons:
            if tab_idx == curr_idx:
                btn.config(bg=COLORS.card_active, fg=COLORS.accent_cyan, font=FONTS['subheading'])
            else:
                btn.config(bg=COLORS.card, fg=COLORS.text_secondary, font=FONTS['body_small'])

    def toggle_theme(self):
        saved_state = {}
        try:
            saved_state['tab_idx'] = self.notebook.index("current")
            for idx_t, tab in enumerate(self._tabs):
                if hasattr(tab, 'get_state'):
                    saved_state[f'tab_{idx_t}'] = tab.get_state()
        except Exception:
            pass

        COLORS.toggle()
        self._build_ui(saved_state=saved_state)

    def save_session_json(self):
        state = {'theme': COLORS.mode, 'tab_idx': self.notebook.index("current")}
        for idx_t, tab in enumerate(self._tabs):
            if hasattr(tab, 'get_state'):
                state[f'tab_{idx_t}'] = tab.get_state()
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Numerical Lab Session", "*.json")],
            initialfile="numerical_lab_session.json",
            title="Save Lab Session"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
            messagebox.showinfo("Session Saved", f"Session saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    def load_session_json(self):
        path = filedialog.askopenfilename(
            filetypes=[("Numerical Lab Session", "*.json")],
            title="Load Lab Session"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                state = json.load(f)
            if state.get('theme') in ('dark', 'light') and state.get('theme') != COLORS.mode:
                COLORS.toggle(state['theme'])
            self._build_ui(saved_state=state)
        except Exception as e:
            messagebox.showerror("Load Error", str(e))

    def _route_keypress(self, event):
        if isinstance(event.widget, (tk.Entry, tk.Text)):
            return
        try:
            idx = self.notebook.index("current")
            if 0 < idx < len(self._tabs):
                tab = self._tabs[idx]
                if hasattr(tab, 'handle_keypress'):
                    tab.handle_keypress(event)
        except Exception:
            pass


if __name__ == '__main__':
    NumericalSuite().mainloop()
