import tkinter as tk
from tkinter import ttk
import subprocess, os, numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from config import COLORS, FONTS, safe_float
from widgets import GlowButton, IconButton, PremiumEntry, SectionLabel, StatCard

class RootFindingTab(tk.Frame):
    def __init__(self, parent, go_home_callback):
        super().__init__(parent, bg=COLORS.bg)
        self.go_home_callback = go_home_callback
        self.algorithm_steps, self.current_step = [], 0
        self._panning, self._pan_start = False, None
        self._build_ui()

    def _build_ui(self):
        self.screen_input = tk.Frame(self, bg=COLORS.bg)
        self.screen_input.pack(fill=tk.BOTH, expand=True)

        content_wrapper = tk.Frame(self.screen_input, bg=COLORS.bg)
        content_wrapper.pack(expand=True) 

        # ── LEFT COLUMN (Configuration) ──
        left_col = tk.Frame(content_wrapper, bg=COLORS.bg, padx=40)
        left_col.pack(side=tk.LEFT, fill=tk.Y, pady=20)

        IconButton(left_col, '← Back to Dashboard', command=self.go_home_callback, font=FONTS['heading']).pack(anchor='w', pady=(0, 20))
        SectionLabel(left_col, 'Configuration').pack(anchor='w')
        
        card = tk.Frame(left_col, bg=COLORS.card, padx=35, pady=30, highlightthickness=1, highlightbackground=COLORS.border)
        card.pack(pady=15)

        self.method_var = tk.StringVar(value='bisection')

        cat_frame = tk.Frame(card, bg=COLORS.card)
        cat_frame.pack(fill=tk.X, pady=(0, 10))

        col_bracketing = tk.Frame(cat_frame, bg=COLORS.card)
        col_bracketing.pack(side=tk.LEFT, anchor='n', padx=(0, 45))
        
        tk.Label(col_bracketing, text="Bracketing", font=FONTS['subheading'], bg=COLORS.card, fg=COLORS.accent_cyan).pack(anchor='w', pady=(0, 10))
        for text, val in [('Bisection', 'bisection'), ('False Position', 'false_position'), ("Brent's", 'brent')]:
            tk.Radiobutton(col_bracketing, text=text, variable=self.method_var, value=val, 
                           bg=COLORS.card, fg=COLORS.text_secondary, selectcolor=COLORS.bg_panel,
                           font=FONTS['heading'], command=self._toggle_inputs,
                           activebackground=COLORS.card, activeforeground=COLORS.accent_cyan).pack(anchor='w', pady=3)

        col_open = tk.Frame(cat_frame, bg=COLORS.card)
        col_open.pack(side=tk.LEFT, anchor='n')
        
        tk.Label(col_open, text="Open Methods", font=FONTS['subheading'], bg=COLORS.card, fg=COLORS.accent_amber).pack(anchor='w', pady=(0, 10))
        for text, val in [('Newton', 'newton'), ('Mod. Newton', 'modified_newton'), ('Secant', 'secant'), ('Mod. Secant', 'modified_secant')]:
            tk.Radiobutton(col_open, text=text, variable=self.method_var, value=val, 
                           bg=COLORS.card, fg=COLORS.text_secondary, selectcolor=COLORS.bg_panel,
                           font=FONTS['heading'], command=self._toggle_inputs,
                           activebackground=COLORS.card, activeforeground=COLORS.accent_cyan).pack(anchor='w', pady=3)

        tk.Frame(card, height=1, bg=COLORS.border, width=420).pack(pady=15)

        tk.Label(card, text="Tolerance (ε):", bg=COLORS.card, fg=COLORS.text_secondary, font=FONTS['subheading']).pack(anchor='w', pady=(0, 2))
        self.entry_tol = PremiumEntry(card, width=32, default='0.0001')
        self.entry_tol.pack(pady=(0, 10))

        tk.Label(card, text="Equation f(x):", bg=COLORS.card, fg=COLORS.text_secondary, font=FONTS['subheading']).pack(anchor='w', pady=(0, 2))
        self.entry_eq = PremiumEntry(card, width=32, default='x^3 - 2*x - 5')
        self.entry_eq.pack(pady=(0, 10))
        self.entry_eq._entry.bind('<KeyRelease>', self._update_preview)

        self.input_block = tk.Frame(card, bg=COLORS.card)
        self.input_block.pack(fill=tk.X)

        self.lbl_v1 = tk.Label(self.input_block, text="Point a:", bg=COLORS.card, fg=COLORS.text_secondary, font=FONTS['subheading'])
        self.lbl_v1.pack(anchor='w', pady=(0, 2))
        self.entry_v1 = PremiumEntry(self.input_block, width=32, default='0.0')
        self.entry_v1.pack(pady=(0, 10))

        self.lbl_v2 = tk.Label(self.input_block, text="Point b:", bg=COLORS.card, fg=COLORS.text_secondary, font=FONTS['subheading'])
        self.lbl_v2.pack(anchor='w', pady=(0, 2))
        self.entry_v2 = PremiumEntry(self.input_block, width=32, default='2.0')
        self.entry_v2.pack()

        # ── RIGHT COLUMN (Preview & Action) ──
        right_col = tk.Frame(content_wrapper, bg=COLORS.bg)
        right_col.pack(side=tk.LEFT, padx=(80, 0), anchor='n', pady=75) 

        preview_frame = tk.Frame(right_col, bg=COLORS.bg_panel, padx=2, pady=2)
        preview_frame.pack()
        
        self.prev_fig = Figure(figsize=(4.5, 3.8), facecolor=COLORS.bg)
        self.prev_ax = self.prev_fig.add_subplot(111); self.prev_ax.set_facecolor(COLORS.plot_axes)
        self.prev_canvas = FigureCanvasTkAgg(self.prev_fig, master=preview_frame)
        self.prev_canvas.get_tk_widget().pack()
        self._update_preview()

        GlowButton(right_col, text='▶ CALCULATE', command=self._run_solver, width=340, height=65, bg=COLORS.bg).pack(pady=(40, 0))

        # ── RESULT SCREEN ──
        self.screen_graph = tk.Frame(self, bg=COLORS.bg)
        dash_bar = tk.Frame(self.screen_graph, bg=COLORS.bg, pady=15, padx=20)
        dash_bar.pack(fill=tk.X)
        IconButton(dash_bar, '← BACK', command=self._go_back).pack(side=tk.LEFT, padx=(0, 20))
        
        self.stat_guess = StatCard(dash_bar, "Current xr", COLORS.accent_cyan)
        self.stat_guess.pack(side=tk.LEFT, padx=5)
        self.stat_ea = StatCard(dash_bar, "Approx Error", COLORS.accent_amber)
        self.stat_ea.pack(side=tk.LEFT, padx=5)
        self.stat_et = StatCard(dash_bar, "True Error", COLORS.accent_red)
        self.stat_et.pack(side=tk.LEFT, padx=5)
        self.stat_root = StatCard(dash_bar, "Target Root", COLORS.accent_green)
        self.stat_root.pack(side=tk.LEFT, padx=5)

        main_res = tk.Frame(self.screen_graph, bg=COLORS.bg)
        main_res.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        self.fig = Figure(figsize=(9, 6), facecolor=COLORS.bg)
        self.ax = self.fig.add_subplot(111); self.ax.set_facecolor(COLORS.plot_axes)
        self.canvas = FigureCanvasTkAgg(self.fig, master=main_res)
        self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(main_res, columns=('step', 'x', 'ea', 'et'), show='headings', height=22)
        for col, head, w in zip(self.tree['columns'], ('Step', 'xr', 'εa (%)', 'εt (%)'), (50, 100, 120, 120)): 
            self.tree.heading(col, text=head)
            self.tree.column(col, width=w, anchor='center')
        self.tree.pack(side=tk.RIGHT, fill=tk.Y, padx=(20, 0))
        self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)

        self.canvas.mpl_connect('scroll_event', self._on_scroll)
        self.canvas.mpl_connect('button_press_event', self._on_press)
        self.canvas.mpl_connect('button_release_event', self._on_release)
        self.canvas.mpl_connect('motion_notify_event', self._on_motion)

    def _toggle_inputs(self):
        m = self.method_var.get()
        self.lbl_v1.pack(anchor='w', pady=(0, 2)); self.entry_v1.pack(pady=(0, 10))
        self.lbl_v2.pack(anchor='w', pady=(0, 2)); self.entry_v2.pack()

        if m in ('newton', 'modified_newton'):
            self.lbl_v1.config(text="Initial Guess (x0):")
            self.lbl_v2.pack_forget(); self.entry_v2.pack_forget()
        elif m in ('bisection', 'false_position', 'brent'):
            self.lbl_v1.config(text="Point a:"); self.lbl_v2.config(text="Point b:")
        elif m == 'secant':
            self.lbl_v1.config(text="Initial x0:"); self.lbl_v2.config(text="Initial x1:")
        elif m == 'modified_secant':
            self.lbl_v1.config(text="Initial x0:"); self.lbl_v2.config(text="Delta (δ):")

    def _update_frame(self, idx):
        self.ax.clear(); self.ax.set_facecolor(COLORS.plot_axes)
        self.ax.plot(self.curve_x, self.curve_y, color=COLORS.accent_cyan, alpha=0.3)
        self.ax.axhline(0, color=COLORS.border_mid, lw=1)
        s = self.algorithm_steps[idx]
        m = self.method_var.get()

        if m in ('bisection', 'false_position', 'brent'):
            self.ax.axvspan(s[1], s[2], color=COLORS.accent_cyan, alpha=0.1)
            self.ax.axvline(s[1], color=COLORS.accent_red, ls='--', alpha=0.5)
            self.ax.axvline(s[2], color=COLORS.accent_cyan, ls='--', alpha=0.5)
            if m == 'false_position':
                self.ax.plot([s[1], s[2]], [np.interp(s[1], self.curve_x, self.curve_y), np.interp(s[2], self.curve_x, self.curve_y)], color=COLORS.accent_amber, lw=1, ls='-')
            self.ax.axvline(s[3], color=COLORS.accent_amber, lw=2.5)
            self.ax.text(s[3], self.ax.get_ylim()[0]*0.9, ' xr', color=COLORS.accent_amber, fontweight='bold')
            
        elif m in ('newton', 'modified_newton'):
            x, fx, x_next = s[1], s[2], s[3]
            self.ax.plot([x, x_next], [fx, 0], color=COLORS.accent_amber, lw=2, ls='--')
            self.ax.scatter([x], [fx], color=COLORS.accent_amber, s=50)
            self.ax.annotate('xr', xy=(x_next, 0), xytext=(x_next, self.ax.get_ylim()[1]*0.1), arrowprops=dict(arrowstyle='->', color=COLORS.accent_amber))
            
        elif m in ('secant', 'modified_secant'):
            x_prev, fx_prev, x_curr, fx_curr, x_next = s[1], s[2], s[3], s[4], s[5]
            self.ax.plot([x_prev, x_next], [fx_prev, 0], color=COLORS.accent_amber, lw=2, ls='--')
            self.ax.scatter([x_prev, x_curr], [fx_prev, fx_curr], color=COLORS.accent_amber, s=50)
            self.ax.annotate('xr', xy=(x_next, 0), xytext=(x_next, self.ax.get_ylim()[1]*0.1), arrowprops=dict(arrowstyle='->', color=COLORS.accent_amber))

        if self.true_root: self.ax.scatter([self.true_root], [0], color=COLORS.accent_green, s=80, edgecolors='white', zorder=6)
        
        xr_val = s[3] if len(s) < 8 else s[5] 
        self.stat_guess.set(f"{xr_val:.5f}")
        self.stat_ea.set(f"{s[-2] * 100:.4f}%") 
        self.stat_et.set(f"{s[-1] * 100:.4f}%") 
        self.canvas.draw_idle()

    def _update_preview(self, e=None):
        self.prev_ax.clear(); self.prev_ax.set_facecolor(COLORS.plot_axes); self.prev_ax.grid(True, color=COLORS.plot_grid, linestyle='--', alpha=0.3)
        try:
            eq = self.entry_eq.get().replace('^', '**').replace('exp', 'np.exp').replace('sin', 'np.sin').replace('cos', 'np.cos')
            x = np.linspace(-5, 5, 100); y = eval(eq, {"__builtins__": None}, {"x": x, "np": np})
            self.prev_ax.plot(x, y, color=COLORS.accent_cyan, lw=2); self.prev_ax.axhline(0, color=COLORS.text_muted, lw=1)
        except: pass
        self.prev_canvas.draw_idle()

    def _run_solver(self):
        self.focus_set()
        exe = os.path.join('build', 'engine.exe')
        args = [exe, self.method_var.get(), self.entry_eq.get(), self.entry_v1.get(), self.entry_v2.get(), self.entry_tol.get()]
        res = subprocess.run(args, capture_output=True, text=True)
        self._on_solver_done(res)

    def _on_solver_done(self, res):
        self.curve_x, self.curve_y, self.algorithm_steps, self.true_root = [], [], [], None
        for line in res.stdout.splitlines():
            p = line.split(',')
            if p[0] == 'CURVE': self.curve_x.append(float(p[1])); self.curve_y.append(float(p[2]))
            elif p[0] == 'TRUEROOT' and p[1] != 'NAN': self.true_root = float(p[1])
            elif p[0] == 'STEP': self.algorithm_steps.append([safe_float(v) for v in p[1:]])
            
        self.stat_root.set(f"{self.true_root:.5f}" if self.true_root else "N/A")
        self.tree.delete(*self.tree.get_children())
        
        for s in self.algorithm_steps:
            xr_val = s[3] if len(s) < 8 else s[5] 
            self.tree.insert('', 'end', iid=str(int(s[0])), values=(
                int(s[0]), f"{xr_val:.5f}", f"{s[-2] * 100:.4f}%", f"{s[-1] * 100:.4f}%"
            ))
            
        self.screen_input.pack_forget(); self.screen_graph.pack(fill=tk.BOTH, expand=True); self.current_step = 0; self._update_frame(0)

    def _go_back(self): self.screen_graph.pack_forget(); self.screen_input.pack(fill=tk.BOTH, expand=True)
    def _on_scroll(self, event):
        ax = self.ax; xmin, xmax = ax.get_xlim(); f = 0.85 if event.button == 'up' else 1.15
        ax.set_xlim(event.xdata + (xmin - event.xdata) * f, event.xdata + (xmax - event.xdata) * f); self.canvas.draw_idle()
    def _on_press(self, event): 
        if event.inaxes: self._pan_start = (event.x, event.y); self._panning = True
    def _on_release(self, event): self._panning = False
    def _on_motion(self, event):
        if self._panning and event.inaxes:
            dx = (event.x - self._pan_start[0]) / 60.0 
            dy = (event.y - self._pan_start[1]) / 60.0
            xmin, xmax = self.ax.get_xlim(); self.ax.set_xlim(xmin - dx, xmax - dx)
            ymin, ymax = self.ax.get_ylim(); self.ax.set_ylim(ymin - dy, ymax - dy)
            self._pan_start = (event.x, event.y); self.canvas.draw_idle()
    def _on_tree_select(self, event):
        selected = self.tree.selection()
        if selected: self.current_step = int(selected[0]); self._update_frame(self.current_step)
    def handle_keypress(self, event):
        if not self.algorithm_steps: return
        if event.keysym in ('Right', 'space'): self.current_step = min(len(self.algorithm_steps)-1, self.current_step+1)
        elif event.keysym == 'Left': self.current_step = max(0, self.current_step-1)
        self._update_frame(self.current_step)