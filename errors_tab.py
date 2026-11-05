import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from config import COLORS, FONTS, safe_float
from c_bridge import run_numlab_engine
from widgets import GlowButton, IconButton, PremiumEntry, SectionLabel, StatCard, MethodBanner, show_working_steps_modal


ERRORS_METHOD_INFO = {
    'u_curve': (
        "Truncation vs. Round-Off Error Tradeoff (Finite-Difference U-Curve)",
        "f'(x0) ≈ [f(x0 + h) - f(x0 - h)] / (2h) + O(h²)   |   E_total(h) ≈ (M/6)h² + ε_mach / h",
        "As step size h decreases, Taylor truncation error O(h²) shrinks until IEEE-754 subtractive cancellation (ε_mach / h) dominates near h* ≈ ε_mach^(1/3) ≈ 10⁻⁵."
    ),
    'taylor': (
        "Taylor Series Polynomial Approximation & Remainder",
        "P_N(x) = Σ_{k=0}^N [f^(k)(x0) / k!] (x - x0)^k   |   R_N(x) = |f(x) - P_N(x)|",
        "Approximates smooth functions locally around x0 using successive higher-order derivatives; truncation remainder R_N decreases as degree N increases."
    ),
    'cancellation': (
        "Catastrophic Subtractive Cancellation & Algebraic Rationalization",
        "Naive: √(x² + 1) - x   ⇒   Rationalized: 1 / (√(x² + 1) + x)",
        "Subtracting two nearly equal floating-point numbers (√(x²+1) ≈ x for large x) erases leading mantissa bits; multiplying by the conjugate eliminates the subtraction."
    ),
    'ieee754': (
        "IEEE-754 64-Bit Double Precision & Scarborough Significant-Figure Criterion",
        "x = (-1)^S × (1.M)_2 × 2^(E - 1023)   |   ε_s = (0.5 × 10^(2 - p)) %",
        "Inspects the exact 1-bit sign, 11-bit biased exponent, and 52-bit mantissa of a C double, and computes Scarborough's stopping criterion for p significant figures."
    ),
}


class ErrorsApproximationsTab(tk.Frame):
    """Unit 1 — Numerical Approximations, Taylor Series & Round-Off Error Lab (C Engine)."""
    def __init__(self, parent, go_home_callback):
        super().__init__(parent, bg=COLORS.bg_root)
        self.go_home_callback = go_home_callback
        self._working_steps = []
        self._build_ui()

    def _build_ui(self):
        wrapper = tk.Frame(self, bg=COLORS.bg_root)
        wrapper.pack(fill=tk.BOTH, expand=True, padx=24, pady=10)

        left_col = tk.Frame(wrapper, bg=COLORS.bg_root, width=410)
        left_col.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 20), pady=5)

        nav_row = tk.Frame(left_col, bg=COLORS.bg_root)
        nav_row.pack(fill=tk.X, pady=(0, 8))
        IconButton(nav_row, '← Back to Dashboard', command=self.go_home_callback, font=FONTS.SUBHEADING).pack(side=tk.LEFT)

        SectionLabel(left_col, 'Unit 1: Approximations & Round-Off Lab (C)', accent='cyan').pack(anchor='w')

        card = tk.Frame(left_col, bg=COLORS.bg_card, padx=22, pady=16, highlightthickness=1, highlightbackground=COLORS.border)
        card.pack(pady=8, fill=tk.X)

        tk.Label(card, text="Interactive Experiment (C Engine)", font=FONTS.SUBHEADING, bg=COLORS.bg_card, fg=COLORS.accent_cyan).pack(anchor='w', pady=(0, 6))
        self.lab_var = tk.StringVar(value='u_curve')
        labs = [
            ('Truncation vs. Round-Off (Finite Diff. U-Curve)', 'u_curve'),
            ('Taylor Series Polynomial Approximation', 'taylor'),
            ('Catastrophic Cancellation (sqrt(x²+1) - x)', 'cancellation'),
            ('Significant Figures & IEEE-754 Float Inspector', 'ieee754'),
        ]
        for text, val in labs:
            tk.Radiobutton(
                card, text=text, variable=self.lab_var, value=val,
                bg=COLORS.bg_card, fg=COLORS.text_secondary, selectcolor=COLORS.bg_panel,
                font=FONTS.BODY, activebackground=COLORS.bg_card,
                activeforeground=COLORS.accent_cyan, command=self._on_lab_change
            ).pack(anchor='w', pady=2)

        tk.Frame(card, height=1, bg=COLORS.border).pack(fill=tk.X, pady=10)

        self.param_frame = tk.Frame(card, bg=COLORS.bg_card)
        self.param_frame.pack(fill=tk.X)

        self.lbl_p1 = tk.Label(self.param_frame, text="Function f(x):", bg=COLORS.bg_card, fg=COLORS.text_secondary, font=FONTS.SUBHEADING)
        self.lbl_p1.pack(anchor='w', pady=(0, 2))
        self.entry_p1 = PremiumEntry(self.param_frame, width=30, default='sin(x)')
        self.entry_p1.pack(fill=tk.X, pady=(0, 8))

        self.lbl_p2 = tk.Label(self.param_frame, text="Evaluation Point x0:", bg=COLORS.bg_card, fg=COLORS.text_secondary, font=FONTS.SUBHEADING)
        self.lbl_p2.pack(anchor='w', pady=(0, 2))
        self.entry_p2 = PremiumEntry(self.param_frame, width=30, default='1.0')
        self.entry_p2.pack(fill=tk.X, pady=(0, 8))

        self.lbl_p3 = tk.Label(self.param_frame, text="Target x / Degree N:", bg=COLORS.bg_card, fg=COLORS.text_secondary, font=FONTS.SUBHEADING)
        self.lbl_p3.pack(anchor='w', pady=(0, 2))
        self.entry_p3 = PremiumEntry(self.param_frame, width=30, default='5')
        self.entry_p3.pack(fill=tk.X, pady=(0, 8))

        GlowButton(left_col, text='▶ RUN EXPERIMENT (C ENGINE)', command=self._run_experiment, width=340, height=50, bg=COLORS.bg_root).pack(pady=(10, 0))

        right_col = tk.Frame(wrapper, bg=COLORS.bg_root)
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)

        stats_row = tk.Frame(right_col, bg=COLORS.bg_root)
        stats_row.pack(fill=tk.X, pady=(0, 8))
        self.stat_1 = StatCard(stats_row, "Optimal / Exact Value", COLORS.accent_cyan)
        self.stat_1.pack(side=tk.LEFT, padx=(0, 6))
        self.stat_2 = StatCard(stats_row, "Approximate Value", COLORS.accent_amber)
        self.stat_2.pack(side=tk.LEFT, padx=6)
        self.stat_3 = StatCard(stats_row, "Absolute Error Et", COLORS.accent_green)
        self.stat_3.pack(side=tk.LEFT, padx=6)
        self.stat_4 = StatCard(stats_row, "Relative Error εt (%)", COLORS.accent_red)
        self.stat_4.pack(side=tk.LEFT, padx=6)

        self.method_banner = MethodBanner(right_col, on_show_steps=self._show_working_steps)
        self.method_banner.pack(fill=tk.X, pady=(0, 6))

        self.lbl_insight = tk.Label(
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
        self.lbl_insight.pack(fill=tk.X, pady=(0, 8))

        viz_split = tk.Frame(right_col, bg=COLORS.bg_root)
        viz_split.pack(fill=tk.BOTH, expand=True)

        graph_card = tk.Frame(viz_split, bg=COLORS.bg_card, highlightthickness=1, highlightbackground=COLORS.border)
        graph_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.fig = Figure(figsize=(6.8, 4.8), facecolor=COLORS.plot_face)
        self.fig.subplots_adjust(left=0.11, bottom=0.11, right=0.96, top=0.92)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(COLORS.plot_axes)
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_card)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        table_card = tk.Frame(viz_split, bg=COLORS.bg_card, highlightthickness=1, highlightbackground=COLORS.border)
        table_card.pack(side=tk.RIGHT, fill=tk.Y, padx=(12, 0))

        self.tree = ttk.Treeview(table_card, columns=('c1', 'c2', 'c3', 'c4'), show='headings', height=20)
        for col, head, w in zip(('c1', 'c2', 'c3', 'c4'), ('Param', 'Value', 'Abs Error', 'Rel Error (%)'), (80, 105, 100, 100)):
            self.tree.heading(col, text=head)
            self.tree.column(col, width=w, anchor='center')
        self.tree.pack(fill=tk.Y, expand=True)

        self._on_lab_change()

    def _on_lab_change(self):
        mode = self.lab_var.get()
        if mode == 'u_curve':
            self.lbl_p1.config(text="Function f(x):")
            self.entry_p1.set("sin(x)")
            self.lbl_p2.config(text="Point x0:")
            self.entry_p2.set("1.0")
            self.lbl_p3.config(text="(Auto-Evaluated by C Engine):")
            self.entry_p3.set("Richardson Order 4")
        elif mode == 'taylor':
            self.lbl_p1.config(text="Function f(x):")
            self.entry_p1.set("sin(x)")
            self.lbl_p2.config(text="Target x_eval (around x0=0):")
            self.entry_p2.set("1.2")
            self.lbl_p3.config(text="Max Polynomial Degree N (1–8):")
            self.entry_p3.set("5")
        elif mode == 'cancellation':
            self.lbl_p1.config(text="Unstable Formula (in C):")
            self.entry_p1.set("sqrt(x^2 + 1) - x")
            self.lbl_p2.config(text="Stable Equivalent (in C):")
            self.entry_p2.set("1 / (sqrt(x^2 + 1) + x)")
            self.lbl_p3.config(text="Max Exponent k (x = 10^k):")
            self.entry_p3.set("8")
        elif mode == 'ieee754':
            self.lbl_p1.config(text="Exact Value (64-bit double):")
            self.entry_p1.set("3.141592653589793")
            self.lbl_p2.config(text="Approximate Value:")
            self.entry_p2.set("3.1416")
            self.lbl_p3.config(text="Significant Figures p (1–15):")
            self.entry_p3.set("5")
        self._run_experiment()

    def _run_experiment(self):
        mode = self.lab_var.get()
        title, eq_str, desc_str = ERRORS_METHOD_INFO.get(mode, ("Unit 1 Lab", "", ""))
        self.method_banner.set_method(title, eq_str, desc_str)
        self._working_steps = []
        self.ax.clear()
        self.ax.set_facecolor(COLORS.plot_axes)
        self.ax.grid(True, color=COLORS.plot_grid, linestyle='--', alpha=0.4)
        self.tree.delete(*self.tree.get_children())

        try:
            if mode == 'u_curve':
                eq = self.entry_p1.get().strip()
                x0 = float(self.entry_p2.get())
                lines = run_numlab_engine(["errors_h_sweep", eq, x0])
                hs, fwd_errs, cen_errs, d2_errs = [], [], [], []
                df_exact, opt_h, min_err = 0.0, 1e-5, 0.0
                for line in lines:
                    p = line.split(',')
                    if p[0] == 'H_ROW' and len(p) >= 9:
                        h = safe_float(p[1])
                        fwd = safe_float(p[2])
                        cen = safe_float(p[4])
                        ef = safe_float(p[5])
                        ec = safe_float(p[7])
                        ed2 = safe_float(p[8])
                        hs.append(h)
                        fwd_errs.append(ef)
                        cen_errs.append(ec)
                        d2_errs.append(ed2)
                        self.tree.insert('', 'end', values=(f"{h:.1e}", f"{cen:.8f}", f"{ec:.2e}", f"{ed2:.2e}"))
                        if len(self._working_steps) < 25:
                            self._working_steps.append(
                                f"h = {h:.2e}:  D_fwd = [f({x0}+{h:.1e}) - f({x0})]/{h:.1e} = {fwd:.8f} (|E|={ef:.2e})  |  "
                                f"D_cen = [f({x0}+{h:.1e}) - f({x0}-{h:.1e})]/(2·{h:.1e}) = {cen:.8f} (|E|={ec:.2e})"
                            )
                    elif p[0] == 'META' and len(p) >= 6:
                        df_exact = safe_float(p[2])
                        opt_h = safe_float(p[4])
                        min_err = safe_float(p[5])
                self._working_steps.insert(0, f"Exact Derivative f'({x0}) = {df_exact:.10f},  Optimal Step Size h* = {opt_h:.2e} (Min Error = {min_err:.3e})")

                self.ax.loglog(hs, fwd_errs, '--', color=COLORS.accent_amber, lw=1.6, label='Forward Diff O(h)')
                self.ax.loglog(hs, cen_errs, '-', color=COLORS.accent_cyan, lw=2.2, label='Centered Diff O(h²)')
                self.ax.loglog(hs, d2_errs, ':', color=COLORS.accent_purple, lw=1.5, label='2nd Deriv O(h²)')
                self.ax.axvline(opt_h, color=COLORS.accent_green, ls=':', label=f'Optimal h* ≈ {opt_h:.1e}')
                self.ax.invert_xaxis()
                self.ax.set_xlabel('Step size h (decreasing →)', color=COLORS.text_secondary)
                self.ax.set_ylabel('Absolute Error |D_h - f\'(x0)|', color=COLORS.text_secondary)
                self.ax.set_title('C Engine: Truncation Error (large h) vs. Round-Off Error (tiny h)', color=COLORS.text_primary, fontsize=11)
                self.ax.legend(loc='best', facecolor=COLORS.bg_panel, edgecolor=COLORS.border, labelcolor=COLORS.text_primary)

                self.stat_1.set(f"{df_exact:.7f}")
                self.stat_2.set(f"h* = {opt_h:.1e}")
                self.stat_3.set(f"{min_err:.3e}")
                rel_pct = (min_err / abs(df_exact) * 100.0) if abs(df_exact) > 1e-14 else 0.0
                self.stat_4.set(f"{rel_pct:.3e}%")
                self.lbl_insight.config(
                    text=f"C Engine Insight: Shrinking h below {opt_h:.1e} INCREASES error due to IEEE-754 subtractive cancellation."
                )

            elif mode == 'taylor':
                eq = self.entry_p1.get().strip()
                x_target = float(self.entry_p2.get())
                order = max(1, min(8, int(self.entry_p3.get())))
                lines = run_numlab_engine(["errors_taylor", eq, 0.0, x_target, order])

                xs, y_true = [], []
                poly_curves = [[] for _ in range(order + 1)]
                true_val, approx_val, rem_final, rel_final = 0.0, 0.0, 0.0, 0.0

                for line in lines:
                    p = line.split(',')
                    if p[0] == 'TAYLOR_ROW' and len(p) >= 8:
                        k = int(p[1])
                        dk = safe_float(p[2])
                        ck = safe_float(p[3])
                        term = safe_float(p[4])
                        partial = safe_float(p[5])
                        rem = safe_float(p[6])
                        rel_pct = safe_float(p[7])
                        self.tree.insert('', 'end', values=(f"Deg {k}", f"{partial:.7f}", f"{rem:.3e}", f"{rel_pct:.3f}%"))
                        self._working_steps.append(
                            f"Term k={k}:  f^({k})(0) = {dk:.5g}  ⇒  c_{k} = {dk:.5g}/{k}! = {ck:.6g}  ⇒  "
                            f"c_{k}·({x_target})^{k} = {term:+.6g}  ⇒  P_{k}({x_target}) = {partial:.8f}  (|R_{k}| = {rem:.3e})"
                        )
                    elif p[0] == 'META' and len(p) >= 5:
                        true_val = safe_float(p[1])
                        approx_val = safe_float(p[2])
                        rem_final = safe_float(p[3])
                        rel_final = safe_float(p[4])
                    elif p[0] == 'CURVE' and len(p) >= 3 + order + 1:
                        xs.append(safe_float(p[1]))
                        y_true.append(safe_float(p[2]))
                        for k in range(order + 1):
                            poly_curves[k].append(safe_float(p[3 + k]))

                self.ax.plot(xs, y_true, color=COLORS.accent_cyan, lw=2.4, label=f'Exact {eq}')
                for k in range(order + 1):
                    if k in (1, 3, order):
                        col = COLORS.accent_amber if k == order else COLORS.text_muted
                        ls = '--' if k == order else ':'
                        self.ax.plot(xs, poly_curves[k], color=col, lw=2 if k == order else 1.2, ls=ls, label=f'Taylor P_{k}(x)')

                self.ax.scatter([x_target], [true_val], color=COLORS.accent_green, s=55, zorder=5, label=f'Exact f({x_target:g})')
                self.ax.scatter([x_target], [approx_val], color=COLORS.accent_amber, s=55, zorder=5, label=f'P_{order}({x_target:g})')
                self.ax.set_ylim(-3.5, 3.5)
                self.ax.set_title(f'C Engine: Taylor Polynomial Convergence (Degree N = {order})', color=COLORS.text_primary, fontsize=11)
                self.ax.legend(loc='best', facecolor=COLORS.bg_panel, edgecolor=COLORS.border, labelcolor=COLORS.text_primary)

                self.stat_1.set(f"{true_val:.7f}")
                self.stat_2.set(f"{approx_val:.7f}")
                self.stat_3.set(f"{rem_final:.3e}")
                self.stat_4.set(f"{rel_final:.4f}%")
                self.lbl_insight.config(text=f"C Engine Taylor Remainder R_{order}({x_target:g}) = {rem_final:.4e}.")

            elif mode == 'cancellation':
                lines = run_numlab_engine(["errors_cancellation"])
                xs_c, errs_c = [], []
                last_naive, last_stable, last_rel = 0.0, 0.0, 0.0
                for line in lines:
                    p = line.split(',')
                    if p[0] == 'CANCEL_ROW' and len(p) >= 7:
                        k = int(p[1])
                        xv = safe_float(p[2])
                        naive = safe_float(p[3])
                        stable = safe_float(p[4])
                        rel_err = safe_float(p[5])
                        lost = safe_float(p[6])
                        self.tree.insert('', 'end', values=(f"10^{k}", f"{naive:.4e}", f"{rel_err:.2e}", f"{lost:.1f} digits"))
                        self._working_steps.append(
                            f"x = 10^{k} ({xv:.0e}):  Naive √(x²+1)-x = {naive:.8e}  |  Stable 1/(√(x²+1)+x) = {stable:.8e}  "
                            f"⇒  Rel. Error = {rel_err:.2e} (~{lost:.1f} digits lost)"
                        )
                        last_naive, last_stable, last_rel = naive, stable, rel_err
                    elif p[0] == 'CURVE' and len(p) >= 3:
                        xs_c.append(safe_float(p[1]))
                        errs_c.append(safe_float(p[2]))

                self.ax.loglog(xs_c, errs_c, '-', color=COLORS.accent_red, lw=2.2, label='Relative Error of Naive sqrt(x²+1)-x')
                self.ax.set_xlabel('x (Log Scale)', color=COLORS.text_secondary)
                self.ax.set_ylabel('Relative Error [Log Scale]', color=COLORS.text_secondary)
                self.ax.set_title('C Engine: Catastrophic Cancellation vs. Rationalized Form', color=COLORS.text_primary, fontsize=11)
                self.ax.legend(loc='best', facecolor=COLORS.bg_panel, edgecolor=COLORS.border, labelcolor=COLORS.text_primary)

                self.stat_1.set(f"{last_stable:.5e}")
                self.stat_2.set(f"{last_naive:.5e}")
                self.stat_3.set(f"{abs(last_stable - last_naive):.3e}")
                self.stat_4.set(f"{last_rel * 100.0:.2f}%")
                self.lbl_insight.config(
                    text="C Engine Insight: Subtracting nearly equal C doubles wipes out mantissa bits; rationalizing preserves full precision!"
                )

            elif mode == 'ieee754':
                exact_val = float(self.entry_p1.get())
                approx_val = float(self.entry_p2.get())
                sig = max(1, min(15, int(self.entry_p3.get())))
                lines = run_numlab_engine(["errors_ieee754", exact_val, approx_val, sig])

                sign_s, exp_s, man_s = "0", "", ""
                eps, ulp, es_tol, abs_err, rel_pct = 0.0, 0.0, 0.0, 0.0, 0.0
                ps, es_list = [], []

                for line in lines:
                    p = line.split(',')
                    if p[0] == 'IEEE_BITS' and len(p) >= 6:
                        sign_s, exp_s, man_s = p[1], p[2], p[3]
                    elif p[0] == 'IEEE_METRICS' and len(p) >= 6:
                        eps = safe_float(p[1])
                        ulp = safe_float(p[2])
                        es_tol = safe_float(p[3])
                        abs_err = safe_float(p[4])
                        rel_pct = safe_float(p[5])
                    elif p[0] == 'SCARBROUGH' and len(p) >= 3:
                        p_idx = int(p[1])
                        es_v = safe_float(p[2])
                        ps.append(p_idx)
                        es_list.append(es_v)
                        self.tree.insert('', 'end', values=(f"p={p_idx} figs", f"Es={es_v:.2e}%", f"ULP={ulp:.2e}", f"ε={eps:.2e}"))

                self.ax.semilogy(ps, es_list, 'o-', color=COLORS.accent_cyan, lw=2, label='Scarborough Tolerance Es = 0.5×10^(2-p) %')
                self.ax.axhline(es_tol, color=COLORS.accent_amber, ls='--', label=f'Target Es (p={sig}) = {es_tol:.2e}%')
                self.ax.set_xlabel('Significant Figures (p)', color=COLORS.text_secondary)
                self.ax.set_ylabel('Stopping Tolerance Es (%)', color=COLORS.text_secondary)
                self.ax.set_title(f'C Engine IEEE-754 64-Bit Double Inspector (DBL_EPSILON = {eps:.2e})', color=COLORS.text_primary, fontsize=11)
                self.ax.legend(loc='best', facecolor=COLORS.bg_panel, edgecolor=COLORS.border, labelcolor=COLORS.text_primary)

                self.stat_1.set(f"{exact_val:.8g}")
                self.stat_2.set(f"{approx_val:.8g}")
                self.stat_3.set(f"{abs_err:.3e}")
                self.stat_4.set(f"{rel_pct:.4f}%")
                self.lbl_insight.config(text=f"C uint64_t Bits of {exact_val:g}:  S:{sign_s} | Exp:{exp_s} | Mantissa:{man_s[:28]}...  (ULP={ulp:.2e})")
                self._working_steps = [
                    f"Exact Input x* = {exact_val:.16g},   Approximation x = {approx_val:.16g}",
                    f"1. IEEE-754 64-Bit Layout:  Sign S = {sign_s},  Biased Exponent = {exp_s}_2,  Mantissa = 1.{man_s}_2",
                    f"2. Machine Epsilon ε_mach = {eps:.6e},   Unit in Last Place ULP({exact_val:g}) = {ulp:.6e}",
                    f"3. Absolute True Error E_t = |{exact_val:g} - {approx_val:g}| = {abs_err:.6e}",
                    f"4. Relative True Error ε_t = (E_t / |{exact_val:g}|) × 100% = {rel_pct:.6f}%",
                    f"5. Scarborough Stopping Tolerance for p={sig} sig. figs:  ε_s = 0.5 × 10^(2 - {sig})% = {es_tol:.4e}%",
                ]

            self.canvas.draw_idle()
        except Exception as ex:
            messagebox.showwarning("C Engine Experiment Error", str(ex))

    def _show_working_steps(self):
        mode = self.lab_var.get()
        title, eq_str, desc_str = ERRORS_METHOD_INFO.get(mode, ("Unit 1 Lab", "", ""))
        show_working_steps_modal(self, title, eq_str, desc_str, self._working_steps)

    def handle_keypress(self, event):
        pass

    def get_state(self):
        return {
            'lab': self.lab_var.get(),
            'p1': self.entry_p1.get(),
            'p2': self.entry_p2.get(),
            'p3': self.entry_p3.get(),
        }

    def set_state(self, state):
        if not state:
            return
        self.lab_var.set(state.get('lab', 'u_curve'))
        self.entry_p1.set(state.get('p1', 'sin(x)'))
        self.entry_p2.set(state.get('p2', '1.0'))
        self.entry_p3.set(state.get('p3', '5'))
        self._run_experiment()
