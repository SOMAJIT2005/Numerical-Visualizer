import math
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from config import COLORS, FONTS, safe_float
from c_bridge import run_numlab_engine
from widgets import GlowButton, IconButton, PremiumEntry, SectionLabel, StatCard, ChipButton, MethodBanner, show_working_steps_modal


INTERP_METHOD_INFO = {
    'newton_dd': (
        "Newton's Divided-Difference Interpolating Polynomial (C Engine)",
        "P_n(x) = f[x0] + f[x0,x1](x-x0) + ... + f[x0..xn](x-x0)...(x-x_{n-1})",
        "Constructs recursive divided differences f[xi..x_{i+k}] = (f[x_{i+1}..x_{i+k}] - f[xi..x_{i+k-1}]) / (x_{i+k} - xi) and evaluates P_n(x) in O(n) nested form."
    ),
    'lagrange': (
        "Lagrange Interpolating Polynomial & Basis Functions (C Engine)",
        "P_n(x) = Σ_{i=0}^n y_i L_i(x)   where   L_i(x) = Π_{j≠i} (x - x_j) / (x_i - x_j)",
        "Builds cardinal basis polynomials L_i(x) satisfying L_i(x_j) = δ_{ij} (1 at node i, 0 at all other nodes) and sums y_i L_i(x)."
    ),
    'coeffs': (
        "Standard Power-Basis Coefficients & Vandermonde System (C Engine)",
        "V c = y   ⇒   P_n(x) = c_0 + c_1 x + c_2 x² + ... + c_n x^n",
        "Solves the Vandermonde linear system V c = y in C and reports the infinity-norm condition number κ_∞(V)."
    ),
    'inverse': (
        "Inverse Interpolation x = P⁻¹(y*) (C Engine)",
        "x(y*) = x_0 + f⁻¹[y0,y1](y* - y0) + f⁻¹[y0,y1,y2](y* - y0)(y* - y1) + ...",
        "Swaps roles of (x_i, y_i) when y_i is strictly monotonic on the interval to estimate x where f(x) = y*."
    ),
    'regression': (
        "Ordinary Least-Squares (OLS) Linear & Polynomial Regression (C Engine)",
        "(Xᵀ X) β = Xᵀ y   |   min_β S_r = Σ_{i=1}^n (y_i - ŷ_i)²   |   R² = 1 - S_r / S_t",
        "Fits noisy trend data without forcing the curve through every point by solving the Normal Equations in C."
    ),
}


class InterpolationTab(tk.Frame):
    """Unit 5 — Interpolation (Newton, Lagrange, Coefficients, Inverse) & Unit 3 Least-Squares Regression (C Engine)."""
    def __init__(self, parent, go_home_callback):
        super().__init__(parent, bg=COLORS.bg_root)
        self.go_home_callback = go_home_callback
        self._working_steps = []
        self._build_ui()

    def _build_ui(self):
        wrapper = tk.Frame(self, bg=COLORS.bg_root)
        wrapper.pack(fill=tk.BOTH, expand=True, padx=24, pady=10)

        left_col = tk.Frame(wrapper, bg=COLORS.bg_root, width=400)
        left_col.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 20), pady=5)

        nav_row = tk.Frame(left_col, bg=COLORS.bg_root)
        nav_row.pack(fill=tk.X, pady=(0, 8))
        IconButton(nav_row, '← Back to Dashboard', command=self.go_home_callback, font=FONTS.SUBHEADING).pack(side=tk.LEFT)

        SectionLabel(left_col, 'Unit 5 & 3: Interpolation & Regression (C)', accent='cyan').pack(anchor='w')

        card = tk.Frame(left_col, bg=COLORS.bg_card, padx=22, pady=16, highlightthickness=1, highlightbackground=COLORS.border)
        card.pack(pady=8, fill=tk.X)

        tk.Label(card, text="Method / Mode (C Engine)", font=FONTS.SUBHEADING, bg=COLORS.bg_card, fg=COLORS.accent_cyan).pack(anchor='w', pady=(0, 4))
        self.method_var = tk.StringVar(value='newton_dd')
        for text, val in [
            ("Newton's Divided-Difference Table", 'newton_dd'),
            ("Lagrange Basis Polynomials L_i(x)", 'lagrange'),
            ("Power-Basis Coefficients & Vandermonde", 'coeffs'),
            ("Inverse Interpolation (Find x for y*)", 'inverse'),
            ("Least-Squares Regression (Linear / Poly)", 'regression'),
        ]:
            tk.Radiobutton(
                card, text=text, variable=self.method_var, value=val,
                bg=COLORS.bg_card, fg=COLORS.text_secondary, selectcolor=COLORS.bg_panel,
                font=FONTS.BODY, activebackground=COLORS.bg_card,
                activeforeground=COLORS.accent_cyan, command=self._compute_and_plot
            ).pack(anchor='w', pady=2)

        tk.Frame(card, height=1, bg=COLORS.border).pack(fill=tk.X, pady=8)

        tk.Label(card, text="Dataset Presets:", font=FONTS.SMALL, bg=COLORS.bg_card, fg=COLORS.text_muted).pack(anchor='w', pady=(0, 4))
        p_row = tk.Frame(card, bg=COLORS.bg_card)
        p_row.pack(fill=tk.X, pady=(0, 8))
        ChipButton(p_row, "Quadratic (x²+1)", command=lambda: self._load_preset('quad'), bg=COLORS.bg_panel).pack(side=tk.LEFT, padx=2)
        ChipButton(p_row, "4-Point Cubic", command=lambda: self._load_preset('cubic'), bg=COLORS.bg_panel).pack(side=tk.LEFT, padx=2)
        ChipButton(p_row, "Linear Data", command=lambda: self._load_preset('linear'), bg=COLORS.bg_panel).pack(side=tk.LEFT, padx=2)
        ChipButton(p_row, "Runge Equi.", command=lambda: self._load_preset('runge'), bg=COLORS.bg_panel).pack(side=tk.LEFT, padx=2)
        ChipButton(p_row, "Chebyshev Nodes", command=lambda: self._load_preset('chebyshev'), accent=COLORS.accent_cyan, bg=COLORS.bg_panel).pack(side=tk.LEFT, padx=2)

        tk.Label(card, text="Node x-coordinates (comma-separated):", bg=COLORS.bg_card, fg=COLORS.text_secondary, font=FONTS.SUBHEADING).pack(anchor='w', pady=(0, 2))
        self.entry_xs = PremiumEntry(card, width=30, default='0, 1, 2, 3')
        self.entry_xs.pack(fill=tk.X, pady=(0, 8))

        tk.Label(card, text="Node y-coordinates (comma-separated):", bg=COLORS.bg_card, fg=COLORS.text_secondary, font=FONTS.SUBHEADING).pack(anchor='w', pady=(0, 2))
        self.entry_ys = PremiumEntry(card, width=30, default='1, 2, 5, 10')
        self.entry_ys.pack(fill=tk.X, pady=(0, 8))

        q_row = tk.Frame(card, bg=COLORS.bg_card)
        q_row.pack(fill=tk.X)
        q_left = tk.Frame(q_row, bg=COLORS.bg_card)
        q_left.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        tk.Label(q_left, text="Query x* (or target y*):", bg=COLORS.bg_card, fg=COLORS.text_secondary, font=FONTS.SMALL).pack(anchor='w')
        self.entry_query = PremiumEntry(q_left, width=12, default='1.5')
        self.entry_query.pack(fill=tk.X)

        q_right = tk.Frame(q_row, bg=COLORS.bg_card)
        q_right.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))
        tk.Label(q_right, text="Regression Degree d:", bg=COLORS.bg_card, fg=COLORS.text_secondary, font=FONTS.SMALL).pack(anchor='w')
        self.entry_deg = PremiumEntry(q_right, width=10, default='1')
        self.entry_deg.pack(fill=tk.X)

        GlowButton(left_col, text='▶ CONSTRUCT POLYNOMIAL (C ENGINE)', command=self._compute_and_plot, width=340, height=50, bg=COLORS.bg_root).pack(pady=(10, 0))

        # Right column
        right_col = tk.Frame(wrapper, bg=COLORS.bg_root)
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)

        stats_row = tk.Frame(right_col, bg=COLORS.bg_root)
        stats_row.pack(fill=tk.X, pady=(0, 6))
        self.stat_eval = StatCard(stats_row, "Evaluated P(x*) / x(y*)", COLORS.accent_cyan)
        self.stat_eval.pack(side=tk.LEFT, padx=(0, 6))
        self.stat_deg = StatCard(stats_row, "Polynomial Degree", COLORS.accent_amber)
        self.stat_deg.pack(side=tk.LEFT, padx=6)
        self.stat_fit = StatCard(stats_row, "Fit Metric (SSE / Cond)", COLORS.accent_green)
        self.stat_fit.pack(side=tk.LEFT, padx=6)
        self.stat_r2 = StatCard(stats_row, "R² / Std Error", COLORS.accent_purple)
        self.stat_r2.pack(side=tk.LEFT, padx=6)

        self.method_banner = MethodBanner(right_col, on_show_steps=self._show_working_steps)
        self.method_banner.pack(fill=tk.X, pady=(0, 6))

        self.lbl_poly = tk.Label(
            right_col,
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
        self.lbl_poly.pack(fill=tk.X, pady=(0, 8))

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

        self.tree = ttk.Treeview(table_card, columns=('c1', 'c2', 'c3', 'c4'), show='headings', height=20)
        for col, head, w in zip(('c1', 'c2', 'c3', 'c4'), ('Node / Term', 'x_i / Basis', 'y_i / Coeff', 'Div. Diff / Residual'), (85, 90, 95, 115)):
            self.tree.heading(col, text=head)
            self.tree.column(col, width=w, anchor='center')
        self.tree.pack(fill=tk.Y, expand=True)

        self._compute_and_plot()

    def _load_preset(self, name):
        if name == 'quad':
            self.entry_xs.set('0, 1, 2')
            self.entry_ys.set('1, 2, 5')
            self.entry_query.set('1.5')
        elif name == 'cubic':
            self.entry_xs.set('0, 1, 2, 3')
            self.entry_ys.set('1, 2, 9, 28')
            self.entry_query.set('1.5')
        elif name == 'linear':
            self.method_var.set('regression')
            self.entry_xs.set('0, 1, 2, 3, 4')
            self.entry_ys.set('1.1, 2.9, 5.2, 6.8, 9.1')
            self.entry_query.set('2.5')
            self.entry_deg.set('1')
        elif name == 'runge':
            self.method_var.set('newton_dd')
            self.entry_xs.set('-3, -2, -1, 0, 1, 2, 3')
            self.entry_ys.set('0.1, 0.2, 0.5, 1.0, 0.5, 0.2, 0.1')
            self.entry_query.set('2.5')
        elif name == 'chebyshev':
            self.method_var.set('newton_dd')
            self.entry_xs.set('-2.898, -2.121, -0.776, 0.776, 2.121, 2.898')
            self.entry_ys.set('0.106, 0.182, 0.624, 0.624, 0.182, 0.106')
            self.entry_query.set('2.5')
        self._compute_and_plot()

    def _compute_and_plot(self):
        m = self.method_var.get()
        title, eq_s, desc_s = INTERP_METHOD_INFO.get(m, ("Interpolation", "", ""))
        self.method_banner.set_method(title, eq_s, desc_s)
        self._working_steps = []
        try:
            xs = [float(v.strip()) for v in self.entry_xs.get().split(',') if v.strip()]
            ys = [float(v.strip()) for v in self.entry_ys.get().split(',') if v.strip()]
            q_val = float(self.entry_query.get())
            reg_deg = max(1, int(self.entry_deg.get()))
        except Exception:
            messagebox.showwarning("Invalid Data", "Please enter comma-separated numbers for x and y, and a valid query value.")
            return

        if len(xs) != len(ys) or len(xs) < 2:
            messagebox.showwarning("Node Mismatch", "Provide at least 2 (x_i, y_i) points with equal lengths.")
            return

        # Sort pairs by x
        pairs = sorted(zip(xs, ys), key=lambda pair: pair[0])
        xs = [p[0] for p in pairs]
        ys = [p[1] for p in pairs]
        n = len(xs)

        m = self.method_var.get()
        c_mode = {
            'newton_dd': 'newton',
            'lagrange': 'lagrange',
            'coeffs': 'power',
            'inverse': 'inverse',
            'regression': 'ols'
        }.get(m, 'newton')

        interleaved = []
        for xv, yv in zip(xs, ys):
            interleaved.extend([xv, yv])

        try:
            lines = run_numlab_engine(["interp", c_mode, q_val, reg_deg, n, *interleaved])
        except Exception as ex:
            messagebox.showerror("C Interpolation Engine Error", str(ex))
            return

        dd_top = []
        lagrange_rows = []
        power_coeffs = []
        inv_rows = []
        ols_coeffs = []
        ols_rows = []
        curve_x, curve_y_int, curve_y_ols = [], [], []
        basis_curves = [[] for _ in range(n)]
        y_interp_q, y_ols_q, x_inv_q, cond_v, r2, sr, syx = 0.0, 0.0, float('nan'), 1.0, 1.0, 0.0, 0.0

        for line in lines:
            p = line.split(',')
            if p[0] == 'DD_ROW' and len(p) >= 4:
                row_idx = int(p[1])
                vals = [safe_float(v) for v in p[3:]]
                if row_idx == 0:
                    dd_top = vals
            elif p[0] == 'LAGRANGE_ROW' and len(p) >= 6:
                lagrange_rows.append((int(p[1]), safe_float(p[2]), safe_float(p[3]), safe_float(p[4]), safe_float(p[5])))
            elif p[0] == 'POWER_ROW' and len(p) >= 3:
                power_coeffs.append(safe_float(p[2]))
            elif p[0] == 'INV_ROW' and len(p) >= 5:
                inv_rows.append((int(p[1]), safe_float(p[2]), safe_float(p[3]), safe_float(p[4])))
            elif p[0] == 'OLS_COEFFS' and len(p) >= 3:
                ols_coeffs = [safe_float(v) for v in p[2:]]
            elif p[0] == 'OLS_ROW' and len(p) >= 7:
                ols_rows.append((int(p[1]), safe_float(p[2]), safe_float(p[3]), safe_float(p[4]), safe_float(p[5]), safe_float(p[6])))
            elif p[0] == 'SUMMARY' and len(p) >= 8:
                y_interp_q = safe_float(p[1])
                y_ols_q = safe_float(p[2])
                x_inv_q = safe_float(p[3])
                cond_v = safe_float(p[4])
                r2 = safe_float(p[5])
                sr = safe_float(p[6])
                syx = safe_float(p[7])
            elif p[0] == 'CURVE' and len(p) >= 4:
                curve_x.append(safe_float(p[1]))
                curve_y_int.append(safe_float(p[2]))
                curve_y_ols.append(safe_float(p[3]))
                if c_mode == 'lagrange' and len(p) >= 4 + n:
                    for i in range(n):
                        basis_curves[i].append(safe_float(p[4 + i]))

        self.ax.clear()
        self.ax.set_facecolor(COLORS.plot_axes)
        self.ax.grid(True, color=COLORS.plot_grid, linestyle='--', alpha=0.35)
        self.tree.delete(*self.tree.get_children())

        if m == 'regression':
            deg = min(reg_deg, n - 1)
            self.ax.plot(curve_x, curve_y_ols, color=COLORS.accent_cyan, lw=2.4, label=f'C Engine OLS Fit (deg {deg})')
            for idx_pt, xv, yv, yhat, res, _ in ols_rows:
                self.ax.plot([xv, xv], [yv, yhat], color=COLORS.accent_red, ls='--', lw=1.3)
                self.tree.insert('', 'end', values=(f"Pt {idx_pt}", f"{xv:.4g}", f"{yv:.4g}", f"e={res:+.4f}"))
            self.ax.scatter(xs, ys, color=COLORS.accent_amber, s=60, zorder=5, label='Observed Data (x_i, y_i)')
            self.ax.scatter([q_val], [y_ols_q], color=COLORS.accent_green, s=75, marker='D', zorder=6, label=f'Query ({q_val:g}, {y_ols_q:.4f})')

            terms = [f"{c:+.4g}x^{i}" if i > 1 else (f"{c:+.4g}x" if i == 1 else f"{c:+.4g}") for i, c in enumerate(ols_coeffs)]
            self.lbl_poly.config(text="C Engine Normal Equations Fit:  y(x) = " + " ".join(terms))
            self.stat_eval.set(f"{y_ols_q:.6f}")
            self.stat_deg.set(f"Degree {deg}")
            self.stat_fit.set(f"SSE = {sr:.3e}")
            self.stat_r2.set(f"R² = {r2:.5f} (sy/x={syx:.3g})")
            self._working_steps.append(f"Fitted OLS Model (Degree {deg}):  y(x) = " + " ".join(terms))
            self._working_steps.append(f"Evaluated at x* = {q_val:g}:  ŷ({q_val:g}) = {y_ols_q:.8f}   (SSE = {sr:.5e}, R² = {r2:.6f}, s_y/x = {syx:.5g})")
            for idx_pt, xv, yv, yhat, res, res2 in ols_rows:
                self._working_steps.append(f"Node {idx_pt}:  x={xv:g}, y={yv:g}  ⇒  ŷ={yhat:.6f},  residual e_i = y_i - ŷ_i = {res:+.6f}  (e_i² = {res2:.4e})")
        else:
            if m == 'lagrange':
                for i in range(n):
                    if basis_curves[i]:
                        weighted = [ys[i] * lv for lv in basis_curves[i]]
                        self.ax.plot(curve_x, weighted, ls=':', lw=1.3, alpha=0.65, label=f'y_{i}·L_{i}(x)')
                for idx_pt, xv, yv, li_v, term_v in lagrange_rows:
                    self.tree.insert('', 'end', values=(f"L_{idx_pt}(x*)", f"L={li_v:.4f}", f"y={yv:g}", f"y·L={term_v:.5f}"))
                    self._working_steps.append(f"Basis i={idx_pt} (x_{idx_pt}={xv:g}, y_{idx_pt}={yv:g}):  L_{idx_pt}({q_val:g}) = {li_v:.6f}  ⇒  y_{idx_pt}·L_{idx_pt}({q_val:g}) = {term_v:+.6f}")
                self._working_steps.append(f"Sum Σ y_i L_i({q_val:g}) = P_{n-1}({q_val:g}) = {y_interp_q:.8f}")
            elif m == 'coeffs':
                for i, c in enumerate(power_coeffs):
                    dd_v = dd_top[i] if i < len(dd_top) else 0.0
                    self.tree.insert('', 'end', values=(f"a_{i} (x^{i})", f"deg {i}", f"{c:.6g}", f"b_{i}={dd_v:.5g}"))
                    self._working_steps.append(f"Term x^{i}:  Power Coefficient c_{i} = {c:.8g}   |   Newton Divided-Diff b_{i} = {dd_v:.8g}")
                self._working_steps.append(f"Vandermonde Condition Number κ_∞(V) = {cond_v:.4e}")
            elif m == 'inverse':
                for idx_pt, yv, xv, inv_b in inv_rows:
                    self.tree.insert('', 'end', values=(f"Node {idx_pt}", f"y={yv:.4g}", f"x={xv:.4g}", f"f⁻¹[..]={inv_b:.5g}"))
                    self._working_steps.append(f"Swapped Node {idx_pt}:  (y_{idx_pt}={yv:g}, x_{idx_pt}={xv:g})  ⇒  Inverse Divided Diff = {inv_b:.8g}")
                self._working_steps.append(f"Evaluated Inverse Interpolant at y* = {q_val:g}:  x* ≈ {x_inv_q:.8f}")
            else:
                for i in range(n):
                    dd_v = dd_top[i] if i < len(dd_top) else 0.0
                    self.tree.insert('', 'end', values=(f"Node {i}", f"{xs[i]:.4g}", f"{ys[i]:.4g}", f"f[x0..x{i}]={dd_v:.5g}"))
                    self._working_steps.append(f"Order {i} Top Divided Difference f[x0..x{i}] = {dd_v:.8g}   (Node x_{i}={xs[i]:g}, y_{i}={ys[i]:g})")
                self._working_steps.append(f"Nested Newton Evaluation at x* = {q_val:g}:  P_{n-1}({q_val:g}) = {y_interp_q:.8f}")

            self.ax.plot(curve_x, curve_y_int, color=COLORS.accent_cyan, lw=2.4, label=f'C Engine Interpolant P_{n-1}(x)')
            self.ax.scatter(xs, ys, color=COLORS.accent_amber, s=60, zorder=5, label='Interpolation Nodes')

            if m == 'inverse':
                y_target = q_val
                self.ax.axhline(y_target, color=COLORS.accent_red, ls='--', lw=1.6, label=f'Target y* = {y_target:g}')
                if not math.isnan(x_inv_q):
                    self.ax.scatter([x_inv_q], [y_target], color=COLORS.accent_green, s=75, marker='D', zorder=6, label=f'Inverse x* ≈ {x_inv_q:.5f}')
                    self.stat_eval.set(f"x ≈ {x_inv_q:.6f}")
                else:
                    self.stat_eval.set("Non-Invertible y_i")
            else:
                self.ax.scatter([q_val], [y_interp_q], color=COLORS.accent_green, s=75, marker='D', zorder=6, label=f'P({q_val:g}) = {y_interp_q:.4f}')
                if q_val < xs[0] or q_val > xs[-1]:
                    self.ax.axvspan(min(q_val, xs[0]), xs[0], color=COLORS.accent_red, alpha=0.08)
                    self.ax.axvspan(xs[-1], max(q_val, xs[-1]), color=COLORS.accent_red, alpha=0.08, label='Extrapolation Zone')
                self.stat_eval.set(f"{y_interp_q:.6f}")

            terms = [f"{c:+.4g}x^{i}" if i > 1 else (f"{c:+.4g}x" if i == 1 else f"{c:+.4g}") for i, c in enumerate(power_coeffs)]
            self.lbl_poly.config(text=f"C Engine P_{n-1}(x) = " + " ".join(terms))
            self.stat_deg.set(f"Degree {n - 1}")
            self.stat_fit.set(f"κ∞(V) = {cond_v:.2e}")
            self.stat_r2.set(f"R²(OLS) = {r2:.4f}")

        self.ax.set_xlabel('x', color=COLORS.text_secondary)
        self.ax.set_ylabel('y', color=COLORS.text_secondary)
        self.ax.legend(loc='best', facecolor=COLORS.bg_panel, edgecolor=COLORS.border, labelcolor=COLORS.text_primary, fontsize=8)
        self.canvas.draw_idle()

    def handle_keypress(self, event):
        pass

    def _show_working_steps(self):
        m = self.method_var.get()
        title, eq_s, desc_s = INTERP_METHOD_INFO.get(m, ("Interpolation", "", ""))
        show_working_steps_modal(self, title, eq_s, desc_s, self._working_steps)

    def get_state(self):
        return {
            'method': self.method_var.get(),
            'xs': self.entry_xs.get(),
            'ys': self.entry_ys.get(),
            'query': self.entry_query.get(),
            'deg': self.entry_deg.get(),
        }

    def set_state(self, state):
        if not state:
            return
        self.method_var.set(state.get('method', 'newton_dd'))
        self.entry_xs.set(state.get('xs', '0, 1, 2, 3'))
        self.entry_ys.set(state.get('ys', '1, 2, 5, 10'))
        self.entry_query.set(state.get('query', '1.5'))
        self.entry_deg.set(state.get('deg', '1'))
        self._compute_and_plot()
