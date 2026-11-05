import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from config import COLORS, FONTS, safe_float
from c_bridge import run_root_engine, run_matrix_engine, run_numlab_engine
from widgets import GlowButton, draw_rounded_rect, IconButton, ChipButton, PremiumEntry


class HomeTab(tk.Frame):
    def __init__(self, parent, notebook):
        super().__init__(parent, bg=COLORS.bg)
        self.notebook = notebook
        self._build_background()
        self._build_ui()

    def _build_background(self):
        self._bg_canvas = tk.Canvas(self, bg=COLORS.bg, highlightthickness=0)
        self._bg_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._bg_canvas.bind('<Configure>', self._draw_grid)

    def _draw_grid(self, event=None):
        self._bg_canvas.delete('grid')
        w, h = self._bg_canvas.winfo_width(), self._bg_canvas.winfo_height()
        for x in range(0, w, 52):
            self._bg_canvas.create_line(x, 0, x, h, fill=COLORS.border, tags='grid')
        for y in range(0, h, 52):
            self._bg_canvas.create_line(0, y, w, y, fill=COLORS.border, tags='grid')
        self._bg_canvas.create_oval(-200, -200, 600, 600, fill=COLORS.bg, outline='', tags='grid')
        self._bg_canvas.create_oval(w - 400, h - 400, w + 300, h + 300, fill=COLORS.bg, outline='', tags='grid')

    def _build_ui(self):
        container = tk.Frame(self, bg=COLORS.bg)
        container.pack(expand=True, fill=tk.BOTH, padx=36, pady=12)

        header = tk.Frame(container, bg=COLORS.bg)
        header.pack(pady=(2, 4))

        chip = tk.Canvas(header, width=360, height=26, bg=COLORS.bg, highlightthickness=0)
        chip.pack()
        draw_rounded_rect(chip, 2, 2, 358, 24, 11, fill=COLORS.card_active, outline=COLORS.border_glow)
        chip.create_text(
            180, 13,
            text='✦  C-Powered Numerical Methods Learning Lab • All 6 Units  ✦',
            font=FONTS['body_small'],
            fill=COLORS.accent_cyan
        )

        tk.Label(
            header,
            text='Numerical Analysis Suite',
            font=FONTS['hero'],
            bg=COLORS.bg,
            fg=COLORS.text_primary
        ).pack(pady=(6, 2))

        tk.Label(
            header,
            text='Complete 6-Unit Interactive Curriculum: Errors, Roots, Matrices, Optimization, Interpolation, Integration & ODEs',
            font=FONTS['body_std'],
            bg=COLORS.bg,
            fg=COLORS.text_secondary
        ).pack(pady=(0, 4))

        div = tk.Canvas(container, height=2, bg=COLORS.bg, highlightthickness=0, width=520)
        div.pack(pady=(6, 12))
        div.create_line(0, 1, 210, 1, fill=COLORS.border_mid)
        div.create_line(210, 1, 260, 1, fill=COLORS.accent_cyan, width=2)
        div.create_line(260, 1, 310, 1, fill=COLORS.accent_amber, width=2)
        div.create_line(310, 1, 520, 1, fill=COLORS.border_mid)

        # Row 1: Primary Engines (Units 1, 2, 3)
        row1 = tk.Frame(container, bg=COLORS.bg)
        row1.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self._make_card(
            row1,
            '🔬',
            'Unit 1: Errors & Float Lab',
            [
                'Truncation vs. Round-Off U-Curve',
                'Taylor Polynomial Approximations',
                'Catastrophic Cancellation & IEEE-754'
            ],
            'Unit 1 • CLO 1',
            3,
            COLORS.accent_purple
        )
        tk.Frame(row1, width=16, bg=COLORS.bg).pack(side=tk.LEFT)

        self._make_card(
            row1,
            '📈',
            'Unit 2: Root Finding Engine',
            [
                '8 C-Powered Bracketing & Open Solvers',
                'Fixed-Point Cobweb & Live AST Preview',
                "Horner's Rule & Polynomial Root Lab"
            ],
            'Unit 2 • C Engine',
            1,
            COLORS.accent_cyan
        )
        tk.Frame(row1, width=16, bg=COLORS.bg).pack(side=tk.LEFT)

        self._make_card(
            row1,
            '🧮',
            'Unit 3: Linear Systems & Inverse',
            [
                'Gaussian, Gauss-Jordan, LU & Gauss-Seidel',
                'Animated Matrix Inversion [A | I] → [I | A⁻¹]',
                'Solution Vector & Residual ||Ax - b|| Check'
            ],
            'Unit 3 • C Engine',
            2,
            COLORS.accent_amber
        )

        # Row 2: Units 4, 5, 6A, 6B
        row2 = tk.Frame(container, bg=COLORS.bg)
        row2.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

        self._make_card(
            row2,
            '🎯',
            'Unit 4: Optimization',
            [
                '1D Golden-Section, Parabolic & Newton',
                '2D Contour Gradient Descent & Hessian',
                'Min / Max / Saddle Classification'
            ],
            'Unit 4 • CLO 1,2',
            4,
            COLORS.accent_green
        )
        tk.Frame(row2, width=14, bg=COLORS.bg).pack(side=tk.LEFT)

        self._make_card(
            row2,
            '📐',
            'Unit 5 & 3: Interp. & Regression',
            [
                'Newton Divided-Difference & Lagrange L_i(x)',
                'Power Coefficients & Inverse Interpolation',
                'Least-Squares Linear/Poly Curve Fitting'
            ],
            'Unit 5 & 3',
            5,
            COLORS.accent_cyan
        )
        tk.Frame(row2, width=14, bg=COLORS.bg).pack(side=tk.LEFT)

        self._make_card(
            row2,
            '∫',
            'Unit 6A: Quadrature',
            [
                "Trapezoidal, Simpson 1/3, 3/8 & Boole's",
                'Romberg Extrapolation Tableau',
                'Gauss-Legendre 2/3/4-Pt Quadrature'
            ],
            'Unit 6A • Integration',
            6,
            COLORS.accent_amber
        )
        tk.Frame(row2, width=14, bg=COLORS.bg).pack(side=tk.LEFT)

        self._make_card(
            row2,
            '⚡',
            'Unit 6B: ODE Solvers',
            [
                'Euler, Heun & Midpoint RK2 Trajectories',
                'Classical RK4 (k1..k4) & Slope Fields',
                'Coupled 2D ODE Systems & Phase Portrait'
            ],
            'Unit 6B • IVP & Systems',
            7,
            COLORS.accent_purple
        )

        footer = tk.Frame(container, bg=COLORS.bg)
        footer.pack(pady=(12, 2))
        tk.Label(
            footer,
            text='⌨  Use ← / → Arrow Keys or Spacebar to step through iterations   •   ',
            font=FONTS['body_small'],
            bg=COLORS.bg,
            fg=COLORS.text_muted
        ).pack(side=tk.LEFT)
        ChipButton(
            footer,
            text='⚖ Method Comparison Lab',
            command=self._show_comparison_lab,
            accent=COLORS.accent_amber,
            bg=COLORS.card
        ).pack(side=tk.LEFT, padx=5)
        ChipButton(
            footer,
            text='🎯 Practice & Self-Test Quiz',
            command=self._show_practice_quiz,
            accent=COLORS.accent_green,
            bg=COLORS.card
        ).pack(side=tk.LEFT, padx=5)
        ChipButton(
            footer,
            text='📚 Full Syllabus Formula Guide',
            command=self._show_formula_guide,
            accent=COLORS.accent_cyan,
            bg=COLORS.card
        ).pack(side=tk.LEFT, padx=5)
        ChipButton(
            footer,
            text='ℹ About Software',
            command=self._show_about,
            accent=COLORS.text_secondary,
            bg=COLORS.card
        ).pack(side=tk.LEFT, padx=5)

    def _make_card(self, parent, icon, title, lines, badge, target, accent):
        outer = tk.Frame(parent, bg=accent, padx=1, pady=1)
        outer.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        card = tk.Frame(outer, bg=COLORS.card, padx=18, pady=14)
        card.pack(fill=tk.BOTH, expand=True)

        tk.Frame(card, height=3, bg=accent).pack(fill=tk.X, pady=(0, 10))
        top_row = tk.Frame(card, bg=COLORS.card)
        top_row.pack(fill=tk.X)
        tk.Label(top_row, text=icon, font=('Segoe UI Emoji', 18), bg=COLORS.card, fg=accent).pack(side=tk.LEFT, padx=(0, 8))
        tk.Label(top_row, text=title, font=FONTS['subheading'], bg=COLORS.card, fg=accent).pack(side=tk.LEFT, anchor='w')

        badge_lbl = tk.Label(card, text=badge, font=FONTS['body_small'], bg=COLORS.bg_mid, fg=accent, padx=8, pady=2)
        badge_lbl.pack(anchor='w', pady=(6, 8))

        for ln in lines:
            row = tk.Frame(card, bg=COLORS.card)
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text='▸', font=FONTS['body_small'], bg=COLORS.card, fg=accent).pack(side=tk.LEFT, padx=(0, 6))
            tk.Label(row, text=ln, font=FONTS['body_small'], bg=COLORS.card, fg=COLORS.text_secondary, anchor='w').pack(side=tk.LEFT)

        btn_accent = 'cyan' if accent in (COLORS.accent_cyan, COLORS.accent_purple) else ('amber' if accent == COLORS.accent_amber else 'green')
        btn = GlowButton(
            card,
            text='Launch Module  →',
            command=lambda t=target: self.notebook.select(t),
            accent=btn_accent,
            width=185,
            height=36,
            bg=COLORS.card
        )
        btn.pack(side=tk.BOTTOM, pady=(10, 0))

    def _show_formula_guide(self):
        win = tk.Toplevel(self)
        win.title("Numerical Methods — Complete 6-Unit Formula & Syllabus Guide")
        win.geometry("780x580")
        win.configure(bg=COLORS.bg)
        win.transient(self.winfo_toplevel())

        hdr = tk.Frame(win, bg=COLORS.card, padx=24, pady=14, highlightthickness=1, highlightbackground=COLORS.border)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="📚 Complete 6-Unit Numerical Methods Formula & Syllabus Reference", font=FONTS['heading'], bg=COLORS.card, fg=COLORS.accent_cyan).pack(anchor='w')
        tk.Label(hdr, text="Covers all 6 course units: Error Analysis, Roots, Linear Systems, Optimization, Interpolation, Quadrature & ODEs.", font=FONTS['body_std'], bg=COLORS.card, fg=COLORS.text_secondary).pack(anchor='w', pady=(2, 0))

        body = tk.Frame(win, bg=COLORS.bg, padx=24, pady=14)
        body.pack(fill=tk.BOTH, expand=True)

        text_widget = tk.Text(
            body,
            bg=COLORS.card,
            fg=COLORS.text_primary,
            font=FONTS['body_std'],
            relief='flat',
            padx=18,
            pady=14,
            wrap=tk.WORD,
            highlightthickness=1,
            highlightbackground=COLORS.border
        )
        scroll = ttk.Scrollbar(body, orient='vertical', command=text_widget.yview)
        text_widget.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        text_widget.tag_configure('unit', font=FONTS['heading'], foreground=COLORS.accent_cyan, spacing1=10, spacing3=4)
        text_widget.tag_configure('sub', font=FONTS['subheading'], foreground=COLORS.accent_amber, spacing1=5, spacing3=2)
        text_widget.tag_configure('mono', font=FONTS['mono_small'], foreground=COLORS.accent_green)
        text_widget.tag_configure('body', font=FONTS['body_std'], foreground=COLORS.text_secondary)

        sections = [
            ("Unit 1 (CLO 1) — Numerical Approximations & Round-Off Errors", [
                ("True & Approximate Errors", "E_t = |x* - x_n|,   ε_a = |(x_n - x_{n-1}) / x_n| × 100%", "Distinguishes exact reference error from consecutive iterate change and equation residual |f(x_n)|."),
                ("Truncation vs. Round-Off Tradeoff", "f'(x) ≈ (f(x+h) - f(x-h)) / (2h) + O(h²)", "Decreasing h reduces Taylor truncation error until floating-point cancellation (~ε_mach / h) dominates."),
            ]),
            ("Unit 2 (CLO 2,3,4,5) — Roots of Equations & Polynomials", [
                ("Bracketing (Bisection, False Position, Brent)", "c = a + (b - a)/2   |   c = b - f(b)(b-a)/(f(b)-f(a))", "Requires continuous f(x) with sign change f(a)·f(b) < 0."),
                ("Open Methods (Newton, Mod. Newton, Secant, Fixed-Point)", "x_{n+1} = x_n - f(x_n)/f'(x_n)   |   x_{n+1} = g(x_n)", "Fast local convergence; Fixed-Point converges when |g'(x*)| < 1."),
                ("Polynomial Roots & Horner's Rule", "b_{k} = a_{k} + b_{k+1} x_0", "Evaluates P(x_0), P'(x_0), and deflated quotient Q(x) in O(n) operations."),
            ]),
            ("Unit 3 (CLO 2,3,4,5) — Linear Systems, Matrix Inversion & Regression", [
                ("Gaussian Elimination, Gauss-Jordan & LU", "PA = LU   ⇒   Ly = Pb,  Ux = y   |   [A | I] → [I | A⁻¹]", "Partial pivoting avoids zero pivots and limits round-off growth."),
                ("Gauss-Seidel Iteration", "x_i^{(k+1)} = (b_i - Σ_{j<i} a_{ij}x_j^{(k+1)} - Σ_{j>i} a_{ij}x_j^{(k)}) / a_{ii}", "Sufficient convergence condition: strict diagonal dominance."),
                ("Least-Squares Regression", "min_β ||Xβ - y||_2^2", "Fits noisy trend data by minimizing sum of squared vertical residuals (SSE)."),
            ]),
            ("Unit 4 (CLO 1,2) — 1D & Multidimensional Unconstrained Optimization", [
                ("1D Golden-Section & Parabolic Search", "φ = (√5 - 1)/2 ≈ 0.618034", "Narrows unimodal bracket without requiring derivatives."),
                ("1D & 2D Newton / Gradient Descent", "x_{k+1} = x_k - H⁻¹ ∇f(x_k)", "Classifies stationary points via Hessian eigenvalues: SPD (Min), Neg-Def (Max), Indefinite (Saddle)."),
            ]),
            ("Unit 5 (CLO 2,3,4,5) — Polynomial Interpolation", [
                ("Newton Divided Differences & Lagrange", "P_n(x) = Σ_{i=0}^n y_i L_i(x)", "Unique degree ≤ n polynomial passing exactly through n+1 distinct nodes."),
                ("Inverse Interpolation", "x = P^{-1}(y*)", "Valid by swapping coordinates when y_i is strictly monotonic on the interval."),
            ]),
            ("Unit 6 (CLO 2,3,4,5) — Numerical Integration & Ordinary Differential Equations", [
                ("Newton-Cotes (Trapezoidal, Simpson 1/3 & 3/8, Boole)", "Simpson 1/3: (h/3)[f_0 + 4Σf_odd + 2Σf_even + f_n]  (n even)", "Higher-order polynomial panel approximations."),
                ("Romberg & Gauss-Legendre Quadrature", "R(k,j) = (4^j R(k,j-1) - R(k-1,j-1))/(4^j - 1)", "Gauss n-point rule integrates polynomials up to degree 2n-1 exactly."),
                ("ODE Solvers (Euler, Heun, Midpoint RK2, Classical RK4 & Systems)", "y_{n+1} = y_n + (h/6)(k_1 + 2k_2 + 2k_3 + k_4)", "RK4 achieves 4th-order global accuracy O(h^4) for scalar and coupled vector IVPs."),
            ]),
        ]

        for unit_title, items in sections:
            text_widget.insert(tk.END, f"{unit_title}\n", 'unit')
            for name, formula, desc in items:
                text_widget.insert(tk.END, f"• {name}\n", 'sub')
                text_widget.insert(tk.END, f"   Formula: {formula}\n", 'mono')
                text_widget.insert(tk.END, f"   {desc}\n\n", 'body')

        text_widget.configure(state='disabled')

        ftr = tk.Frame(win, bg=COLORS.bg, pady=8)
        ftr.pack(fill=tk.X)
        ChipButton(ftr, text="Close Guide", command=win.destroy, accent=COLORS.accent_cyan, bg=COLORS.card).pack()

    def _show_about(self):
        about = tk.Toplevel(self)
        about.title("About Software")
        about.geometry("520x330")
        about.configure(bg=COLORS.bg)
        about.resizable(False, False)

        about.transient(self.winfo_toplevel())
        about.grab_set()

        card = tk.Frame(about, bg=COLORS.card, padx=30, pady=25, highlightthickness=1, highlightbackground=COLORS.border)
        card.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(card, text="Numerical Analysis Suite", font=FONTS['title'], bg=COLORS.card, fg=COLORS.accent_cyan).pack(pady=(5, 4))
        tk.Label(card, text="Version 2.0.0 — Complete 6-Unit Learning Lab (Open Edition)", font=FONTS['body_std'], bg=COLORS.card, fg=COLORS.accent_green).pack(pady=(0, 18))

        tk.Label(card, text="Lead Developer: Somajit Deb", font=FONTS['heading'], bg=COLORS.card, fg=COLORS.accent_amber).pack(pady=(0, 4))
        tk.Label(card, text="Computer Science & Engineering", font=FONTS['body_std'], bg=COLORS.card, fg=COLORS.text_primary).pack(pady=(0, 2))
        tk.Label(card, text="Khulna University", font=FONTS['subheading'], bg=COLORS.card, fg=COLORS.text_secondary).pack(pady=(0, 18))

        ChipButton(card, text="Close Window", command=about.destroy, accent=COLORS.accent_cyan, bg=COLORS.bg_mid).pack()

    def _show_comparison_lab(self):
        win = tk.Toplevel(self)
        win.title("Method Comparison Benchmark Lab (C Engine)")
        win.geometry("920x620")
        win.configure(bg=COLORS.bg)
        win.transient(self.winfo_toplevel())

        hdr = tk.Frame(win, bg=COLORS.card, padx=22, pady=12, highlightthickness=1, highlightbackground=COLORS.border)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="⚖ Multi-Method Side-by-Side Benchmark (C Engine)", font=FONTS['heading'], bg=COLORS.card, fg=COLORS.accent_amber).pack(anchor='w')
        tk.Label(hdr, text="Compare convergence speed, iterations, and residual accuracy across Root Solvers, Quadrature Rules, or ODE Solvers on the same problem.", font=FONTS['body_small'], bg=COLORS.card, fg=COLORS.text_secondary).pack(anchor='w')

        ctrl = tk.Frame(win, bg=COLORS.bg, padx=22, pady=10)
        ctrl.pack(fill=tk.X)
        tk.Label(ctrl, text="Benchmark Suite:", font=FONTS['subheading'], bg=COLORS.bg, fg=COLORS.accent_cyan).pack(side=tk.LEFT, padx=(0, 8))

        suite_var = tk.StringVar(value='roots')
        eq_entry = PremiumEntry(ctrl, width=24, default='x^3 - 2*x - 5')

        def load_suite(mode):
            suite_var.set(mode)
            if mode == 'roots':
                eq_entry.set('x^3 - 2*x - 5')
            elif mode == 'quad':
                eq_entry.set('sin(x) + 0.5*x^2')
            else:
                eq_entry.set('-2*y + sin(t)')
            run_benchmark()

        ChipButton(ctrl, "Root Solvers (f(x)=0)", command=lambda: load_suite('roots'), accent=COLORS.accent_cyan, bg=COLORS.card).pack(side=tk.LEFT, padx=3)
        ChipButton(ctrl, "Quadrature Rules (∫f(x)dx)", command=lambda: load_suite('quad'), accent=COLORS.accent_amber, bg=COLORS.card).pack(side=tk.LEFT, padx=3)
        ChipButton(ctrl, "ODE Solvers (dy/dt)", command=lambda: load_suite('ode'), accent=COLORS.accent_purple, bg=COLORS.card).pack(side=tk.LEFT, padx=3)
        tk.Label(ctrl, text="  Expression:", font=FONTS['body_small'], bg=COLORS.bg, fg=COLORS.text_secondary).pack(side=tk.LEFT, padx=(10, 4))
        eq_entry.pack(side=tk.LEFT, padx=4)

        body = tk.Frame(win, bg=COLORS.bg, padx=22, pady=6)
        body.pack(fill=tk.BOTH, expand=True)

        fig = Figure(figsize=(5.2, 4.2), facecolor=COLORS.plot_face)
        fig.subplots_adjust(left=0.14, bottom=0.14, right=0.95, top=0.90)
        ax = fig.add_subplot(111)
        ax.set_facecolor(COLORS.plot_axes)
        canvas = FigureCanvasTkAgg(fig, master=body)
        canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        tree = ttk.Treeview(body, columns=('method', 'iters', 'result', 'error', 'order'), show='headings', height=16)
        for col, h, w in zip(tree['columns'], ('Method', 'Steps/N', 'Final Estimate', 'Residual / Error', 'Order'), (140, 65, 115, 115, 70)):
            tree.heading(col, text=h)
            tree.column(col, width=w, anchor='center')
        tree.pack(side=tk.RIGHT, fill=tk.Y)

        def run_benchmark():
            tree.delete(*tree.get_children())
            ax.clear()
            ax.set_facecolor(COLORS.plot_axes)
            ax.grid(True, color=COLORS.plot_grid, linestyle='--', alpha=0.55)
            ax.tick_params(colors=COLORS.text_secondary, labelsize=8)
            mode = suite_var.get()
            expr = eq_entry.get().strip()

            if mode == 'roots':
                specs = [
                    ('Bisection', 'bisection', 1.5, 3.0, 'O(1/2^n)', COLORS.accent_cyan),
                    ('False Position', 'false_position', 1.5, 3.0, 'Superlinear', COLORS.accent_amber),
                    ("Brent's Method", 'brent', 1.5, 3.0, 'Superlinear', COLORS.accent_green),
                    ('Newton-Raphson', 'newton', 2.0, 0.0, 'O(e^2)', COLORS.accent_purple),
                    ('Modified Newton', 'modified_newton', 2.0, 0.0, 'O(e^2)', COLORS.accent_red),
                    ('Secant', 'secant', 1.5, 2.5, 'O(e^1.618)', '#38bdf8'),
                    ('Modified Secant', 'modified_secant', 2.0, 0.01, 'Superlinear', '#f472b6'),
                ]
                for label, m, v1, v2, ord_str, col in specs:
                    lines = run_root_engine([m, expr, v1, v2, 0.0001])
                    res_list = [safe_float(l.split(',')[2]) for l in lines if l.startswith('RESIDUAL,')]
                    steps = [[safe_float(v) for v in l.split(',')[1:]] for l in lines if l.startswith('STEP,')]
                    if steps and res_list:
                        xr = steps[-1][3] if len(steps[-1]) < 8 else steps[-1][5]
                        tree.insert('', 'end', values=(label, len(steps), f"{xr:.7f}", f"{res_list[-1]:.2e}", ord_str))
                        ax.semilogy(range(1, len(res_list) + 1), [max(r, 1e-16) for r in res_list], 'o-', color=col, lw=1.8, markersize=4, label=label)
                ax.set_title("Root Convergence: |f(x_k)| vs Iteration (C Engine)", color=COLORS.text_primary, fontsize=10, fontweight='bold')
                ax.set_xlabel("Iteration k", color=COLORS.text_secondary, fontsize=9)
                ax.set_ylabel("|f(x_k)| (log scale)", color=COLORS.text_secondary, fontsize=9)
                ax.legend(facecolor=COLORS.card, edgecolor=COLORS.border, labelcolor=COLORS.text_primary, fontsize=7.5)
            elif mode == 'quad':
                specs = [
                    ('Trapezoidal', 'trap', 6, 'O(h^2)'),
                    ('Simpson 1/3', 'simp13', 6, 'O(h^4)'),
                    ('Simpson 3/8', 'simp38', 6, 'O(h^4)'),
                    ("Boole's Rule", 'boole', 8, 'O(h^6)'),
                    ('Romberg R(4,4)', 'romberg', 8, 'O(h^8)'),
                    ('Gauss 4-Point', 'gauss', 4, 'Exact deg≤7'),
                ]
                names, errs = [], []
                for label, m, n_sub, ord_str in specs:
                    lines = run_numlab_engine(["quad", m, expr, 0.0, 3.14159265, n_sub])
                    summ = [l.split(',') for l in lines if l.startswith('SUMMARY,')]
                    if summ:
                        s = summ[0]
                        val, err = safe_float(s[1]), max(safe_float(s[3]), 1e-16)
                        tree.insert('', 'end', values=(label, s[5], f"{val:.8f}", f"{err:.2e}", ord_str))
                        names.append(label)
                        errs.append(err)
                ax.bar(names, errs, color=COLORS.accent_amber, alpha=0.85)
                ax.set_yscale('log')
                ax.set_title("Quadrature Absolute Error |I_exact - I_approx| on [0, π]", color=COLORS.text_primary, fontsize=10, fontweight='bold')
                ax.tick_params(axis='x', rotation=20)
            else:
                specs = [
                    ('Euler O(h)', 'euler', 'O(h)', COLORS.accent_red),
                    ('Heun RK2', 'heun', 'O(h^2)', COLORS.accent_amber),
                    ('Midpoint RK2', 'midpoint', 'O(h^2)', COLORS.accent_purple),
                    ('Classical RK4', 'rk4', 'O(h^4)', COLORS.accent_cyan),
                ]
                for label, m, ord_str, col in specs:
                    lines = run_numlab_engine(["ode", m, expr, "", 0.0, 1.0, 0.0, 3.0, 0.25])
                    steps = [l.split(',') for l in lines if l.startswith('STEP_1D,')]
                    if steps:
                        ts = [safe_float(r[2]) for r in steps]
                        ys = [safe_float(r[3]) for r in steps]
                        tree.insert('', 'end', values=(label, len(steps) - 1, f"y(3)={ys[-1]:.6f}", f"h=0.25", ord_str))
                        ax.plot(ts, ys, 'o-', color=col, lw=1.8, markersize=4, label=label)
                ax.set_title("ODE Trajectories y(t) on [0, 3] (C Engine)", color=COLORS.text_primary, fontsize=10, fontweight='bold')
                ax.legend(facecolor=COLORS.card, edgecolor=COLORS.border, labelcolor=COLORS.text_primary, fontsize=8)

            canvas.draw_idle()

        ChipButton(ctrl, "▶ Run C Benchmark", command=run_benchmark, accent=COLORS.accent_green, bg=COLORS.card).pack(side=tk.LEFT, padx=6)
        run_benchmark()

    def _show_practice_quiz(self):
        win = tk.Toplevel(self)
        win.title("Exam Practice & Self-Test Quiz (C Engine Verified)")
        win.geometry("760x480")
        win.configure(bg=COLORS.bg)
        win.transient(self.winfo_toplevel())

        problems = [
            {
                "unit": "Unit 2 • Root Finding (Newton-Raphson)",
                "prompt": "Find the positive root of f(x) = x^3 - 2*x - 5 starting near x0 = 2.0 (to 4 decimal places):",
                "hint": "Formula: x_{n+1} = x_n - (x_n^3 - 2x_n - 5) / (3x_n^2 - 2). After 4 iterations in C, x* ≈ 2.0946.",
                "solve_c": lambda: safe_float([l.split(',') for l in run_root_engine(["newton", "x^3 - 2*x - 5", 2.0, 0.0, 0.0001]) if l.startswith("STEP,")][-1][4]),
                "tol": 0.005,
            },
            {
                "unit": "Unit 2 • Horner's Rule Polynomial Evaluation",
                "prompt": "Evaluate P(2) for P(x) = 2x^3 - 6x^2 + 2x - 1 using nested Horner multiplication:",
                "hint": "b_3 = 2; b_2 = 2(2) - 6 = -2; b_1 = -2(2) + 2 = -2; b_0 = -2(2) - 1 = -5.",
                "solve_c": lambda: safe_float([l.split(',') for l in run_root_engine(["horner", 2.0, 3, 2, -6, 2, -1]) if l.startswith("HORNER_EVAL,")][0][1]),
                "tol": 0.01,
            },
            {
                "unit": "Unit 3 • Linear Systems (Gaussian Elimination)",
                "prompt": "Solve for x_1 in the system: 2x_1 + x_2 - x_3 = 8,  -3x_1 - x_2 + 2x_3 = -11,  -2x_1 + x_2 + 2x_3 = -3:",
                "hint": "Full C solution vector is [x_1, x_2, x_3] = [2, 3, -1], so x_1 = 2.",
                "solve_c": lambda: safe_float([l.split(',') for l in run_matrix_engine(["gaussian", 3, 2, 1, -1, -3, -1, 2, -2, 1, 2, 8, -11, -3]) if l.startswith("SOLUTION,")][0][1]),
                "tol": 0.01,
            },
            {
                "unit": "Unit 4 • 1D Optimization",
                "prompt": "Find the x* that minimizes f(x) = (x - 2)^2 + 1 on [0, 5]:",
                "hint": "Set f'(x) = 2(x - 2) = 0 ⇒ x* = 2.0.",
                "solve_c": lambda: safe_float([l.split(',') for l in run_numlab_engine(["opt_1d", "newton1d", "(x - 2)^2 + 1", 0.5, 5.0, 1e-6]) if l.startswith("SUMMARY,")][0][1]),
                "tol": 0.01,
            },
            {
                "unit": "Unit 5 • Newton Divided-Difference Interpolation",
                "prompt": "Given points (0, 1), (1, 2), (2, 5), evaluate the quadratic interpolant P_2(1.5):",
                "hint": "The points lie on y = x^2 + 1, so P_2(1.5) = 1.5^2 + 1 = 3.25.",
                "solve_c": lambda: safe_float([l.split(',') for l in run_numlab_engine(["interp", "newton", 1.5, 2, 3, 0, 1, 1, 2, 2, 5]) if l.startswith("SUMMARY,")][0][1]),
                "tol": 0.01,
            },
            {
                "unit": "Unit 6A • Numerical Integration (Simpson's 1/3 Rule)",
                "prompt": "Compute ∫_0^2 x^3 dx using Simpson's 1/3 Rule with n = 4 panels:",
                "hint": "Simpson's 1/3 rule is exact for cubics! Exact integral = [x^4 / 4]_0^2 = 4.0.",
                "solve_c": lambda: safe_float([l.split(',') for l in run_numlab_engine(["quad", "simp13", "x^3", 0.0, 2.0, 4]) if l.startswith("SUMMARY,")][0][1]),
                "tol": 0.01,
            },
        ]

        idx_var = tk.IntVar(value=0)
        score_var = tk.IntVar(value=0)

        card = tk.Frame(win, bg=COLORS.card, padx=26, pady=20, highlightthickness=1, highlightbackground=COLORS.border)
        card.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        lbl_unit = tk.Label(card, text="", font=FONTS['subheading'], bg=COLORS.card, fg=COLORS.accent_amber)
        lbl_unit.pack(anchor='w')
        lbl_prompt = tk.Label(card, text="", font=FONTS['heading'], bg=COLORS.card, fg=COLORS.text_primary, wraplength=660, justify='left')
        lbl_prompt.pack(anchor='w', pady=(10, 14))

        ans_row = tk.Frame(card, bg=COLORS.card)
        ans_row.pack(fill=tk.X, pady=6)
        tk.Label(ans_row, text="Your Numerical Answer:", font=FONTS['subheading'], bg=COLORS.card, fg=COLORS.text_secondary).pack(side=tk.LEFT, padx=(0, 10))
        entry_ans = PremiumEntry(ans_row, width=18, default='')
        entry_ans.pack(side=tk.LEFT, padx=(0, 10))

        lbl_feedback = tk.Label(card, text="Enter your answer and click Verify with C Engine.", font=FONTS['body_std'], bg=COLORS.card, fg=COLORS.text_secondary, wraplength=660, justify='left')
        lbl_feedback.pack(anchor='w', pady=(14, 10))

        def load_q(idx):
            idx_var.set(idx % len(problems))
            p = problems[idx_var.get()]
            lbl_unit.config(text=f"Question {idx_var.get() + 1} / {len(problems)}   •   {p['unit']}   •   Score: {score_var.get()}")
            lbl_prompt.config(text=p['prompt'])
            entry_ans.set('')
            lbl_feedback.config(text="Enter your answer and click Verify with C Engine.", fg=COLORS.text_secondary)

        def check_ans():
            p = problems[idx_var.get()]
            try:
                user_v = float(entry_ans.get().strip())
            except Exception:
                lbl_feedback.config(text="⚠ Please enter a valid floating-point number.", fg=COLORS.accent_red)
                return
            c_val = p['solve_c']()
            if abs(user_v - c_val) <= p['tol']:
                score_var.set(score_var.get() + 1)
                lbl_unit.config(text=f"Question {idx_var.get() + 1} / {len(problems)}   •   {p['unit']}   •   Score: {score_var.get()}")
                lbl_feedback.config(text=f"✓ Correct! C Engine verified answer = {c_val:.6g}.  {p['hint']}", fg=COLORS.accent_green)
            else:
                lbl_feedback.config(text=f"✗ Not quite (your answer: {user_v:.6g}, C Engine exact: {c_val:.6g}).\nHint: {p['hint']}", fg=COLORS.accent_amber)

        def show_hint():
            p = problems[idx_var.get()]
            lbl_feedback.config(text=f"💡 Hint: {p['hint']}", fg=COLORS.accent_cyan)

        ChipButton(ans_row, "✓ Verify with C Engine", command=check_ans, accent=COLORS.accent_green, bg=COLORS.bg_mid).pack(side=tk.LEFT, padx=4)
        ChipButton(ans_row, "💡 Show Formula Hint", command=show_hint, accent=COLORS.accent_cyan, bg=COLORS.bg_mid).pack(side=tk.LEFT, padx=4)
        ChipButton(ans_row, "Next Question →", command=lambda: load_q(idx_var.get() + 1), accent=COLORS.accent_amber, bg=COLORS.bg_mid).pack(side=tk.LEFT, padx=4)

        load_q(0)
