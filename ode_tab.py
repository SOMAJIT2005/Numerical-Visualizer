import math
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from config import COLORS, FONTS, safe_float
from c_bridge import run_numlab_engine
from widgets import GlowButton, IconButton, PremiumEntry, SectionLabel, StatCard, ChipButton, StepControlBar, MethodBanner, show_working_steps_modal


ODE_METHOD_INFO = {
    'euler': (
        "Euler's Explicit 1st-Order Method (C Engine)",
        "y_{n+1} = y_n + h f(t_n, y_n)   |   Local O(h²), Global O(h)",
        "Steps along the initial tangent slope k1 = f(t_n, y_n) at the left endpoint of each step interval [t_n, t_n + h]."
    ),
    'heun': (
        "Heun's Predictor-Corrector (RK2 Trapezoidal) Method (C Engine)",
        "k1 = f(t_n, y_n),   k2 = f(t_n + h, y_n + h k1)   ⇒   y_{n+1} = y_n + (h / 2)(k1 + k2)",
        "Predicts an Euler endpoint y_n + h k1, evaluates the end slope k2, and averages both slopes for 2nd-order O(h²) global accuracy."
    ),
    'midpoint': (
        "Midpoint RK2 (Half-Step) Method (C Engine)",
        "k1 = f(t_n, y_n),   k2 = f(t_n + h/2, y_n + (h/2) k1)   ⇒   y_{n+1} = y_n + h k2",
        "Samples the derivative at the midpoint (t_n + h/2, y_n + (h/2)k1) to advance across the full step with O(h²) global accuracy."
    ),
    'rk4': (
        "Classical 4th-Order Runge-Kutta (RK4) Method (C Engine)",
        "y_{n+1} = y_n + (h / 6)(k1 + 2 k2 + 2 k3 + k4)",
        "Evaluates 4 stage slopes (initial k1, two midpoint trial slopes k2 & k3, and endpoint slope k4) with Simpson-like 1-2-2-1 weights for O(h⁴) accuracy."
    ),
    'system': (
        "Coupled 2D First-Order ODE System Solver via Vector RK4 (C Engine)",
        "dx/dt = f_1(t, x, y),   dy/dt = f_2(t, x, y)   ⇒   [x_{n+1}, y_{n+1}]ᵀ via synchronized 4-stage RK4",
        "Integrates coupled state variables (x(t), y(t)) simultaneously using 4th-order Runge-Kutta and plots the (x, y) phase-plane portrait."
    ),
}


class ODETab(tk.Frame):
    """Unit 6B — Ordinary Differential Equations (IVP) & Systems Lab (C Engine)."""
    def __init__(self, parent, go_home_callback):
        super().__init__(parent, bg=COLORS.bg_root)
        self.go_home_callback = go_home_callback
        self.steps = []
        self.exact_t, self.exact_y = [], []
        self.quiver_tg, self.quiver_yg, self.quiver_ut, self.quiver_uy = [], [], [], []
        self.current_step = 0
        self._build_ui()

    def _build_ui(self):
        wrapper = tk.Frame(self, bg=COLORS.bg_root)
        wrapper.pack(fill=tk.BOTH, expand=True, padx=24, pady=10)

        left_col = tk.Frame(wrapper, bg=COLORS.bg_root, width=400)
        left_col.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 20), pady=5)

        nav_row = tk.Frame(left_col, bg=COLORS.bg_root)
        nav_row.pack(fill=tk.X, pady=(0, 8))
        IconButton(nav_row, '← Back to Dashboard', command=self.go_home_callback, font=FONTS.SUBHEADING).pack(side=tk.LEFT)

        SectionLabel(left_col, 'Unit 6B: ODE Initial-Value Solvers (C)', accent='cyan').pack(anchor='w')

        card = tk.Frame(left_col, bg=COLORS.bg_card, padx=22, pady=16, highlightthickness=1, highlightbackground=COLORS.border)
        card.pack(pady=8, fill=tk.X)

        tk.Label(card, text="ODE Integration Method (C Engine)", font=FONTS.SUBHEADING, bg=COLORS.bg_card, fg=COLORS.accent_cyan).pack(anchor='w', pady=(0, 4))
        self.method_var = tk.StringVar(value='rk4')
        for text, val in [
            ("Euler's Explicit Method (1st Order)", 'euler'),
            ("Heun's Predictor-Corrector (RK2 Trapezoidal)", 'heun'),
            ("Midpoint Method (RK2 Half-Step)", 'midpoint'),
            ("Classical 4th-Order Runge-Kutta (RK4)", 'rk4'),
            ("Coupled 2D ODE System (dx/dt, dy/dt + Phase)", 'system'),
        ]:
            tk.Radiobutton(
                card, text=text, variable=self.method_var, value=val,
                bg=COLORS.bg_card, fg=COLORS.text_secondary, selectcolor=COLORS.bg_panel,
                font=FONTS.BODY, activebackground=COLORS.bg_card,
                activeforeground=COLORS.accent_cyan, command=self._on_method_change
            ).pack(anchor='w', pady=2)

        tk.Frame(card, height=1, bg=COLORS.border).pack(fill=tk.X, pady=8)

        tk.Label(card, text="Presets:", font=FONTS.SMALL, bg=COLORS.bg_card, fg=COLORS.text_muted).pack(anchor='w', pady=(0, 4))
        p_row = tk.Frame(card, bg=COLORS.bg_card)
        p_row.pack(fill=tk.X, pady=(0, 8))
        ChipButton(p_row, "Growth y'=y", command=lambda: self._load_preset('growth'), bg=COLORS.bg_panel).pack(side=tk.LEFT, padx=2)
        ChipButton(p_row, "Decay y'=-2y+t", command=lambda: self._load_preset('decay'), bg=COLORS.bg_panel).pack(side=tk.LEFT, padx=2)
        ChipButton(p_row, "Logistic", command=lambda: self._load_preset('logistic'), bg=COLORS.bg_panel).pack(side=tk.LEFT, padx=2)
        ChipButton(p_row, "Oscillator 2D", command=lambda: self._load_preset('oscillator'), bg=COLORS.bg_panel).pack(side=tk.LEFT, padx=2)

        self.lbl_eq1 = tk.Label(card, text="Derivative dy/dt = f(t, y):", bg=COLORS.bg_card, fg=COLORS.text_secondary, font=FONTS.SUBHEADING)
        self.lbl_eq1.pack(anchor='w', pady=(0, 2))
        self.entry_eq1 = PremiumEntry(card, width=30, default='y')
        self.entry_eq1.pack(fill=tk.X, pady=(0, 6))

        self.lbl_eq2 = tk.Label(card, text="Exact y(t) [optional] or dy/dt for 2D:", bg=COLORS.bg_card, fg=COLORS.text_secondary, font=FONTS.SMALL)
        self.lbl_eq2.pack(anchor='w', pady=(0, 2))
        self.entry_eq2 = PremiumEntry(card, width=30, default='exp(t)')
        self.entry_eq2.pack(fill=tk.X, pady=(0, 8))

        ic_row = tk.Frame(card, bg=COLORS.bg_card)
        ic_row.pack(fill=tk.X, pady=(0, 6))
        for lbl_txt, attr_name, d_val in [('t0:', 'entry_t0', '0.0'), ('y0 (or x0):', 'entry_y0', '1.0'), ('z0 (2D y0):', 'entry_z0', '0.0')]:
            sub = tk.Frame(ic_row, bg=COLORS.bg_card)
            sub.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
            tk.Label(sub, text=lbl_txt, bg=COLORS.bg_card, fg=COLORS.text_secondary, font=FONTS.SMALL).pack(anchor='w')
            ent = PremiumEntry(sub, width=7, default=d_val)
            ent.pack(fill=tk.X)
            setattr(self, attr_name, ent)

        step_row = tk.Frame(card, bg=COLORS.bg_card)
        step_row.pack(fill=tk.X)
        for lbl_txt, attr_name, d_val in [('Final t_end:', 'entry_tend', '2.0'), ('Step Size h:', 'entry_h', '0.2')]:
            sub = tk.Frame(step_row, bg=COLORS.bg_card)
            sub.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
            tk.Label(sub, text=lbl_txt, bg=COLORS.bg_card, fg=COLORS.text_secondary, font=FONTS.SMALL).pack(anchor='w')
            ent = PremiumEntry(sub, width=10, default=d_val)
            ent.pack(fill=tk.X)
            setattr(self, attr_name, ent)

        GlowButton(left_col, text='▶ INTEGRATE ODE TRAJECTORY (C)', command=self._run_ode, width=340, height=50, bg=COLORS.bg_root).pack(pady=(10, 0))

        # Right column
        right_col = tk.Frame(wrapper, bg=COLORS.bg_root)
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)

        stats_row = tk.Frame(right_col, bg=COLORS.bg_root)
        stats_row.pack(fill=tk.X, pady=(0, 6))
        self.stat_t = StatCard(stats_row, "Current Time t_n", COLORS.accent_cyan)
        self.stat_t.pack(side=tk.LEFT, padx=(0, 6))
        self.stat_y = StatCard(stats_row, "Numerical State y_n", COLORS.accent_amber)
        self.stat_y.pack(side=tk.LEFT, padx=6)
        self.stat_exact = StatCard(stats_row, "Exact / 2nd State", COLORS.accent_green)
        self.stat_exact.pack(side=tk.LEFT, padx=6)
        self.stat_err = StatCard(stats_row, "Global Error |y* - y_n|", COLORS.accent_red)
        self.stat_err.pack(side=tk.LEFT, padx=6)

        self.method_banner = MethodBanner(right_col, on_show_steps=self._show_working_steps)
        self.method_banner.pack(fill=tk.X, pady=(0, 6))

        ctrl_row = tk.Frame(right_col, bg=COLORS.bg_root)
        ctrl_row.pack(fill=tk.X, pady=(0, 6))
        self.step_player = StepControlBar(
            ctrl_row,
            on_step_change=self._select_step,
            get_total_steps=lambda: len(self.steps),
            get_current_step=lambda: self.current_step
        )
        self.step_player.pack(side=tk.LEFT)

        self.lbl_stage = tk.Label(
            ctrl_row,
            text="",
            font=FONTS.MONO_SMALL,
            bg=COLORS.bg_card,
            fg=COLORS.text_primary,
            padx=12,
            pady=6,
            anchor='w',
            highlightthickness=1,
            highlightbackground=COLORS.border
        )
        self.lbl_stage.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))

        viz_split = tk.Frame(right_col, bg=COLORS.bg_root)
        viz_split.pack(fill=tk.BOTH, expand=True)

        graph_card = tk.Frame(viz_split, bg=COLORS.bg_card, highlightthickness=1, highlightbackground=COLORS.border)
        graph_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.fig = Figure(figsize=(6.6, 4.8), facecolor=COLORS.plot_face)
        self.fig.subplots_adjust(left=0.10, bottom=0.10, right=0.96, top=0.92)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(COLORS.plot_axes)
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_card)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        table_card = tk.Frame(viz_split, bg=COLORS.bg_card, highlightthickness=1, highlightbackground=COLORS.border)
        table_card.pack(side=tk.RIGHT, fill=tk.Y, padx=(12, 0))

        self.tree = ttk.Treeview(table_card, columns=('step', 't', 'y', 'err'), show='headings', height=20)
        for col, head, w in zip(('step', 't', 'y', 'err'), ('Step', 't_n', 'y_n / x_n', '|Error| / y_n'), (48, 80, 110, 110)):
            self.tree.heading(col, text=head)
            self.tree.column(col, width=w, anchor='center')
        self.tree.pack(fill=tk.Y, expand=True)
        self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)

        self._on_method_change()

    def _load_preset(self, name):
        if name == 'growth':
            self.method_var.set('rk4')
            self.entry_eq1.set('y')
            self.entry_eq2.set('exp(t)')
            self.entry_t0.set('0.0')
            self.entry_y0.set('1.0')
            self.entry_tend.set('2.0')
            self.entry_h.set('0.2')
        elif name == 'decay':
            self.method_var.set('heun')
            self.entry_eq1.set('-2*y + t')
            self.entry_eq2.set('0.5*t - 0.25 + 1.25*exp(-2*t)')
            self.entry_t0.set('0.0')
            self.entry_y0.set('1.0')
            self.entry_tend.set('2.0')
            self.entry_h.set('0.2')
        elif name == 'logistic':
            self.method_var.set('rk4')
            self.entry_eq1.set('y * (1 - y/10)')
            self.entry_eq2.set('10 / (1 + 9*exp(-t))')
            self.entry_t0.set('0.0')
            self.entry_y0.set('1.0')
            self.entry_tend.set('5.0')
            self.entry_h.set('0.5')
        elif name == 'oscillator':
            self.method_var.set('system')
            self.entry_eq1.set('y')
            self.entry_eq2.set('-x - 0.3*y')
            self.entry_t0.set('0.0')
            self.entry_y0.set('2.0')
            self.entry_z0.set('0.0')
            self.entry_tend.set('12.0')
            self.entry_h.set('0.15')
        self._on_method_change()

    def _on_method_change(self):
        m = self.method_var.get()
        if m == 'system':
            self.lbl_eq1.config(text="dx/dt = f1(t, x, y):")
            self.lbl_eq2.config(text="dy/dt = f2(t, x, y):")
            if self.entry_eq2.get() == 'exp(t)':
                self.entry_eq1.set('y')
                self.entry_eq2.set('-x - 0.3*y')
                self.entry_y0.set('2.0')
                self.entry_z0.set('0.0')
                self.entry_tend.set('10.0')
                self.entry_h.set('0.15')
        else:
            self.lbl_eq1.config(text="Derivative dy/dt = f(t, y):")
            self.lbl_eq2.config(text="Exact Solution y(t) [optional]:")
            if '-x' in self.entry_eq2.get():
                self.entry_eq1.set('y')
                self.entry_eq2.set('exp(t)')
                self.entry_y0.set('1.0')
                self.entry_tend.set('2.0')
                self.entry_h.set('0.2')
        self._run_ode()

    def _run_ode(self):
        m = self.method_var.get()
        title, eq_s, desc_s = ODE_METHOD_INFO.get(m, ("ODE Solver", "", ""))
        self.method_banner.set_method(title, eq_s, desc_s)
        eq1 = self.entry_eq1.get().strip()
        eq2 = self.entry_eq2.get().strip()
        try:
            t0 = float(self.entry_t0.get())
            y0 = float(self.entry_y0.get())
            z0 = float(self.entry_z0.get())
            t_end = float(self.entry_tend.get())
            h = float(self.entry_h.get())
            if h <= 0 or t_end <= t0:
                raise ValueError("Require h > 0 and t_end > t0")
        except Exception as ex:
            messagebox.showwarning("Invalid Parameters", f"Check initial conditions and step size:\n{ex}")
            return

        self.steps = []
        self.exact_t, self.exact_y = [], []
        self.quiver_tg, self.quiver_yg, self.quiver_ut, self.quiver_uy = [], [], [], []

        try:
            lines = run_numlab_engine(["ode", m, eq1, eq2, t0, y0, z0, t_end, h])
            for line in lines:
                p = line.split(',')
                if p[0] == 'STEP_SYS' and len(p) >= 7:
                    idx = int(p[1])
                    tv = safe_float(p[2])
                    xv = safe_float(p[3])
                    yv = safe_float(p[4])
                    k1x = safe_float(p[5])
                    k1y = safe_float(p[6])
                    self.steps.append({
                        'mode': 'system', 'step': idx, 't': tv, 'y': xv, 'z': yv, 'err': float('nan'),
                        'trace': f"C Engine Step {idx} (t={tv:.3f}):  x_n = {xv:.5f},  y_n = {yv:.5f}   |   dx/dt = {k1x:.4f},  dy/dt = {k1y:.4f}"
                    })
                elif p[0] == 'STEP_1D' and len(p) >= 12:
                    idx = int(p[1])
                    tv = safe_float(p[2])
                    yv = safe_float(p[3])
                    y_next = safe_float(p[4])
                    y_euler = safe_float(p[5])
                    y_true = safe_float(p[6])
                    err = safe_float(p[7])
                    k1 = safe_float(p[8])
                    k2 = safe_float(p[9])
                    k3 = safe_float(p[10])
                    k4 = safe_float(p[11])
                    if m == 'euler':
                        trace = f"C Engine Step {idx} (t={tv:.3f}):  slope k1={k1:.5f}  →  y_{{n+1}} = {yv:.5f} + {h:g}·({k1:.5f}) = {y_next:.5f}"
                    elif m == 'heun':
                        trace = f"C Engine Step {idx} (t={tv:.3f}):  k1={k1:.4f}, k2={k2:.4f}  →  y_{{n+1}} = {y_next:.5f}"
                    elif m == 'midpoint':
                        trace = f"C Engine Step {idx} (t={tv:.3f}):  k1={k1:.4f}, midpoint k2={k2:.4f}  →  y_{{n+1}} = {y_next:.5f}"
                    else:
                        trace = f"C Engine Step {idx}: k1={k1:.4f}, k2={k2:.4f}, k3={k3:.4f}, k4={k4:.4f} → y_{{n+1}}={y_next:.6f}"
                    self.steps.append({
                        'mode': '1d', 'step': idx, 't': tv, 'y': yv, 'y_next': y_next,
                        'y_euler': y_euler, 'y_true': y_true, 'err': err, 'trace': trace
                    })
                elif p[0] == 'EXACT_CURVE' and len(p) >= 3:
                    self.exact_t.append(safe_float(p[1]))
                    self.exact_y.append(safe_float(p[2]))
                elif p[0] == 'QUIVER' and len(p) >= 5:
                    self.quiver_tg.append(safe_float(p[1]))
                    self.quiver_yg.append(safe_float(p[2]))
                    self.quiver_ut.append(safe_float(p[3]))
                    self.quiver_uy.append(safe_float(p[4]))

            self.tree.delete(*self.tree.get_children())
            for i, s in enumerate(self.steps):
                col4 = f"{s['z']:.5f}" if s['mode'] == 'system' else (f"{s['err']:.2e}" if not math.isnan(s['err']) else "N/A")
                self.tree.insert('', 'end', iid=str(i), values=(s['step'], f"{s['t']:.4f}", f"{s['y']:.6f}", col4))

            if self.steps:
                self._select_step(len(self.steps) - 1)
        except Exception as ex:
            messagebox.showerror("C ODE Engine Error", str(ex))

    def _select_step(self, idx):
        if not self.steps:
            return
        self.current_step = max(0, min(len(self.steps) - 1, idx))
        iid = str(self.current_step)
        if self.tree.exists(iid):
            self.tree.selection_set(iid)
            self.tree.see(iid)
        self._draw_step(self.current_step)
        self.step_player.update_counter()

    def _draw_step(self, idx):
        self.ax.clear()
        self.ax.set_facecolor(COLORS.plot_axes)
        self.ax.grid(True, color=COLORS.plot_grid, linestyle='--', alpha=0.35)
        s = self.steps[idx]

        if s['mode'] == 'system':
            xs = [st['y'] for st in self.steps[:idx + 1]]
            zs = [st['z'] for st in self.steps[:idx + 1]]
            self.ax.plot(xs, zs, 'o-', color=COLORS.accent_cyan, lw=2, markersize=4, label='C Engine Phase Trajectory (x(t), y(t))')
            self.ax.scatter([s['y']], [s['z']], color=COLORS.accent_amber, s=75, zorder=5, label=f"Current State t={s['t']:.2f}")
            self.ax.set_xlabel('x(t)', color=COLORS.text_secondary)
            self.ax.set_ylabel('y(t)', color=COLORS.text_secondary)
            self.ax.set_title('2D Coupled ODE Phase Portrait (C Engine)', color=COLORS.text_primary, fontsize=11)
            self.stat_t.set(f"{s['t']:.4f}")
            self.stat_y.set(f"x = {s['y']:.5f}")
            self.stat_exact.set(f"y = {s['z']:.5f}")
            self.stat_err.set("2D System")
        else:
            ts_all = [st['t'] for st in self.steps]
            ys_all = [st['y'] for st in self.steps]
            eu_all = [st['y_euler'] for st in self.steps]

            if self.quiver_tg:
                self.ax.quiver(self.quiver_tg, self.quiver_yg, self.quiver_ut, self.quiver_uy,
                               color=COLORS.text_muted, alpha=0.35, angles='xy')

            if self.exact_t and self.exact_y:
                self.ax.plot(self.exact_t, self.exact_y, color=COLORS.accent_green, lw=2, alpha=0.8, label='Exact Solution y*(t)')

            if self.method_var.get() != 'euler':
                self.ax.plot(ts_all[:idx + 1], eu_all[:idx + 1], '--', color=COLORS.text_muted, lw=1.4, label='Euler Baseline (C)')

            self.ax.plot(ts_all[:idx + 1], ys_all[:idx + 1], 'o-', color=COLORS.accent_cyan, lw=2.2, markersize=5, label=f"{self.method_var.get().upper()} Trajectory (C)")
            self.ax.scatter([s['t']], [s['y']], color=COLORS.accent_amber, s=75, zorder=6, label=f"(t_{idx}, y_{idx})")

            self.ax.set_xlabel('t', color=COLORS.text_secondary)
            self.ax.set_ylabel('y(t)', color=COLORS.text_secondary)
            self.stat_t.set(f"{s['t']:.4f}")
            self.stat_y.set(f"{s['y']:.6f}")
            self.stat_exact.set(f"{s['y_true']:.6f}" if not math.isnan(s['y_true']) else "N/A")
            self.stat_err.set(f"{s['err']:.3e}" if not math.isnan(s['err']) else "N/A")

        self.lbl_stage.config(text=s['trace'])
        self.ax.legend(loc='best', facecolor=COLORS.bg_panel, edgecolor=COLORS.border, labelcolor=COLORS.text_primary, fontsize=8)
        self.canvas.draw_idle()

    def _on_tree_select(self, event):
        sel = self.tree.selection()
        if sel:
            self.current_step = int(sel[0])
            self._draw_step(self.current_step)
            self.step_player.update_counter()

    def _show_working_steps(self):
        m = self.method_var.get()
        title, eq_s, desc_s = ODE_METHOD_INFO.get(m, ("ODE Solver", "", ""))
        lines = [f"ODE Problem: dy/dt = {self.entry_eq1.get()},   Step Size h = {self.entry_h.get()}"]
        for s in self.steps:
            lines.append(s['trace'])
        show_working_steps_modal(self, title, eq_s, desc_s, lines)

    def handle_keypress(self, event):
        if not self.steps:
            return
        if event.keysym in ('Right', 'space'):
            self.step_player.step_next()
        elif event.keysym == 'Left':
            self.step_player.step_prev()

    def get_state(self):
        return {
            'method': self.method_var.get(),
            'eq1': self.entry_eq1.get(),
            'eq2': self.entry_eq2.get(),
            't0': self.entry_t0.get(),
            'y0': self.entry_y0.get(),
            'z0': self.entry_z0.get(),
            'tend': self.entry_tend.get(),
            'h': self.entry_h.get(),
            'current_step': self.current_step,
        }

    def set_state(self, state):
        if not state:
            return
        self.method_var.set(state.get('method', 'rk4'))
        self.entry_eq1.set(state.get('eq1', 'y'))
        self.entry_eq2.set(state.get('eq2', 'exp(t)'))
        self.entry_t0.set(state.get('t0', '0.0'))
        self.entry_y0.set(state.get('y0', '1.0'))
        self.entry_z0.set(state.get('z0', '0.0'))
        self.entry_tend.set(state.get('tend', '2.0'))
        self.entry_h.set(state.get('h', '0.2'))
        self._run_ode()
        self._select_step(state.get('current_step', 0))
