import csv
import math
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from config import COLORS, FONTS, safe_float
from c_bridge import run_root_engine
from widgets import GlowButton, IconButton, PremiumEntry, SectionLabel, StatCard, ChipButton, StepControlBar, show_working_steps_modal


METHOD_INFO = {
    'bisection': (
        "Bisection Method (C Engine)",
        "c = a + (b - a) / 2   |   Keep [a, c] if f(a)·f(c) < 0 else [c, b]",
        "Repeatedly halves a continuous bracket [a, b] where f(a)·f(b) < 0. Guaranteed linear convergence O(1/2^n); bracket width halves every step."
    ),
    'false_position': (
        "False Position / Regula Falsi (C Engine)",
        "c = b - f(b)(b - a) / (f(b) - f(a))",
        "Connects endpoints (a, f(a)) and (b, f(b)) with a secant chord and uses its x-intercept c as the new bracket split point."
    ),
    'brent': (
        "Brent's Hybrid Method (C Engine)",
        "Inverse Quadratic Interpolation + Secant + Safeguarded Bisection",
        "Combines the guaranteed bracket safety of Bisection with superlinear Secant / Inverse Quadratic Interpolation steps whenever safe."
    ),
    'newton': (
        "Newton-Raphson Method (C Engine)",
        "x_{n+1} = x_n - f(x_n) / f'(x_n)",
        "Projects the tangent line at (x_n, f(x_n)) to the x-axis. Achieves fast quadratic convergence O(e_n²) near simple roots where f'(x*) ≠ 0."
    ),
    'modified_newton': (
        "Modified Newton-Raphson for Multiple Roots (C Engine)",
        "x_{n+1} = x_n - [f(x_n) f'(x_n)] / ([f'(x_n)]² - f(x_n) f''(x_n))",
        "Applies Newton's method to u(x) = f(x)/f'(x), restoring full quadratic convergence on repeated roots of multiplicity m > 1."
    ),
    'secant': (
        "Secant Method (C Engine)",
        "x_{n+1} = x_n - f(x_n)(x_n - x_{n-1}) / (f(x_n) - f(x_{n-1}))",
        "Replaces the analytical derivative f'(x_n) with a two-point backward secant difference; converges superlinearly with order φ ≈ 1.618."
    ),
    'modified_secant': (
        "Modified Secant Method (C Engine)",
        "x_{n+1} = x_n - [δ·x_n·f(x_n)] / [f(x_n + δ·x_n) - f(x_n)]",
        "Approximates the derivative using a fractional perturbation δ·x_n from a single guess x_n without requiring a second starting point."
    ),
    'fixed_point': (
        "Fixed-Point Iteration (C Engine)",
        "x_{n+1} = g(x_n)   |   Root of f(x) = g(x) - x = 0",
        "Iterates x_{n+1} = g(x_n) along a cobweb trajectory between y = g(x) and y = x. Converges locally when |g'(x*)| < 1."
    ),
}


class RootFindingTab(tk.Frame):
    def __init__(self, parent, go_home_callback):
        super().__init__(parent, bg=COLORS.bg_root)
        self.go_home_callback = go_home_callback
        self.algorithm_steps, self.step_residuals, self.current_step = [], {}, 0
        self.curve_x, self.curve_y, self.true_root = [], [], None
        self._in_result_view = False
        self._panning, self._pan_start = False, None
        self._preview_timer = None
        self._build_ui()

    def _build_ui(self):
        self.screen_input = tk.Frame(self, bg=COLORS.bg_root)
        self.screen_input.pack(fill=tk.BOTH, expand=True)

        content_wrapper = tk.Frame(self.screen_input, bg=COLORS.bg_root)
        content_wrapper.pack(expand=True, fill=tk.BOTH, padx=30, pady=10)

        # ── LEFT COLUMN (Configuration) ──
        left_col = tk.Frame(content_wrapper, bg=COLORS.bg_root)
        left_col.pack(side=tk.LEFT, fill=tk.Y, padx=(15, 25), pady=5)

        nav_row = tk.Frame(left_col, bg=COLORS.bg_root)
        nav_row.pack(fill=tk.X, pady=(0, 8))
        IconButton(nav_row, '← Back to Dashboard', command=self.go_home_callback, font=FONTS.SUBHEADING).pack(side=tk.LEFT)

        SectionLabel(left_col, 'Root Solver Configuration (C Engine)').pack(anchor='w')

        card = tk.Frame(left_col, bg=COLORS.bg_card, padx=26, pady=18, highlightthickness=1, highlightbackground=COLORS.border)
        card.pack(pady=8, fill=tk.X)

        self.method_var = tk.StringVar(value='bisection')

        cat_frame = tk.Frame(card, bg=COLORS.bg_card)
        cat_frame.pack(fill=tk.X, pady=(0, 6))

        col_bracketing = tk.Frame(cat_frame, bg=COLORS.bg_card)
        col_bracketing.pack(side=tk.LEFT, anchor='n', padx=(0, 35))

        tk.Label(col_bracketing, text="Bracketing Methods", font=FONTS.SUBHEADING, bg=COLORS.bg_card, fg=COLORS.accent_cyan).pack(anchor='w', pady=(0, 6))
        for text, val in [('Bisection', 'bisection'), ('False Position', 'false_position'), ("Brent's Method", 'brent')]:
            tk.Radiobutton(
                col_bracketing, text=text, variable=self.method_var, value=val,
                bg=COLORS.bg_card, fg=COLORS.text_secondary, selectcolor=COLORS.bg_panel,
                font=FONTS.BODY, command=self._toggle_inputs,
                activebackground=COLORS.bg_card, activeforeground=COLORS.accent_cyan
            ).pack(anchor='w', pady=2)

        col_open = tk.Frame(cat_frame, bg=COLORS.bg_card)
        col_open.pack(side=tk.LEFT, anchor='n')

        tk.Label(col_open, text="Open Methods", font=FONTS.SUBHEADING, bg=COLORS.bg_card, fg=COLORS.accent_amber).pack(anchor='w', pady=(0, 6))
        for text, val in [
            ('Newton-Raphson', 'newton'),
            ('Modified Newton', 'modified_newton'),
            ('Secant', 'secant'),
            ('Modified Secant', 'modified_secant'),
            ('Fixed-Point g(x)', 'fixed_point')
        ]:
            tk.Radiobutton(
                col_open, text=text, variable=self.method_var, value=val,
                bg=COLORS.bg_card, fg=COLORS.text_secondary, selectcolor=COLORS.bg_panel,
                font=FONTS.BODY, command=self._toggle_inputs,
                activebackground=COLORS.bg_card, activeforeground=COLORS.accent_cyan
            ).pack(anchor='w', pady=2)

        tk.Frame(card, height=1, bg=COLORS.border).pack(fill=tk.X, pady=10)

        # Quick Presets Row
        preset_hdr = tk.Frame(card, bg=COLORS.bg_card)
        preset_hdr.pack(fill=tk.X, pady=(0, 4))
        tk.Label(preset_hdr, text="Quick Examples:", bg=COLORS.bg_card, fg=COLORS.text_muted, font=FONTS.SMALL).pack(side=tk.LEFT)
        ChipButton(
            preset_hdr,
            text="📐 Horner & Polynomial Roots (C)",
            command=self._show_horner_lab,
            accent=COLORS.accent_amber,
            bg=COLORS.bg_panel
        ).pack(side=tk.RIGHT)
        presets_row = tk.Frame(card, bg=COLORS.bg_card)
        presets_row.pack(fill=tk.X, pady=(0, 10))
        presets = [
            ("Cubic", "bisection", "x^3 - 2*x - 5", "1.5", "2.5"),
            ("Cos-x", "newton", "cos(x) - x", "0.5", "1.0"),
            ("Exp", "false_position", "exp(-x) - x", "0.0", "1.0"),
            ("Trig", "brent", "sin(x) - x/2", "1.5", "2.5"),
            ("Fixed-Pt", "fixed_point", "cos(x)", "0.5", "1.0"),
        ]
        for label, m_val, eq_val, v1_val, v2_val in presets:
            ChipButton(
                presets_row,
                text=label,
                command=lambda mv=m_val, eq=eq_val, a=v1_val, b=v2_val: self._apply_preset(mv, eq, a, b),
                bg=COLORS.bg_panel
            ).pack(side=tk.LEFT, padx=(0, 5))

        tk.Label(card, text="Stopping Tolerance ε (%):", bg=COLORS.bg_card, fg=COLORS.text_secondary, font=FONTS.SUBHEADING).pack(anchor='w', pady=(0, 2))
        self.entry_tol = PremiumEntry(card, width=32, default='0.0001')
        self.entry_tol.pack(fill=tk.X, pady=(0, 8))

        self.lbl_eq = tk.Label(card, text="Equation f(x) = 0:", bg=COLORS.bg_card, fg=COLORS.text_secondary, font=FONTS.SUBHEADING)
        self.lbl_eq.pack(anchor='w', pady=(0, 2))
        self.entry_eq = PremiumEntry(card, width=32, default='x^3 - 2*x - 5')
        self.entry_eq.pack(fill=tk.X, pady=(0, 8))
        self.entry_eq._entry.bind('<KeyRelease>', self._schedule_preview)

        self.input_block = tk.Frame(card, bg=COLORS.bg_card)
        self.input_block.pack(fill=tk.X)

        self.lbl_v1 = tk.Label(self.input_block, text="Lower Bound (a):", bg=COLORS.bg_card, fg=COLORS.text_secondary, font=FONTS.SUBHEADING)
        self.lbl_v1.pack(anchor='w', pady=(0, 2))
        self.entry_v1 = PremiumEntry(self.input_block, width=32, default='1.5')
        self.entry_v1.pack(fill=tk.X, pady=(0, 8))
        self.entry_v1._entry.bind('<KeyRelease>', self._schedule_preview)

        self.lbl_v2 = tk.Label(self.input_block, text="Upper Bound (b):", bg=COLORS.bg_card, fg=COLORS.text_secondary, font=FONTS.SUBHEADING)
        self.lbl_v2.pack(anchor='w', pady=(0, 2))
        self.entry_v2 = PremiumEntry(self.input_block, width=32, default='2.5')
        self.entry_v2.pack(fill=tk.X)
        self.entry_v2._entry.bind('<KeyRelease>', self._schedule_preview)

        # ── RIGHT COLUMN (Preview & Action) ──
        right_col = tk.Frame(content_wrapper, bg=COLORS.bg_root)
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20, 15), pady=5)

        SectionLabel(right_col, 'Live Function & Bracket Preview (C Engine)', accent='amber').pack(anchor='w', pady=(34, 8))

        preview_card = tk.Frame(right_col, bg=COLORS.bg_card, padx=14, pady=14, highlightthickness=1, highlightbackground=COLORS.border)
        preview_card.pack(fill=tk.BOTH, expand=True)

        self.lbl_method_desc = tk.Label(
            preview_card,
            text="",
            font=FONTS.SMALL,
            bg=COLORS.bg_card,
            fg=COLORS.accent_cyan,
            anchor='w'
        )
        self.lbl_method_desc.pack(fill=tk.X, pady=(0, 6))

        self.prev_fig = Figure(figsize=(5.2, 3.6), facecolor=COLORS.bg_card)
        self.prev_fig.subplots_adjust(left=0.12, bottom=0.12, right=0.96, top=0.94)
        self.prev_ax = self.prev_fig.add_subplot(111)
        self.prev_ax.set_facecolor(COLORS.plot_axes)
        self.prev_canvas = FigureCanvasTkAgg(self.prev_fig, master=preview_card)
        self.prev_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.lbl_preview_status = tk.Label(
            preview_card,
            text="Ready",
            font=FONTS.MONO_SMALL,
            bg=COLORS.bg_card,
            fg=COLORS.accent_green,
            anchor='w'
        )
        self.lbl_preview_status.pack(fill=tk.X, pady=(6, 0))

        action_bar = tk.Frame(right_col, bg=COLORS.bg_root)
        action_bar.pack(pady=(16, 4))
        GlowButton(action_bar, text='▶ CALCULATE ROOT (C ENGINE)', command=self._run_solver, width=320, height=54, bg=COLORS.bg_root).pack()

        # ── RESULT SCREEN ──
        self.screen_graph = tk.Frame(self, bg=COLORS.bg_root)

        dash_bar = tk.Frame(self.screen_graph, bg=COLORS.bg_root, pady=10, padx=20)
        dash_bar.pack(fill=tk.X)
        IconButton(dash_bar, '← BACK TO INPUTS', command=self._go_back, font=FONTS.SUBHEADING).pack(side=tk.LEFT, padx=(0, 16))

        self.stat_guess = StatCard(dash_bar, "Current xr", COLORS.accent_cyan)
        self.stat_guess.pack(side=tk.LEFT, padx=4)
        self.stat_res = StatCard(dash_bar, "Residual |f(xr)|", COLORS.accent_purple)
        self.stat_res.pack(side=tk.LEFT, padx=4)
        self.stat_ea = StatCard(dash_bar, "Approx Error (εa)", COLORS.accent_amber)
        self.stat_ea.pack(side=tk.LEFT, padx=4)
        self.stat_et = StatCard(dash_bar, "Ref. Diff |x* - xr|", COLORS.accent_red)
        self.stat_et.pack(side=tk.LEFT, padx=4)
        self.stat_root = StatCard(dash_bar, "Reference Root", COLORS.accent_green)
        self.stat_root.pack(side=tk.LEFT, padx=4)

        # Step explanation & playback controls bar
        ctrl_bar = tk.Frame(self.screen_graph, bg=COLORS.bg_root, padx=20, pady=4)
        ctrl_bar.pack(fill=tk.X)

        self.step_player = StepControlBar(
            ctrl_bar,
            on_step_change=self._select_step,
            get_total_steps=lambda: len(self.algorithm_steps),
            get_current_step=lambda: self.current_step
        )
        self.step_player.pack(side=tk.LEFT)

        ChipButton(ctrl_bar, text="🔍 Reset Zoom", command=self._reset_zoom, bg=COLORS.bg_card).pack(side=tk.LEFT, padx=(10, 4))
        ChipButton(ctrl_bar, text="📥 Export CSV", command=self._export_csv, accent=COLORS.accent_cyan, bg=COLORS.bg_card).pack(side=tk.LEFT, padx=4)
        ChipButton(ctrl_bar, text="📖 Working Steps & Equation", command=self._show_working_steps, accent=COLORS.accent_amber, bg=COLORS.bg_card).pack(side=tk.LEFT, padx=4)

        self.lbl_step_formula = tk.Label(
            ctrl_bar,
            text="",
            font=FONTS.MONO_SMALL,
            bg=COLORS.bg_card,
            fg=COLORS.text_primary,
            padx=12,
            pady=6,
            highlightthickness=1,
            highlightbackground=COLORS.border
        )
        self.lbl_step_formula.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(12, 0))

        main_res = tk.Frame(self.screen_graph, bg=COLORS.bg_root)
        main_res.pack(fill=tk.BOTH, expand=True, padx=20, pady=(6, 16))

        graph_container = tk.Frame(main_res, bg=COLORS.bg_card, highlightthickness=1, highlightbackground=COLORS.border)
        graph_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.fig = Figure(figsize=(8.6, 5.6), facecolor=COLORS.plot_face)
        self.fig.subplots_adjust(left=0.08, bottom=0.09, right=0.96, top=0.94)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(COLORS.plot_axes)

        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_container)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        bottom_graph_bar = tk.Frame(graph_container, bg=COLORS.bg_card, padx=10, pady=4)
        bottom_graph_bar.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Label(
            bottom_graph_bar,
            text="Scroll to Zoom  •  Left-Click & Drag to Pan  •  ←/→ or Space to Step",
            font=FONTS.SMALL,
            bg=COLORS.bg_card,
            fg=COLORS.text_muted
        ).pack(side=tk.LEFT)
        self.lbl_coords = tk.Label(bottom_graph_bar, text="X: ---  |  Y: ---", bg=COLORS.bg_card, fg=COLORS.accent_cyan, font=FONTS.MONO_SMALL)
        self.lbl_coords.pack(side=tk.RIGHT)

        # Iteration Table with Scrollbar
        table_frame = tk.Frame(main_res, bg=COLORS.bg_card, highlightthickness=1, highlightbackground=COLORS.border)
        table_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(14, 0))

        self.tree = ttk.Treeview(table_frame, columns=('step', 'x', 'fx', 'ea', 'et'), show='headings', height=22)
        cols_cfg = [
            ('step', 'Iter', 48),
            ('x', 'xr', 100),
            ('fx', '|f(xr)|', 95),
            ('ea', 'εa (%)', 95),
            ('et', '|x* - xr|', 95),
        ]
        for col, head, w in cols_cfg:
            self.tree.heading(col, text=head)
            self.tree.column(col, width=w, anchor='center')

        tree_scroll = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.Y)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)

        self.canvas.mpl_connect('scroll_event', self._on_scroll)
        self.canvas.mpl_connect('button_press_event', self._on_press)
        self.canvas.mpl_connect('button_release_event', self._on_release)
        self.canvas.mpl_connect('motion_notify_event', self._on_motion)

        self._toggle_inputs()

    def _apply_preset(self, method, eq, v1, v2):
        self.method_var.set(method)
        self.entry_eq.set(eq)
        self.entry_v1.set(v1)
        self.entry_v2.set(v2)
        self._toggle_inputs()

    def _show_horner_lab(self):
        win = tk.Toplevel(self)
        win.title("Unit 2 — Polynomial Roots & Horner's Synthetic Division Lab (C Engine)")
        win.geometry("780x560")
        win.configure(bg=COLORS.bg_root)
        win.transient(self.winfo_toplevel())

        top = tk.Frame(win, bg=COLORS.bg_card, padx=20, pady=14, highlightthickness=1, highlightbackground=COLORS.border)
        top.pack(fill=tk.X, padx=16, pady=(16, 8))

        tk.Label(top, text="Polynomial Coefficients (highest degree a_n down to a_0, comma-separated):", font=FONTS.SUBHEADING, bg=COLORS.bg_card, fg=COLORS.accent_cyan).pack(anchor='w')
        row_in = tk.Frame(top, bg=COLORS.bg_card)
        row_in.pack(fill=tk.X, pady=(6, 0))

        coeff_entry = PremiumEntry(row_in, width=28, default="1, 0, -2, -5")
        coeff_entry.pack(side=tk.LEFT, padx=(0, 12))
        tk.Label(row_in, text="Evaluate / Deflate at x0:", font=FONTS.BODY, bg=COLORS.bg_card, fg=COLORS.text_secondary).pack(side=tk.LEFT, padx=(0, 6))
        x0_entry = PremiumEntry(row_in, width=10, default="2.09455")
        x0_entry.pack(side=tk.LEFT, padx=(0, 12))

        out_text = tk.Text(win, bg=COLORS.bg_card, fg=COLORS.text_primary, font=FONTS.MONO_SMALL, padx=16, pady=14, relief='flat', highlightthickness=1, highlightbackground=COLORS.border)
        out_text.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 12))

        def compute_horner():
            out_text.configure(state='normal')
            out_text.delete('1.0', tk.END)
            try:
                coeffs = [float(c.strip()) for c in coeff_entry.get().split(',') if c.strip()]
                x0 = float(x0_entry.get())
                n = len(coeffs) - 1
                if n < 1:
                    raise ValueError("Enter at least 2 coefficients.")

                # Execute Horner synthetic division & polynomial root deflation in C
                lines = run_root_engine(["horner", x0, n, *coeffs])

                b_vals, d_vals, roots = [], [], []
                p_val, dp_val, nr_next = 0.0, 0.0, float('nan')
                for line in lines:
                    parts = line.split(',')
                    if parts[0] == 'HORNER_EVAL':
                        p_val = safe_float(parts[1])
                        dp_val = safe_float(parts[2])
                        nr_next = safe_float(parts[3])
                    elif parts[0] == 'HORNER_B':
                        b_vals = [safe_float(v) for v in parts[1:]]
                    elif parts[0] == 'HORNER_D':
                        d_vals = [safe_float(v) for v in parts[1:]]
                    elif parts[0] == 'POLY_ROOT':
                        roots.append((parts[2], safe_float(parts[3]), safe_float(parts[4])))

                terms = [f"({c:g})x^{n-i}" if n - i > 1 else (f"({c:g})x" if n - i == 1 else f"({c:g})") for i, c in enumerate(coeffs)]
                out_text.insert(tk.END, f"Polynomial P(x) of degree {n} (Evaluated in C):\n  P(x) = " + " + ".join(terms) + "\n\n")

                out_text.insert(tk.END, f"1. Horner's Nested Synthetic Division at x0 = {x0:g}:\n")
                out_text.insert(tk.END, "   Coefficients a_k :  " + "   ".join(f"{c:10.4f}" for c in coeffs) + "\n")
                out_text.insert(tk.END, "   Horner Pass 1 b_k:  " + "   ".join(f"{b:10.4f}" for b in b_vals) + "\n")
                if d_vals:
                    out_text.insert(tk.END, "   Horner Pass 2 d_k:  " + "   ".join(f"{d:10.4f}" for d in d_vals) + "\n")
                out_text.insert(tk.END, f"   ⇒  P({x0:g})  = b_0 = {p_val:.8g}\n")
                out_text.insert(tk.END, f"   ⇒  P'({x0:g}) = {dp_val:.8g}\n")
                if not math.isnan(nr_next):
                    out_text.insert(tk.END, f"   ⇒  One Newton-Horner Step:  x1 = x0 - P(x0)/P'(x0) = {nr_next:.8g}\n\n")

                q_terms = [f"{b:.5g}x^{n-1-i}" if n - 1 - i > 0 else f"{b:.5g}" for i, b in enumerate(b_vals[:-1])]
                out_text.insert(tk.END, f"2. Deflated Quotient Q(x) [where P(x) = (x - {x0:g})Q(x) + {p_val:.4g}]:\n")
                out_text.insert(tk.END, "   Q(x) = " + " + ".join(q_terms) + "\n\n")

                out_text.insert(tk.END, "3. Full Polynomial Root Spectrum (Newton-Horner C Deflation):\n")
                for idx_r, (kind, re_v, im_v) in enumerate(roots):
                    if kind == 'REAL' or abs(im_v) < 1e-10:
                        out_text.insert(tk.END, f"   Root {idx_r+1}:  x = {re_v:.8f}   (Real)\n")
                    else:
                        sign = "+" if im_v >= 0 else "-"
                        out_text.insert(tk.END, f"   Root {idx_r+1}:  x = {re_v:.8f} {sign} {abs(im_v):.8f}i   (Complex Conjugate)\n")
            except Exception as ex:
                out_text.insert(tk.END, f"Error: {ex}\n")
            out_text.configure(state='disabled')

        ChipButton(row_in, text="▶ Run Horner & Root Spectrum (C)", command=compute_horner, accent=COLORS.accent_cyan, bg=COLORS.bg_panel).pack(side=tk.LEFT)
        compute_horner()

    def _toggle_inputs(self):
        m = self.method_var.get()
        title, formula, desc = METHOD_INFO.get(m, ("Root Solver", "", ""))
        self.lbl_method_desc.config(text=f"{title}  •  {formula}\n{desc}")

        if m == 'fixed_point':
            self.lbl_eq.config(text="Iteration Function g(x) [where x = g(x)]:")
        else:
            self.lbl_eq.config(text="Equation f(x) [where f(x) = 0]:")

        self.lbl_v1.pack(anchor='w', pady=(0, 2))
        self.entry_v1.pack(fill=tk.X, pady=(0, 8))
        self.lbl_v2.pack(anchor='w', pady=(0, 2))
        self.entry_v2.pack(fill=tk.X)

        if m in ('newton', 'modified_newton', 'fixed_point'):
            self.lbl_v1.config(text="Initial Guess (x0):")
            self.lbl_v2.pack_forget()
            self.entry_v2.pack_forget()
        elif m in ('bisection', 'false_position', 'brent'):
            self.lbl_v1.config(text="Lower Bound (a):")
            self.lbl_v2.config(text="Upper Bound (b):")
        elif m == 'secant':
            self.lbl_v1.config(text="Initial x0:")
            self.lbl_v2.config(text="Initial x1:")
        elif m == 'modified_secant':
            self.lbl_v1.config(text="Initial x0:")
            self.lbl_v2.config(text="Perturbation Delta (δ):")

        self._schedule_preview()

    def _get_step_xr(self, s, m):
        if m == 'fixed_point':
            return s[2]
        return s[3] if len(s) < 8 else s[5]

    def _select_step(self, idx):
        if not self.algorithm_steps:
            return
        self.current_step = max(0, min(len(self.algorithm_steps) - 1, idx))
        iid = str(self.current_step)
        if self.tree.exists(iid):
            self.tree.selection_set(iid)
            self.tree.see(iid)
        self._update_frame(self.current_step)
        self.step_player.update_counter()

    def _reset_zoom(self):
        if self.algorithm_steps:
            self._update_frame(self.current_step)

    def _update_frame(self, idx):
        self.ax.clear()
        self.ax.set_facecolor(COLORS.plot_axes)
        self.ax.grid(True, color=COLORS.plot_grid, linestyle='--', alpha=0.4)

        self.ax.tick_params(axis='both', colors=COLORS.text_secondary, labelsize=10, pad=5)
        self.ax.spines['left'].set_visible(True)
        self.ax.spines['left'].set_color(COLORS.border)
        self.ax.spines['bottom'].set_visible(True)
        self.ax.spines['bottom'].set_color(COLORS.border)

        s = self.algorithm_steps[idx]
        m = self.method_var.get()

        if m == 'fixed_point':
            self.ax.plot(self.curve_x, self.curve_y, color=COLORS.accent_cyan, lw=2, alpha=0.75, label='y = g(x)')
            self.ax.plot(self.curve_x, self.curve_x, color=COLORS.text_muted, lw=1.5, ls='--', label='y = x')
        else:
            self.ax.plot(self.curve_x, self.curve_y, color=COLORS.accent_cyan, lw=2, alpha=0.65, label='Function f(x)')
            self.ax.axhline(0, color=COLORS.plot_zero, lw=1.2, label='y = 0 (X-Axis)')

        x_points = []
        y_points = [0.0]
        formula_trace = ""

        if m in ('bisection', 'false_position', 'brent'):
            a_val, b_val, xr_val = s[1], s[2], s[3]
            fa = float(np.interp(a_val, self.curve_x, self.curve_y)) if self.curve_x else 0.0
            fb = float(np.interp(b_val, self.curve_x, self.curve_y)) if self.curve_x else 0.0
            fxr = float(np.interp(xr_val, self.curve_x, self.curve_y)) if self.curve_x else 0.0

            self.ax.axvspan(min(a_val, b_val), max(a_val, b_val), color=COLORS.accent_cyan, alpha=0.10, label='Active Bracket [a, b]')
            self.ax.axvline(a_val, color=COLORS.accent_red, ls='--', alpha=0.6, label=f'a = {a_val:.5f}')
            self.ax.axvline(b_val, color=COLORS.accent_cyan, ls='--', alpha=0.6, label=f'b = {b_val:.5f}')
            if m == 'false_position':
                self.ax.plot([a_val, b_val], [fa, fb], color=COLORS.accent_amber, lw=1.5, ls='-', label='Secant Chord')
            self.ax.axvline(xr_val, color=COLORS.accent_amber, lw=2.2, label=f'xr = {xr_val:.5f}')
            self.ax.scatter([xr_val], [fxr], color=COLORS.accent_amber, s=55, zorder=5)

            self.ax.annotate('xr', xy=(xr_val, 0), xytext=(6, 8), textcoords='offset points', color=COLORS.accent_amber, fontweight='bold')
            x_points = [a_val, b_val, xr_val]
            y_points.extend([fa, fb, fxr])
            formula_trace = f"Iter {int(s[0])}:  [a = {a_val:.5f}, b = {b_val:.5f}]  →  xr = {xr_val:.6f}   (width = {abs(b_val - a_val):.5e})"

        elif m in ('newton', 'modified_newton'):
            x, fx, x_next = s[1], s[2], s[3]
            self.ax.plot([x, x_next], [fx, 0], color=COLORS.accent_amber, lw=2, ls='--', label='Tangent Projection')
            self.ax.plot([x, x], [0, fx], color=COLORS.border_focus, lw=1, ls=':')
            self.ax.scatter([x], [fx], color=COLORS.accent_amber, s=55, zorder=5, label='(x_n, f(x_n))')
            self.ax.scatter([x_next], [0], color=COLORS.accent_green, s=55, zorder=5, label=f'x_{{n+1}} = {x_next:.5f}')

            self.ax.annotate('xr', xy=(x_next, 0), xytext=(0, 26), textcoords='offset points',
                             arrowprops=dict(arrowstyle='->', color=COLORS.accent_amber),
                             color=COLORS.accent_amber, ha='center', fontweight='bold')
            x_points = [x, x_next]
            y_points.extend([fx, 0])
            formula_trace = f"Iter {int(s[0])}:  x_n = {x:.5f},  f(x_n) = {fx:.5e}  →  x_{{n+1}} = {x_next:.6f}"

        elif m in ('secant', 'modified_secant'):
            x_prev, fx_prev, x_curr, fx_curr, x_next = s[1], s[2], s[3], s[4], s[5]
            self.ax.plot([x_prev, x_curr, x_next], [fx_prev, fx_curr, 0], color=COLORS.accent_amber, lw=2, ls='--', label='Secant Projection')
            self.ax.scatter([x_prev, x_curr], [fx_prev, fx_curr], color=COLORS.accent_amber, s=55, zorder=5, label='Secant Points')
            self.ax.scatter([x_next], [0], color=COLORS.accent_green, s=55, zorder=5)

            self.ax.annotate('xr', xy=(x_next, 0), xytext=(0, 26), textcoords='offset points',
                             arrowprops=dict(arrowstyle='->', color=COLORS.accent_amber),
                             color=COLORS.accent_amber, ha='center', fontweight='bold')
            x_points = [x_prev, x_curr, x_next]
            y_points.extend([fx_prev, fx_curr, 0])
            formula_trace = f"Iter {int(s[0])}:  x_prev = {x_prev:.5f},  x_curr = {x_curr:.5f}  →  x_next = {x_next:.6f}"

        elif m == 'fixed_point':
            x_curr, x_next = s[1], s[2]
            self.ax.plot([x_curr, x_curr], [x_curr, x_next], color=COLORS.accent_amber, lw=2, ls='-', label='Vertical to g(x)')
            self.ax.plot([x_curr, x_next], [x_next, x_next], color=COLORS.accent_green, lw=2, ls='--', label='Horizontal to y = x')
            self.ax.scatter([x_curr], [x_next], color=COLORS.accent_amber, s=55, zorder=5, label='(x_n, g(x_n))')
            self.ax.scatter([x_next], [x_next], color=COLORS.accent_green, s=55, zorder=5, label=f'x_{{n+1}} = {x_next:.5f}')
            x_points = [x_curr, x_next]
            y_points.extend([x_curr, x_next])
            formula_trace = f"Iter {int(s[0])}:  x_n = {x_curr:.5f}  →  x_{{n+1}} = g(x_n) = {x_next:.6f}"

        if x_points:
            x_min, x_max = min(x_points), max(x_points)
            y_min, y_max = min(y_points), max(y_points)

            global_dx = (max(self.curve_x) - min(self.curve_x)) if self.curve_x else 10.0
            global_dy = (max(self.curve_y) - min(self.curve_y)) if self.curve_y else 10.0

            dx = x_max - x_min
            dy = y_max - y_min

            clamped_dx = max(dx, global_dx * 0.08, 1e-4)
            clamped_dy = max(dy, global_dy * 0.08, 1e-4)

            mid_x = (x_max + x_min) / 2.0
            mid_y = (y_max + y_min) / 2.0

            pad_x = clamped_dx * 0.32
            pad_y = clamped_dy * 0.32

            self.ax.set_xlim(mid_x - (clamped_dx / 2.0) - pad_x, mid_x + (clamped_dx / 2.0) + pad_x)
            self.ax.set_ylim(mid_y - (clamped_dy / 2.0) - pad_y, mid_y + (clamped_dy / 2.0) + pad_y)

        self.ax.legend(loc='best', facecolor=COLORS.bg_panel, edgecolor=COLORS.border, labelcolor=COLORS.text_primary, fontsize=9, framealpha=0.88)

        xr_val = self._get_step_xr(s, m)
        res_val = self.step_residuals.get(idx, float('nan'))
        self.stat_guess.set(f"{xr_val:.6f}")
        self.stat_res.set(f"{res_val:.3e}" if not math.isnan(res_val) else "N/A")
        self.stat_ea.set(f"{s[-2] * 100:.4f}%")
        self.stat_et.set(f"{s[-1]:.4e}")
        self.lbl_step_formula.config(text=formula_trace)

        self.canvas.draw_idle()

    def _schedule_preview(self, event=None):
        if self._preview_timer:
            self.after_cancel(self._preview_timer)
        self._preview_timer = self.after(220, self._update_preview)

    def _update_preview(self, e=None):
        self.prev_ax.clear()
        self.prev_ax.set_facecolor(COLORS.plot_axes)
        self.prev_ax.grid(True, color=COLORS.plot_grid, linestyle='--', alpha=0.35)
        self.prev_ax.tick_params(axis='both', colors=COLORS.text_muted, labelsize=8)

        eq = self.entry_eq.get().strip()
        if not eq:
            self.prev_canvas.draw_idle()
            return

        m = self.method_var.get()
        try:
            v1 = float(self.entry_v1.get())
        except Exception:
            v1 = -2.0
        try:
            v2 = float(self.entry_v2.get())
        except Exception:
            v2 = 2.0

        if m in ('bisection', 'false_position', 'brent', 'secant'):
            span = max(abs(v2 - v1), 2.0)
            x_low = min(v1, v2) - span * 0.6
            x_high = max(v1, v2) + span * 0.6
        else:
            x_low, x_high = v1 - 4.0, v1 + 4.0

        try:
            lines = run_root_engine(["preview", eq, x_low, x_high, v1, v2])
            xs, ys = [], []
            fa, fb, prod = float('nan'), float('nan'), float('nan')
            for line in lines:
                p = line.split(',')
                if p[0] == 'CURVE' and len(p) >= 3:
                    xs.append(safe_float(p[1]))
                    ys.append(safe_float(p[2]))
                elif p[0] == 'EVAL_A' and len(p) >= 3:
                    fa = safe_float(p[2])
                elif p[0] == 'EVAL_B' and len(p) >= 3:
                    fb = safe_float(p[2])
                elif p[0] == 'BRACKET' and len(p) >= 4:
                    prod = safe_float(p[3])

            if m == 'fixed_point':
                self.prev_ax.plot(xs, ys, color=COLORS.accent_cyan, lw=2, label='y = g(x)')
                self.prev_ax.plot(xs, xs, color=COLORS.accent_amber, lw=1.3, ls='--', label='y = x')
                self.prev_ax.axvline(v1, color=COLORS.accent_green, ls=':', alpha=0.7)
                self.prev_ax.legend(loc='best', fontsize=8, facecolor=COLORS.bg_panel, edgecolor=COLORS.border, labelcolor=COLORS.text_primary)
                self.lbl_preview_status.config(text=f"✓ C Preview: seeking intersection of y = g(x) and y = x near x0 = {v1:g}", fg=COLORS.accent_green)
            else:
                self.prev_ax.plot(xs, ys, color=COLORS.accent_cyan, lw=2)
                self.prev_ax.axhline(0, color=COLORS.text_muted, lw=1)

                if m in ('bisection', 'false_position', 'brent'):
                    self.prev_ax.axvspan(min(v1, v2), max(v1, v2), color=COLORS.accent_cyan, alpha=0.12)
                    self.prev_ax.scatter([v1, v2], [fa, fb], color=COLORS.accent_amber, s=35, zorder=5)
                    if not (math.isfinite(fa) and math.isfinite(fb)):
                        self.lbl_preview_status.config(text="⚠ f(a) or f(b) is undefined on this bracket.", fg=COLORS.accent_red)
                    elif prod <= 0:
                        self.lbl_preview_status.config(text=f"✓ Valid C Bracket [{v1:g}, {v2:g}]:  f(a) = {fa:.3g},  f(b) = {fb:.3g}  (opposite signs)", fg=COLORS.accent_green)
                    else:
                        self.lbl_preview_status.config(text=f"⚠ Same Sign on [{v1:g}, {v2:g}]:  f(a) = {fa:.3g},  f(b) = {fb:.3g}  (f(a)·f(b) > 0)", fg=COLORS.accent_amber)
                else:
                    self.prev_ax.scatter([v1], [fa], color=COLORS.accent_amber, s=40, zorder=5)
                    self.lbl_preview_status.config(text=f"✓ C Preview Ready:  f({v1:g}) = {fa:.4g}", fg=COLORS.accent_green)
        except Exception as ex:
            self.lbl_preview_status.config(text=f"⚠ Syntax hint: use * for multiply (e.g. 2*x) — {ex}", fg=COLORS.accent_red)

        self.prev_canvas.draw_idle()

    def _run_solver(self):
        m = self.method_var.get()
        eq = self.entry_eq.get().strip()
        if not eq:
            messagebox.showwarning("Input Required", "Please enter an equation first.")
            return

        try:
            tol = float(self.entry_tol.get())
            if tol <= 0 or not math.isfinite(tol):
                raise ValueError()
        except Exception:
            messagebox.showwarning("Invalid Tolerance", "Tolerance (ε) must be a positive finite number (e.g. 0.0001).")
            return

        try:
            v1 = float(self.entry_v1.get())
            v2 = float(self.entry_v2.get()) if m not in ('newton', 'modified_newton', 'fixed_point') else 0.0
            if not (math.isfinite(v1) and math.isfinite(v2)):
                raise ValueError()
        except Exception:
            messagebox.showwarning("Invalid Parameters", "Please enter valid finite starting numbers.")
            return

        # Bracket validation in C for bracketing methods
        if m in ('bisection', 'false_position', 'brent'):
            if v1 == v2:
                messagebox.showwarning("Invalid Bracket", "Lower bound (a) and Upper bound (b) must be distinct.")
                return
            if v1 > v2:
                v1, v2 = v2, v1
                self.entry_v1.set(str(v1))
                self.entry_v2.set(str(v2))
            try:
                prev_lines = run_root_engine(["preview", eq, v1, v2, v1, v2])
                fa, fb, prod = float('nan'), float('nan'), float('nan')
                for line in prev_lines:
                    p = line.split(',')
                    if p[0] == 'BRACKET' and len(p) >= 4:
                        fa, fb, prod = safe_float(p[1]), safe_float(p[2]), safe_float(p[3])
                if not (math.isfinite(fa) and math.isfinite(fb)):
                    messagebox.showerror("Domain Error", f"Function is undefined at the bracket endpoints: f({v1})={fa}, f({v2})={fb}.")
                    return
                if prod > 0:
                    proceed = messagebox.askyesno(
                        "Bracketing Assumption Warning",
                        f"f({v1:g}) = {fa:.4g} and f({v2:g}) = {fb:.4g} have the SAME sign.\n\n"
                        f"{METHOD_INFO[m][0]} requires a sign change f(a)·f(b) < 0 to guarantee a root in [a, b].\n\n"
                        "Do you want to run the C solver anyway to observe the behavior?"
                    )
                    if not proceed:
                        return
            except Exception as ex:
                messagebox.showerror("Invalid Equation Syntax", str(ex))
                return

        def worker():
            try:
                lines = run_root_engine([m, eq, str(v1), str(v2), str(tol)])
                self.after(0, lambda: self._on_solver_done("\n".join(lines)))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("C Solver Error", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_solver_done(self, stdout_text):
        self.curve_x, self.curve_y, self.algorithm_steps, self.true_root = [], [], [], None
        self.step_residuals = {}
        error_msg = None

        for line in stdout_text.splitlines():
            p = line.split(',')
            if not p:
                continue
            if p[0] == 'ERROR':
                error_msg = ",".join(p[1:])
            elif p[0] == 'CURVE' and len(p) >= 3:
                cx, cy = safe_float(p[1]), safe_float(p[2])
                if not (math.isnan(cx) or math.isnan(cy)):
                    self.curve_x.append(cx)
                    self.curve_y.append(cy)
            elif p[0] == 'TRUEROOT' and len(p) >= 2 and p[1].strip().upper() != 'NAN':
                tr = safe_float(p[1])
                if not math.isnan(tr):
                    self.true_root = tr
            elif p[0] == 'STEP':
                self.algorithm_steps.append([safe_float(v) for v in p[1:]])
            elif p[0] == 'RESIDUAL' and len(p) >= 3:
                self.step_residuals[int(p[1])] = safe_float(p[2])

        if error_msg:
            messagebox.showerror("C Engine Error", error_msg)
            return

        if not self.algorithm_steps:
            messagebox.showwarning(
                "No Iterations Produced",
                "The C solver could not take a valid step (e.g., zero derivative or flat function values). Try adjusting your starting values."
            )
            return

        self._populate_results_view()

    def _populate_results_view(self):
        if self.true_root is not None and not math.isnan(self.true_root):
            self.stat_root.set(f"{self.true_root:.6f}")
        else:
            self.stat_root.set("N/A")

        self.tree.delete(*self.tree.get_children())
        m = self.method_var.get()

        for i, s in enumerate(self.algorithm_steps):
            xr_val = self._get_step_xr(s, m)
            res_val = self.step_residuals.get(i, float('nan'))
            res_str = f"{res_val:.3e}" if not math.isnan(res_val) else "N/A"
            self.tree.insert('', 'end', iid=str(i), values=(
                int(s[0]),
                f"{xr_val:.6f}",
                res_str,
                f"{s[-2] * 100:.4f}%",
                f"{s[-1]:.3e}"
            ))

        self.screen_input.pack_forget()
        self.screen_graph.pack(fill=tk.BOTH, expand=True)
        self._in_result_view = True

        if self.algorithm_steps:
            self._select_step(min(self.current_step, len(self.algorithm_steps) - 1))

    def _go_back(self):
        self.step_player.stop_play()
        self._in_result_view = False
        self.screen_graph.pack_forget()
        self.screen_input.pack(fill=tk.BOTH, expand=True)

    def _show_working_steps(self):
        m = self.method_var.get()
        title, formula, desc = METHOD_INFO.get(m, ("Root Solver", "", ""))
        lines = [f"Problem: Solve f(x) = {self.entry_eq.get()}   (Stopping Tolerance ε = {self.entry_tol.get()}%)"]
        for i, s in enumerate(self.algorithm_steps):
            it = int(s[0])
            res = self.step_residuals.get(i, float('nan'))
            ea_pct = s[-2] * 100.0
            if m in ('bisection', 'false_position', 'brent'):
                lines.append(
                    f"Iteration {it}:  Bracket [a={s[1]:.8g}, b={s[2]:.8g}]  ⇒  xr = {s[3]:.10g}  "
                    f"|f(xr)| = {res:.4e},  ε_a = {ea_pct:.5f}%,  Width = {abs(s[2]-s[1]):.4e}"
                )
            elif m in ('newton', 'modified_newton'):
                lines.append(
                    f"Iteration {it}:  x_{it} = {s[1]:.8g},  f(x_{it}) = {s[2]:.5e}  ⇒  x_{it+1} = {s[3]:.10g}  "
                    f"(|f(x_{it+1})| = {res:.4e},  ε_a = {ea_pct:.5f}%)"
                )
            elif m in ('secant', 'modified_secant'):
                lines.append(
                    f"Iteration {it}:  (x0={s[1]:.7g}, f0={s[2]:.4e}), (x1={s[3]:.7g}, f1={s[4]:.4e})  ⇒  x_next = {s[5]:.10g}  "
                    f"(|f(x_next)| = {res:.4e},  ε_a = {ea_pct:.5f}%)"
                )
            elif m == 'fixed_point':
                lines.append(
                    f"Iteration {it}:  x_{it} = {s[1]:.8g}  ⇒  x_{it+1} = g({s[1]:.8g}) = {s[2]:.10g}  "
                    f"(|g(x)-x| = {res:.4e},  ε_a = {ea_pct:.5f}%)"
                )
        show_working_steps_modal(self, title, formula, desc, lines)

    def _export_csv(self):
        if not self.algorithm_steps:
            return
        path = filedialog.asksaveasfilename(
            title="Export Iteration Trace to CSV",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            initialfile=f"root_trace_{self.method_var.get()}.csv"
        )
        if not path:
            return
        m = self.method_var.get()
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Method", m, "Equation", self.entry_eq.get(), "Tolerance(%)", self.entry_tol.get()])
                writer.writerow(["Iteration", "xr", "Residual |f(xr)|", "Approx Error (%)", "Ref Diff |x* - xr|"])
                for i, s in enumerate(self.algorithm_steps):
                    xr_val = self._get_step_xr(s, m)
                    res_val = self.step_residuals.get(i, float('nan'))
                    writer.writerow([int(s[0]), f"{xr_val:.10g}", f"{res_val:.10g}", f"{s[-2] * 100:.6f}", f"{s[-1]:.10g}"])
            messagebox.showinfo("Export Complete", f"Iteration table exported to:\n{path}")
        except Exception as ex:
            messagebox.showerror("Export Error", str(ex))

    def _on_scroll(self, event):
        if not event.inaxes:
            return
        f = 0.85 if event.button == 'up' else 1.15

        xmin, xmax = self.ax.get_xlim()
        self.ax.set_xlim(event.xdata + (xmin - event.xdata) * f, event.xdata + (xmax - event.xdata) * f)

        ymin, ymax = self.ax.get_ylim()
        self.ax.set_ylim(event.ydata + (ymin - event.ydata) * f, event.ydata + (ymax - event.ydata) * f)

        self.canvas.draw_idle()

    def _on_press(self, event):
        if event.inaxes and event.button == 1:
            self._panning = True
            self._pan_start = (event.x, event.y)
            self._start_xlim = self.ax.get_xlim()
            self. _start_ylim = self.ax.get_ylim()

    def _on_release(self, event):
        if event.button == 1:
            self._panning = False

    def _on_motion(self, event):
        if event.inaxes and event.xdata is not None and event.ydata is not None:
            self.lbl_coords.config(text=f"X: {event.xdata:.5f}  |  Y: {event.ydata:.5f}")
        else:
            self.lbl_coords.config(text="X: ---  |  Y: ---")

        if self._panning and event.inaxes:
            dx_pixel = event.x - self._pan_start[0]
            dy_pixel = event.y - self._pan_start[1]

            bbox = self.ax.get_window_extent()
            if bbox.width > 0 and bbox.height > 0:
                dx_data = dx_pixel * (self._start_xlim[1] - self._start_xlim[0]) / bbox.width
                dy_data = dy_pixel * (self._start_ylim[1] - self._start_ylim[0]) / bbox.height

                self.ax.set_xlim(self._start_xlim[0] - dx_data, self._start_xlim[1] - dx_data)
                self.ax.set_ylim(self._start_ylim[0] - dy_data, self._start_ylim[1] - dy_data)
                self.canvas.draw_idle()

    def _on_tree_select(self, event):
        selected = self.tree.selection()
        if selected:
            self.current_step = int(selected[0])
            self._update_frame(self.current_step)
            self.step_player.update_counter()

    def handle_keypress(self, event):
        if not self._in_result_view or not self.algorithm_steps:
            return
        if event.keysym in ('Right', 'space'):
            self.step_player.step_next()
        elif event.keysym == 'Left':
            self.step_player.step_prev()

    def get_state(self):
        return {
            'method': self.method_var.get(),
            'tol': self.entry_tol.get(),
            'eq': self.entry_eq.get(),
            'v1': self.entry_v1.get(),
            'v2': self.entry_v2.get(),
            'curve_x': list(self.curve_x),
            'curve_y': list(self.curve_y),
            'steps': list(self.algorithm_steps),
            'residuals': dict(self.step_residuals),
            'true_root': self.true_root,
            'current_step': self.current_step,
            'in_result_view': self._in_result_view,
        }

    def set_state(self, state):
        if not state:
            return
        self.method_var.set(state.get('method', 'bisection'))
        self.entry_tol.set(state.get('tol', '0.0001'))
        self.entry_eq.set(state.get('eq', 'x^3 - 2*x - 5'))
        self.entry_v1.set(state.get('v1', '1.5'))
        self.entry_v2.set(state.get('v2', '2.5'))
        self._toggle_inputs()

        self.curve_x = state.get('curve_x', [])
        self.curve_y = state.get('curve_y', [])
        self.algorithm_steps = state.get('steps', [])
        self.step_residuals = state.get('residuals', {})
        self.true_root = state.get('true_root', None)
        self.current_step = state.get('current_step', 0)
        if state.get('in_result_view') and self.algorithm_steps:
            self._populate_results_view()
