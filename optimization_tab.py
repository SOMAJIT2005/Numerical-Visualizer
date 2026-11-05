import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from config import COLORS, FONTS, safe_float
from c_bridge import run_numlab_engine
from widgets import GlowButton, IconButton, PremiumEntry, SectionLabel, StatCard, ChipButton, StepControlBar, MethodBanner, show_working_steps_modal


OPT_METHOD_INFO = {
    'golden': (
        "1D Golden-Section Search (C Engine)",
        "φ = (√5 - 1)/2 ≈ 0.618034   |   x1 = a + φ(b - a),   x2 = b - φ(b - a)",
        "Narrows a unimodal bracket [a, b] by the Golden Ratio φ at every iteration, reusing one interior function evaluation without derivatives."
    ),
    'parabolic': (
        "1D Successive Parabolic Interpolation (C Engine)",
        "x3 = [f0(x1²-x2²) + f1(x2²-x0²) + f2(x0²-x1²)] / [2f0(x1-x2) + 2f1(x2-x0) + 2f2(x0-x1)]",
        "Fits a unique quadratic parabola through three bracketing points (x0, x1, x2) and jumps directly to its vertex x3."
    ),
    'newton_1d': (
        "1D Newton Stationary-Point Optimization (C Engine)",
        "x_{k+1} = x_k - f'(x_k) / f''(x_k)   |   Min if f''(x*) > 0, Max if f''(x*) < 0",
        "Applies Newton-Raphson to the stationary condition f'(x) = 0 using 2nd-order Taylor curvature f''(x_k)."
    ),
    'grad_2d': (
        "2D Steepest Gradient Descent / Ascent (C Engine)",
        "(x_{k+1}, y_{k+1}) = (x_k, y_k) - α ∇f(x_k, y_k)   where ∇f = [∂f/∂x, ∂f/∂y]ᵀ",
        "Steps orthogonally across contour lines in the direction of steepest descent -∇f(x, y) with step rate α."
    ),
    'coord_2d': (
        "2D Cyclic Coordinate Descent (C Engine)",
        "Odd k: x_{k+1} = x_k - (∂f/∂x)/|∂²f/∂x²|   |   Even k: y_{k+1} = y_k - (∂f/∂y)/|∂²f/∂y²|",
        "Optimizes one coordinate axis at a time (alternating horizontal x-steps and vertical y-steps on the contour surface)."
    ),
    'newton_2d': (
        "2D Multivariable Newton + Hessian Classification (C Engine)",
        "x_{k+1} = x_k - H(x_k)⁻¹ ∇f(x_k)   |   det(H) = f_xx f_yy - (f_xy)²",
        "Uses the full 2×2 Hessian matrix H to jump toward stationary points and classifies them via eigenvalues λ1, λ2 (SPD=Min, Neg-Def=Max, det(H)<0=Saddle)."
    ),
}


class OptimizationTab(tk.Frame):
    """Unit 4 — 1D and 2D Unconstrained Optimization Lab (C Engine)."""
    def __init__(self, parent, go_home_callback):
        super().__init__(parent, bg=COLORS.bg_root)
        self.go_home_callback = go_home_callback
        self.steps = []
        self.curve_x, self.curve_y = [], []
        self.grid_x, self.grid_y, self.grid_z = None, None, None
        self.summary_kind = "---"
        self.current_step = 0
        self._build_ui()

    def _build_ui(self):
        wrapper = tk.Frame(self, bg=COLORS.bg_root)
        wrapper.pack(fill=tk.BOTH, expand=True, padx=24, pady=10)

        left_col = tk.Frame(wrapper, bg=COLORS.bg_root, width=390)
        left_col.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 20), pady=5)

        nav_row = tk.Frame(left_col, bg=COLORS.bg_root)
        nav_row.pack(fill=tk.X, pady=(0, 8))
        IconButton(nav_row, '← Back to Dashboard', command=self.go_home_callback, font=FONTS.SUBHEADING).pack(side=tk.LEFT)

        SectionLabel(left_col, 'Unit 4: Optimization Engine (C)', accent='amber').pack(anchor='w')

        card = tk.Frame(left_col, bg=COLORS.bg_card, padx=22, pady=16, highlightthickness=1, highlightbackground=COLORS.border)
        card.pack(pady=8, fill=tk.X)

        tk.Label(card, text="Optimization Method (C Engine)", font=FONTS.SUBHEADING, bg=COLORS.bg_card, fg=COLORS.accent_cyan).pack(anchor='w', pady=(0, 4))
        self.method_var = tk.StringVar(value='golden')
        for text, val in [
            ('1D Golden-Section Search', 'golden'),
            ('1D Parabolic Interpolation', 'parabolic'),
            ('1D Newton (Stationary Point)', 'newton_1d'),
            ('2D Gradient Descent (Contour)', 'grad_2d'),
            ('2D Coordinate Descent (Axis-Aligned)', 'coord_2d'),
            ('2D Newton + Hessian Classification', 'newton_2d'),
        ]:
            tk.Radiobutton(
                card, text=text, variable=self.method_var, value=val,
                bg=COLORS.bg_card, fg=COLORS.text_secondary, selectcolor=COLORS.bg_panel,
                font=FONTS.BODY, activebackground=COLORS.bg_card,
                activeforeground=COLORS.accent_cyan, command=self._on_method_change
            ).pack(anchor='w', pady=2)

        goal_row = tk.Frame(card, bg=COLORS.bg_card)
        goal_row.pack(fill=tk.X, pady=(8, 4))
        tk.Label(goal_row, text="Goal:", font=FONTS.SUBHEADING, bg=COLORS.bg_card, fg=COLORS.accent_amber).pack(side=tk.LEFT, padx=(0, 10))
        self.goal_var = tk.StringVar(value='min')
        tk.Radiobutton(goal_row, text="Minimize", variable=self.goal_var, value='min', bg=COLORS.bg_card, fg=COLORS.text_primary, selectcolor=COLORS.bg_panel, font=FONTS.BODY).pack(side=tk.LEFT, padx=4)
        tk.Radiobutton(goal_row, text="Maximize", variable=self.goal_var, value='max', bg=COLORS.bg_card, fg=COLORS.text_primary, selectcolor=COLORS.bg_panel, font=FONTS.BODY).pack(side=tk.LEFT, padx=4)

        tk.Frame(card, height=1, bg=COLORS.border).pack(fill=tk.X, pady=8)

        tk.Label(card, text="Presets:", font=FONTS.SMALL, bg=COLORS.bg_card, fg=COLORS.text_muted).pack(anchor='w', pady=(0, 4))
        p_row = tk.Frame(card, bg=COLORS.bg_card)
        p_row.pack(fill=tk.X, pady=(0, 8))
        ChipButton(p_row, "1D Parabola", command=lambda: self._load_preset('1d_quad'), bg=COLORS.bg_panel).pack(side=tk.LEFT, padx=2)
        ChipButton(p_row, "1D Trig-Peak", command=lambda: self._load_preset('1d_trig'), bg=COLORS.bg_panel).pack(side=tk.LEFT, padx=2)
        ChipButton(p_row, "2D Bowl", command=lambda: self._load_preset('2d_bowl'), bg=COLORS.bg_panel).pack(side=tk.LEFT, padx=2)
        ChipButton(p_row, "2D Saddle", command=lambda: self._load_preset('2d_saddle'), bg=COLORS.bg_panel).pack(side=tk.LEFT, padx=2)

        self.lbl_eq = tk.Label(card, text="Objective f(x):", bg=COLORS.bg_card, fg=COLORS.text_secondary, font=FONTS.SUBHEADING)
        self.lbl_eq.pack(anchor='w', pady=(0, 2))
        self.entry_eq = PremiumEntry(card, width=28, default='(x - 2)^2 + 1')
        self.entry_eq.pack(fill=tk.X, pady=(0, 8))

        self.lbl_v1 = tk.Label(card, text="Lower Bound a (or x0):", bg=COLORS.bg_card, fg=COLORS.text_secondary, font=FONTS.SUBHEADING)
        self.lbl_v1.pack(anchor='w', pady=(0, 2))
        self.entry_v1 = PremiumEntry(card, width=28, default='0.0')
        self.entry_v1.pack(fill=tk.X, pady=(0, 8))

        self.lbl_v2 = tk.Label(card, text="Upper Bound b (or y0):", bg=COLORS.bg_card, fg=COLORS.text_secondary, font=FONTS.SUBHEADING)
        self.lbl_v2.pack(anchor='w', pady=(0, 2))
        self.entry_v2 = PremiumEntry(card, width=28, default='5.0')
        self.entry_v2.pack(fill=tk.X, pady=(0, 8))

        tk.Label(card, text="Tolerance:", bg=COLORS.bg_card, fg=COLORS.text_secondary, font=FONTS.SUBHEADING).pack(anchor='w', pady=(0, 2))
        self.entry_tol = PremiumEntry(card, width=28, default='0.0001')
        self.entry_tol.pack(fill=tk.X)

        GlowButton(left_col, text='▶ OPTIMIZE OBJECTIVE (C ENGINE)', command=self._run_optimizer, accent='amber', width=340, height=50, bg=COLORS.bg_root).pack(pady=(10, 0))

        # Right visualization & step trace column
        right_col = tk.Frame(wrapper, bg=COLORS.bg_root)
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)

        stats_row = tk.Frame(right_col, bg=COLORS.bg_root)
        stats_row.pack(fill=tk.X, pady=(0, 6))
        self.stat_pt = StatCard(stats_row, "Current Point x*", COLORS.accent_cyan)
        self.stat_pt.pack(side=tk.LEFT, padx=(0, 6))
        self.stat_val = StatCard(stats_row, "Objective f(x*)", COLORS.accent_green)
        self.stat_val.pack(side=tk.LEFT, padx=6)
        self.stat_grad = StatCard(stats_row, "||∇f|| / Width", COLORS.accent_amber)
        self.stat_grad.pack(side=tk.LEFT, padx=6)
        self.stat_class = StatCard(stats_row, "Curvature / Classification", COLORS.accent_purple)
        self.stat_class.pack(side=tk.LEFT, padx=6)

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

        self.lbl_trace = tk.Label(
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
        self.lbl_trace.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))

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

        self.tree = ttk.Treeview(table_card, columns=('iter', 'pt', 'fval', 'metric'), show='headings', height=20)
        for col, head, w in zip(('iter', 'pt', 'fval', 'metric'), ('Iter', 'Point', 'f(x)', 'Grad / Width'), (45, 120, 95, 95)):
            self.tree.heading(col, text=head)
            self.tree.column(col, width=w, anchor='center')
        self.tree.pack(fill=tk.Y, expand=True)
        self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)

        self._on_method_change()

    def _load_preset(self, name):
        if name == '1d_quad':
            self.method_var.set('golden')
            self.goal_var.set('min')
            self.entry_eq.set('(x - 2)^2 + 1')
            self.entry_v1.set('0.0')
            self.entry_v2.set('5.0')
        elif name == '1d_trig':
            self.method_var.set('parabolic')
            self.goal_var.set('max')
            self.entry_eq.set('2*sin(x) - (x^2)/10')
            self.entry_v1.set('0.0')
            self.entry_v2.set('4.0')
        elif name == '2d_bowl':
            self.method_var.set('grad_2d')
            self.goal_var.set('min')
            self.entry_eq.set('(x - 1)^2 + 2*(y + 1.5)^2')
            self.entry_v1.set('-2.0')
            self.entry_v2.set('2.0')
        elif name == '2d_saddle':
            self.method_var.set('newton_2d')
            self.goal_var.set('min')
            self.entry_eq.set('x^2 - y^2 + 0.2*x - 0.4*y')
            self.entry_v1.set('1.5')
            self.entry_v2.set('1.2')
        self._on_method_change()

    def _on_method_change(self):
        m = self.method_var.get()
        if m in ('grad_2d', 'coord_2d', 'newton_2d'):
            self.lbl_eq.config(text="Objective f(x, y):")
            if 'y' not in self.entry_eq.get():
                self.entry_eq.set('(x - 1)^2 + 2*(y + 1.5)^2')
                self.entry_v1.set('-2.0')
                self.entry_v2.set('2.0')
            self.lbl_v1.config(text="Initial Guess x0:")
            self.lbl_v2.config(text="Initial Guess y0:")
        elif m == 'newton_1d':
            self.lbl_eq.config(text="Objective f(x):")
            if 'y' in self.entry_eq.get():
                self.entry_eq.set('(x - 2)^2 + 1')
            self.lbl_v1.config(text="Initial Guess x0:")
            self.lbl_v2.config(text="(Unused in 1D Newton):")
        else:
            self.lbl_eq.config(text="Objective f(x):")
            if 'y' in self.entry_eq.get():
                self.entry_eq.set('(x - 2)^2 + 1')
                self.entry_v1.set('0.0')
                self.entry_v2.set('5.0')
            self.lbl_v1.config(text="Bracket Lower Bound a:")
            self.lbl_v2.config(text="Bracket Upper Bound b:")
        self._run_optimizer()

    def _run_optimizer(self):
        m = self.method_var.get()
        title, eq_s, desc_s = OPT_METHOD_INFO.get(m, ("Optimization", "", ""))
        self.method_banner.set_method(title, eq_s, desc_s)
        eq = self.entry_eq.get().strip()
        is_max = (self.goal_var.get() == 'max')
        c_eq = f"-({eq})" if is_max and m in ('golden', 'parabolic', 'grad_2d', 'coord_2d') else eq
        flip = -1.0 if is_max and m in ('golden', 'parabolic', 'grad_2d', 'coord_2d') else 1.0

        try:
            v1 = float(self.entry_v1.get())
            v2 = float(self.entry_v2.get())
            tol = max(1e-10, float(self.entry_tol.get()))
        except Exception:
            messagebox.showwarning("Invalid Parameters", "Enter valid numeric bounds/starting guesses and tolerance.")
            return

        self.steps = []
        self.curve_x, self.curve_y = [], []
        self.grid_x, self.grid_y, self.grid_z = None, None, None
        self.summary_kind = "---"

        try:
            if m in ('golden', 'parabolic', 'newton_1d'):
                c_method = 'newton1d' if m == 'newton_1d' else m
                lines = run_numlab_engine(["opt_1d", c_method, c_eq, v1, v2, tol])

                for line in lines:
                    p = line.split(',')
                    if p[0] == 'STEP' and len(p) >= 9:
                        k = int(p[1])
                        x_v = safe_float(p[2])
                        fx_v = flip * safe_float(p[3])
                        err = safe_float(p[4])
                        a_v = safe_float(p[5])
                        b_v = safe_float(p[6])
                        x1_v = safe_float(p[7])
                        x2_v = safe_float(p[8])
                        if m == 'newton_1d':
                            self.steps.append({
                                'mode': '1d_newton', 'iter': k, 'x': x_v, 'x_next': a_v,
                                'fx': fx_v, 'metric': abs(b_v),
                                'desc': f"C Engine Iter {k}: x={x_v:.5f}, f'(x)={b_v:.3e}, f''(x)={x1_v:.3e} → x_next={a_v:.5f}"
                            })
                        else:
                            self.steps.append({
                                'mode': '1d', 'iter': k, 'a': a_v, 'b': b_v, 'x1': x1_v, 'x2': x2_v,
                                'x': x_v, 'fx': fx_v, 'metric': err,
                                'desc': f"C Engine Iter {k}: [{a_v:.4f}, {b_v:.4f}], x1={x1_v:.4f}, x2={x2_v:.4f} → x*={x_v:.5f}"
                            })
                    elif p[0] == 'SUMMARY' and len(p) >= 6:
                        if is_max and m in ('golden', 'parabolic'):
                            self.summary_kind = "Local Maximum (f''<0)"
                        else:
                            self.summary_kind = p[4]
                    elif p[0] == 'CURVE' and len(p) >= 3:
                        self.curve_x.append(safe_float(p[1]))
                        self.curve_y.append(flip * safe_float(p[2]))
            else:
                c_method = {'grad_2d': 'grad2d', 'coord_2d': 'coord2d', 'newton_2d': 'newton2d'}.get(m, 'newton2d')
                lines = run_numlab_engine(["opt_2d", c_method, c_eq, v1, v2, 0.15])
                grid_rows = []
                ng = 0
                gx0, gx1, gy0, gy1 = -3.0, 3.0, -3.0, 3.0

                for line in lines:
                    p = line.split(',')
                    if p[0] == 'STEP' and len(p) >= 8:
                        k = int(p[1])
                        xv, yv = safe_float(p[2]), safe_float(p[3])
                        fxv = flip * safe_float(p[4])
                        gnorm = safe_float(p[5])
                        xn, yn = safe_float(p[6]), safe_float(p[7])
                        self.steps.append({
                            'mode': '2d', 'iter': k, 'x': xv, 'y': yv, 'x_next': xn, 'y_next': yn,
                            'fx': fxv, 'metric': gnorm,
                            'desc': f"C Engine Iter {k}: (x,y)=({xv:.4f}, {yv:.4f}), ||∇f||={gnorm:.3e} → ({xn:.4f}, {yn:.4f})"
                        })
                    elif p[0] == 'SUMMARY' and len(p) >= 9:
                        l1, l2 = safe_float(p[5]), safe_float(p[6])
                        kind = p[8]
                        if is_max and m == 'grad_2d':
                            kind = "Local Maximum"
                        self.summary_kind = f"{kind} (λ={l1:.2g},{l2:.2g})"
                    elif p[0] == 'GRID_META' and len(p) >= 6:
                        ng = int(p[1])
                        gx0, gx1 = safe_float(p[2]), safe_float(p[3])
                        gy0, gy1 = safe_float(p[4]), safe_float(p[5])
                    elif p[0] == 'GRID_ROW' and len(p) >= 3:
                        grid_rows.append([flip * safe_float(v) for v in p[2:]])

                if ng > 0 and len(grid_rows) == ng:
                    self.grid_x, self.grid_y = np.meshgrid(np.linspace(gx0, gx1, ng), np.linspace(gy0, gy1, ng))
                    self.grid_z = np.array(grid_rows, dtype=float)

            for s in self.steps:
                s['cls'] = self.summary_kind

            self.tree.delete(*self.tree.get_children())
            for i, s in enumerate(self.steps):
                pt_str = f"({s['x']:.3f}, {s['y']:.3f})" if s['mode'] == '2d' else f"{s['x']:.5f}"
                self.tree.insert('', 'end', iid=str(i), values=(s['iter'], pt_str, f"{s['fx']:.5f}", f"{s['metric']:.2e}"))

            if self.steps:
                self._select_step(len(self.steps) - 1)
        except Exception as ex:
            messagebox.showwarning("C Engine Optimization Error", str(ex))

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

        if s['mode'] in ('1d', '1d_newton'):
            if self.curve_x and self.curve_y:
                self.ax.plot(self.curve_x, self.curve_y, color=COLORS.accent_cyan, lw=2.2, label='Objective f(x) (C Engine)')

            if s['mode'] == '1d':
                self.ax.axvspan(min(s['a'], s['b']), max(s['a'], s['b']), color=COLORS.accent_cyan, alpha=0.12, label='Search Bracket [a, b]')
                self.ax.axvline(s['x1'], color=COLORS.accent_amber, ls='--', alpha=0.7, label='Interior x1 / x2')
                self.ax.axvline(s['x2'], color=COLORS.accent_amber, ls='--', alpha=0.7)
            self.ax.scatter([s['x']], [s['fx']], color=COLORS.accent_green, s=70, zorder=5, label=f"Current x* = {s['x']:.5f}")
            self.ax.set_xlabel('x', color=COLORS.text_secondary)
            self.ax.set_ylabel('f(x)', color=COLORS.text_secondary)
            self.ax.legend(loc='best', facecolor=COLORS.bg_panel, edgecolor=COLORS.border, labelcolor=COLORS.text_primary)
            self.stat_pt.set(f"{s['x']:.5f}")
        else:
            xs_path = [st['x'] for st in self.steps[:idx + 1]] + [s['x_next']]
            ys_path = [st['y'] for st in self.steps[:idx + 1]] + [s['y_next']]
            if self.grid_x is not None and self.grid_z is not None:
                self.ax.contour(self.grid_x, self.grid_y, self.grid_z, levels=18, cmap='cool', alpha=0.65)
            self.ax.plot(xs_path, ys_path, 'o--', color=COLORS.accent_amber, lw=2, markersize=5, label='C Engine Trajectory')
            self.ax.scatter([s['x']], [s['y']], color=COLORS.accent_red, s=65, zorder=5, label='Current (x_k, y_k)')
            self.ax.scatter([s['x_next']], [s['y_next']], color=COLORS.accent_green, s=65, zorder=6, label='Next Step')
            self.ax.set_xlabel('x', color=COLORS.text_secondary)
            self.ax.set_ylabel('y', color=COLORS.text_secondary)
            self.ax.legend(loc='best', facecolor=COLORS.bg_panel, edgecolor=COLORS.border, labelcolor=COLORS.text_primary)
            self.stat_pt.set(f"({s['x']:.3f}, {s['y']:.3f})")

        self.stat_val.set(f"{s['fx']:.6f}")
        self.stat_grad.set(f"{s['metric']:.3e}")
        self.stat_class.set(s['cls'])
        self.lbl_trace.config(text=s['desc'])
        self.canvas.draw_idle()

    def _on_tree_select(self, event):
        sel = self.tree.selection()
        if sel:
            self.current_step = int(sel[0])
            self._draw_step(self.current_step)
            self.step_player.update_counter()

    def _show_working_steps(self):
        m = self.method_var.get()
        title, eq_s, desc_s = OPT_METHOD_INFO.get(m, ("Optimization", "", ""))
        lines = [
            f"Objective: {'Maximize' if self.goal_var.get() == 'max' else 'Minimize'} f = {self.entry_eq.get()}   |   Classification: {self.summary_kind}"
        ]
        for s in self.steps:
            lines.append(f"Step {s['iter']}:  {s['desc']}   [f = {s['fx']:.8g}]")
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
            'goal': self.goal_var.get(),
            'eq': self.entry_eq.get(),
            'v1': self.entry_v1.get(),
            'v2': self.entry_v2.get(),
            'tol': self.entry_tol.get(),
            'current_step': self.current_step,
        }

    def set_state(self, state):
        if not state:
            return
        self.method_var.set(state.get('method', 'golden'))
        self.goal_var.set(state.get('goal', 'min'))
        self.entry_eq.set(state.get('eq', '(x - 2)^2 + 1'))
        self.entry_v1.set(state.get('v1', '0.0'))
        self.entry_v2.set(state.get('v2', '5.0'))
        self.entry_tol.set(state.get('tol', '0.0001'))
        self._run_optimizer()
        self._select_step(state.get('current_step', 0))
