import math
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from config import COLORS, FONTS, safe_float
from c_bridge import run_numlab_engine
from widgets import GlowButton, IconButton, PremiumEntry, SectionLabel, StatCard, ChipButton, MethodBanner, show_working_steps_modal


QUAD_METHOD_INFO = {
    'trapezoidal': (
        "Composite Trapezoidal Rule (C Engine)",
        "I ≈ (h / 2) [f(x_0) + 2 Σ_{i=1}^{n-1} f(x_i) + f(x_n)]   where h = (b - a) / n",
        "Approximates f(x) on each subinterval by a straight-line trapezoid; global truncation error is O(h²)."
    ),
    'simpson13': (
        "Composite Simpson's 1/3 Rule (C Engine)",
        "I ≈ (h / 3) [f(x_0) + 4 Σ_{i odd} f(x_i) + 2 Σ_{i even} f(x_i) + f(x_n)]   (n even)",
        "Fits quadratic parabolas across pairs of subintervals (weights 1-4-2-4...-4-1); exact for cubics with global error O(h⁴)."
    ),
    'simpson38': (
        "Composite Simpson's 3/8 Rule (C Engine)",
        "I ≈ (3h / 8) [f(x_0) + 3f(x_1) + 3f(x_2) + 2f(x_3) + ... + f(x_n)]   (n divisible by 3)",
        "Fits cubic polynomials across triples of subintervals (weights 1-3-3-2...-3-3-1); global truncation error is O(h⁴)."
    ),
    'boole': (
        "Newton-Cotes 5-Point Boole's Rule (C Engine)",
        "I ≈ (2h / 45) [7f_0 + 32f_1 + 12f_2 + 32f_3 + 14f_4 + ... + 7f_n]   (n divisible by 4)",
        "Closed 4th-degree Newton-Cotes quadrature rule across groups of 4 panels; achieves O(h⁶) global accuracy."
    ),
    'romberg': (
        "Romberg Integration & Richardson Extrapolation Tableau (C Engine)",
        "R(k, j) = [4^j R(k, j-1) - R(k-1, j-1)] / (4^j - 1)   for j = 1..k",
        "Combines successive halved-step Trapezoidal estimates R(k, 0) to systematically cancel leading even powers of h."
    ),
    'gauss': (
        "Gauss-Legendre Quadrature (C Engine)",
        "∫_a^b f(x) dx ≈ ((b - a)/2) Σ_{i=1}^n w_i f(((b - a)/2) t_i + (a + b)/2)",
        "Samples optimal interior roots t_i of Legendre polynomials P_n(t) on [-1, 1]; n points integrate polynomials of degree ≤ 2n-1 exactly."
    ),
}


class IntegrationTab(tk.Frame):
    """Unit 6A — Numerical Integration & Quadrature Lab (C Engine)."""
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

        SectionLabel(left_col, 'Unit 6A: Numerical Integration (C)', accent='amber').pack(anchor='w')

        card = tk.Frame(left_col, bg=COLORS.bg_card, padx=22, pady=16, highlightthickness=1, highlightbackground=COLORS.border)
        card.pack(pady=8, fill=tk.X)

        tk.Label(card, text="Quadrature Method (C Engine)", font=FONTS.SUBHEADING, bg=COLORS.bg_card, fg=COLORS.accent_cyan).pack(anchor='w', pady=(0, 4))
        self.method_var = tk.StringVar(value='simpson13')
        for text, val in [
            ("Composite Trapezoidal Rule", 'trapezoidal'),
            ("Composite Simpson's 1/3 Rule (n even)", 'simpson13'),
            ("Composite Simpson's 3/8 Rule (n mult of 3)", 'simpson38'),
            ("Newton-Cotes Boole's Rule (n mult of 4)", 'boole'),
            ("Romberg Integration (Richardson Tableau)", 'romberg'),
            ("Gauss-Legendre Quadrature (2–5 pts)", 'gauss'),
        ]:
            tk.Radiobutton(
                card, text=text, variable=self.method_var, value=val,
                bg=COLORS.bg_card, fg=COLORS.text_secondary, selectcolor=COLORS.bg_panel,
                font=FONTS.BODY, activebackground=COLORS.bg_card,
                activeforeground=COLORS.accent_cyan, command=self._run_quadrature
            ).pack(anchor='w', pady=2)

        tk.Frame(card, height=1, bg=COLORS.border).pack(fill=tk.X, pady=8)

        tk.Label(card, text="Presets:", font=FONTS.SMALL, bg=COLORS.bg_card, fg=COLORS.text_muted).pack(anchor='w', pady=(0, 4))
        p_row = tk.Frame(card, bg=COLORS.bg_card)
        p_row.pack(fill=tk.X, pady=(0, 8))
        ChipButton(p_row, "∫ x² [0,1]", command=lambda: self._load_preset("x^2", "0", "1", "6"), bg=COLORS.bg_panel).pack(side=tk.LEFT, padx=2)
        ChipButton(p_row, "∫ sin(x) [0,π]", command=lambda: self._load_preset("sin(x)", "0", "3.141592653589793", "6"), bg=COLORS.bg_panel).pack(side=tk.LEFT, padx=2)
        ChipButton(p_row, "∫ exp(-x²) [0,2]", command=lambda: self._load_preset("exp(-x^2)", "0", "2", "6"), bg=COLORS.bg_panel).pack(side=tk.LEFT, padx=2)
        ChipButton(p_row, "∫ 1/(1+x) [0,3]", command=lambda: self._load_preset("1/(1+x)", "0", "3", "6"), bg=COLORS.bg_panel).pack(side=tk.LEFT, padx=2)

        tk.Label(card, text="Integrand f(x):", bg=COLORS.bg_card, fg=COLORS.text_secondary, font=FONTS.SUBHEADING).pack(anchor='w', pady=(0, 2))
        self.entry_eq = PremiumEntry(card, width=30, default='sin(x)')
        self.entry_eq.pack(fill=tk.X, pady=(0, 8))

        bounds_row = tk.Frame(card, bg=COLORS.bg_card)
        bounds_row.pack(fill=tk.X, pady=(0, 8))
        b_left = tk.Frame(bounds_row, bg=COLORS.bg_card)
        b_left.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        tk.Label(b_left, text="Lower Limit a:", bg=COLORS.bg_card, fg=COLORS.text_secondary, font=FONTS.SMALL).pack(anchor='w')
        self.entry_a = PremiumEntry(b_left, width=12, default='0')
        self.entry_a.pack(fill=tk.X)

        b_right = tk.Frame(bounds_row, bg=COLORS.bg_card)
        b_right.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))
        tk.Label(b_right, text="Upper Limit b:", bg=COLORS.bg_card, fg=COLORS.text_secondary, font=FONTS.SMALL).pack(anchor='w')
        self.entry_b = PremiumEntry(b_right, width=12, default='3.141592653589793')
        self.entry_b.pack(fill=tk.X)

        tk.Label(card, text="Subintervals n (or Gauss Nodes 2–5):", bg=COLORS.bg_card, fg=COLORS.text_secondary, font=FONTS.SMALL).pack(anchor='w', pady=(0, 2))
        self.entry_n = PremiumEntry(card, width=30, default='6')
        self.entry_n.pack(fill=tk.X)

        GlowButton(left_col, text='▶ INTEGRATE f(x) dx (C ENGINE)', command=self._run_quadrature, accent='amber', width=340, height=50, bg=COLORS.bg_root).pack(pady=(10, 0))

        # Right column
        right_col = tk.Frame(wrapper, bg=COLORS.bg_root)
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)

        stats_row = tk.Frame(right_col, bg=COLORS.bg_root)
        stats_row.pack(fill=tk.X, pady=(0, 6))
        self.stat_est = StatCard(stats_row, "Quadrature Estimate I", COLORS.accent_cyan)
        self.stat_est.pack(side=tk.LEFT, padx=(0, 6))
        self.stat_ref = StatCard(stats_row, "High-Res Reference I*", COLORS.accent_green)
        self.stat_ref.pack(side=tk.LEFT, padx=6)
        self.stat_err = StatCard(stats_row, "Absolute Error |I* - I|", COLORS.accent_amber)
        self.stat_err.pack(side=tk.LEFT, padx=6)
        self.stat_h = StatCard(stats_row, "Step Width h / Nodes", COLORS.accent_purple)
        self.stat_h.pack(side=tk.LEFT, padx=6)

        self.method_banner = MethodBanner(right_col, on_show_steps=self._show_working_steps)
        self.method_banner.pack(fill=tk.X, pady=(0, 6))

        self.lbl_formula = tk.Label(
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
        self.lbl_formula.pack(fill=tk.X, pady=(0, 8))

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
        for col, head, w in zip(('c1', 'c2', 'c3', 'c4'), ('Idx / Level', 'x_i / h', 'f(x_i) / R(k,0)', 'Weight·f / Extrap'), (75, 95, 105, 115)):
            self.tree.heading(col, text=head)
            self.tree.column(col, width=w, anchor='center')
        self.tree.pack(fill=tk.Y, expand=True)

        self._run_quadrature()

    def _load_preset(self, eq, a, b, n):
        self.entry_eq.set(eq)
        self.entry_a.set(a)
        self.entry_b.set(b)
        self.entry_n.set(n)
        self._run_quadrature()

    @staticmethod
    def _parse_bound(txt):
        s = str(txt).strip().lower()
        if s == 'pi':
            return 3.141592653589793
        if s == '-pi':
            return -3.141592653589793
        if s == 'e':
            return 2.718281828459045
        return float(s)

    def _run_quadrature(self):
        eq = self.entry_eq.get().strip()
        m = self.method_var.get()
        title, eq_s, desc_s = QUAD_METHOD_INFO.get(m, ("Quadrature", "", ""))
        self.method_banner.set_method(title, eq_s, desc_s)
        self._working_steps = []
        try:
            a = self._parse_bound(self.entry_a.get())
            b = self._parse_bound(self.entry_b.get())
            n = max(1, min(200, int(self.entry_n.get())))
        except Exception:
            messagebox.showwarning("Invalid Inputs", "Please provide valid numeric limits [a, b] and integer subinterval count n.")
            return

        c_method = {
            'trapezoidal': 'trap',
            'simpson13': 'simp13',
            'simpson38': 'simp38',
            'boole': 'boole',
            'romberg': 'romberg',
            'gauss': 'gauss'
        }.get(m, 'simp13')

        try:
            lines = run_numlab_engine(["quad", c_method, eq, a, b, n])
        except Exception as ex:
            messagebox.showerror("C Quadrature Engine Error", str(ex))
            return

        nodes = []
        romberg_rows = []
        xs_curve, ys_curve = [], []
        est, ref_val, abs_err, rel_pct, n_used = 0.0, 0.0, 0.0, 0.0, n
        note = ""

        for line in lines:
            p = line.split(',')
            if p[0] == 'NODE' and len(p) >= 6:
                nodes.append((int(p[1]), safe_float(p[2]), safe_float(p[3]), safe_float(p[4]), safe_float(p[5])))
            elif p[0] == 'ROMBERG_ROW' and len(p) >= 4:
                lvl = int(p[1])
                sub_n = int(p[2])
                r_vals = [safe_float(v) for v in p[3:]]
                romberg_rows.append((lvl, sub_n, r_vals))
            elif p[0] == 'SUMMARY' and len(p) >= 6:
                est = safe_float(p[1])
                ref_val = safe_float(p[2])
                abs_err = safe_float(p[3])
                rel_pct = safe_float(p[4])
                n_used = int(p[5])
                note = p[6] if len(p) >= 7 else ""
            elif p[0] == 'CURVE' and len(p) >= 3:
                xs_curve.append(safe_float(p[1]))
                ys_curve.append(safe_float(p[2]))

        if n_used != n and m in ('simpson13', 'simpson38', 'boole'):
            self.entry_n.set(str(n_used))

        self.ax.clear()
        self.ax.set_facecolor(COLORS.plot_axes)
        self.ax.grid(True, color=COLORS.plot_grid, linestyle='--', alpha=0.35)
        self.tree.delete(*self.tree.get_children())

        self.ax.plot(xs_curve, ys_curve, color=COLORS.accent_cyan, lw=2.4, label='f(x) (C Engine)')
        self.ax.axhline(0, color=COLORS.plot_zero, lw=1.2)

        x_nodes = [nd[1] for nd in nodes]
        y_nodes = [nd[2] for nd in nodes]

        if m == 'romberg':
            for lvl, sub_n, r_vals in romberg_rows:
                hk = (b - a) / sub_n
                rk0 = r_vals[0]
                rkk = r_vals[lvl] if lvl < len(r_vals) else rk0
                self.tree.insert('', 'end', values=(f"k={lvl} (n={sub_n})", f"h={hk:.4f}", f"R({lvl},0)={rk0:.6f}", f"R({lvl},{lvl})={rkk:.7f}"))
                row_s = ",  ".join(f"R({lvl},{j})={r_vals[j]:.8f}" for j in range(lvl + 1) if j < len(r_vals))
                self._working_steps.append(f"Level k={lvl} (n={sub_n}, h={hk:.5g}):  {row_s}")
            self.ax.fill_between(xs_curve, 0, ys_curve, color=COLORS.accent_cyan, alpha=0.15, label='Romberg Extrapolated Area')
            formula_str = f"C Engine Romberg R(k,j) = [4^j R(k,j-1) - R(k-1,j-1)] / (4^j - 1)   (εt = {rel_pct:.3e}%)"
            self.stat_h.set(f"{len(romberg_rows)} Levels")
        elif m == 'gauss':
            for idx_g, xv, yv, wv, contrib in nodes:
                self.tree.insert('', 'end', values=(f"Node {idx_g+1}", f"x={xv:.5f}", f"f(x)={yv:.5f}", f"w={wv:.4f} → {contrib:.5f}"))
                self.ax.plot([xv, xv], [0, yv], color=COLORS.accent_amber, lw=2, ls='--')
                self._working_steps.append(f"Gauss Node {idx_g+1}:  x_{idx_g+1} = {xv:.8f},  f(x_{idx_g+1}) = {yv:.8f},  scaled weight w = {wv:.8f}  ⇒  w·f = {contrib:+.8f}")
            self.ax.fill_between(xs_curve, 0, ys_curve, color=COLORS.accent_green, alpha=0.14)
            self.ax.scatter(x_nodes, y_nodes, color=COLORS.accent_amber, s=65, zorder=5, label=f'Gauss-Legendre ({n_used} interior nodes)')
            formula_str = f"C Engine Gauss-Legendre ({n_used}-pt): exact for polynomials up to degree {2*n_used - 1}"
            self.stat_h.set(f"{n_used} Gauss Pts")
        else:
            h = (b - a) / max(1, n_used)
            for idx_n, xv, yv, wv, contrib in nodes:
                self.tree.insert('', 'end', values=(f"i={idx_n}", f"{xv:.5f}", f"{yv:.5f}", f"w={wv:.4f} → {contrib:.5f}"))
                self._working_steps.append(f"Node i={idx_n}:  x_{idx_n} = {xv:.6f},  f(x_{idx_n}) = {yv:.8f},  quadrature weight w_{idx_n} = {wv:.6f}  ⇒  w_{idx_n}·f(x_{idx_n}) = {contrib:+.8f}")
            for i in range(len(x_nodes) - 1):
                self.ax.fill_between([x_nodes[i], x_nodes[i + 1]], [0, 0], [y_nodes[i], y_nodes[i + 1]], color=COLORS.accent_amber, alpha=0.16, edgecolor=COLORS.accent_amber)
            self.ax.scatter(x_nodes, y_nodes, color=COLORS.accent_amber, s=45, zorder=5, label=f'{len(x_nodes)} Quadrature Nodes')
            note_sfx = f"  [{note}]" if note else ""
            formula_str = f"C Engine {m.upper()} Composite Quadrature: n = {n_used}, h = {h:.5g}{note_sfx}"
            self.stat_h.set(f"h = {h:.5f}")
        self._working_steps.append(f"Total Integral Estimate I = {est:.10f}   |   Reference I* = {ref_val:.10f}   |   |I* - I| = {abs_err:.4e} ({rel_pct:.4f}%)")

        self.stat_est.set(f"{est:.7f}")
        self.stat_ref.set(f"{ref_val:.7f}")
        self.stat_err.set(f"{abs_err:.3e}")
        self.lbl_formula.config(text=formula_str)

        self.ax.set_xlabel('x', color=COLORS.text_secondary)
        self.ax.set_ylabel('f(x)', color=COLORS.text_secondary)
        self.ax.legend(loc='best', facecolor=COLORS.bg_panel, edgecolor=COLORS.border, labelcolor=COLORS.text_primary)
        self.canvas.draw_idle()

    def handle_keypress(self, event):
        pass

    def _show_working_steps(self):
        m = self.method_var.get()
        title, eq_s, desc_s = QUAD_METHOD_INFO.get(m, ("Quadrature", "", ""))
        show_working_steps_modal(self, title, eq_s, desc_s, self._working_steps)

    def get_state(self):
        return {
            'method': self.method_var.get(),
            'eq': self.entry_eq.get(),
            'a': self.entry_a.get(),
            'b': self.entry_b.get(),
            'n': self.entry_n.get(),
        }

    def set_state(self, state):
        if not state:
            return
        self.method_var.set(state.get('method', 'simpson13'))
        self.entry_eq.set(state.get('eq', 'sin(x)'))
        self.entry_a.set(state.get('a', '0'))
        self.entry_b.set(state.get('b', '3.141592653589793'))
        self.entry_n.set(state.get('n', '6'))
        self._run_quadrature()
