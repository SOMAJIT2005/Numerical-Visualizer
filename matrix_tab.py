import math
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from config import COLORS, FONTS, safe_float
from c_bridge import run_matrix_engine
from widgets import GlowButton, IconButton, PremiumEntry, SectionLabel, StatCard, ChipButton, StepControlBar, show_working_steps_modal


MATRIX_METHOD_INFO = {
    'gaussian': (
        "Gaussian Elimination with Partial Pivoting (C Engine)",
        "R_i ← R_i - (a_{ik} / a_{kk}) R_k   ⇒   x_i = (b_i - Σ_{j>i} u_{ij} x_j) / u_{ii}",
        "Reduces [A | b] to upper-triangular echelon form using partial pivoting (swapping largest |a_{ik}| into the pivot) followed by O(n²) back-substitution."
    ),
    'gauss_jordan': (
        "Gauss-Jordan RREF Reduction (C Engine)",
        "R_k ← R_k / a_{kk},   R_i ← R_i - a_{ik} R_k   (for all i ≠ k)   ⇒   [A | b] → [I | x]",
        "Normalizes each pivot to 1 and eliminates entries both above and below the pivot so the right-hand column becomes the solution vector x directly."
    ),
    'lu': (
        "PA = LU Factorization with Pivoting (C Engine)",
        "PA = LU   ⇒   Forward: L y = P b,   Backward: U x = y",
        "Decomposes permuted A into unit lower-triangular L (storing elimination multipliers) and upper-triangular U, then solves two triangular systems."
    ),
    'gauss_seidel': (
        "Gauss-Seidel Iterative Relaxation (C Engine)",
        "x_i^{(k+1)} = (b_i - Σ_{j<i} a_{ij} x_j^{(k+1)} - Σ_{j>i} a_{ij} x_j^{(k)}) / a_{ii}",
        "Uses the newest updated components x_j^{(k+1)} immediately within the same sweep. Guaranteed to converge if A is strictly diagonally dominant or SPD."
    ),
    'jacobi': (
        "Jacobi Simultaneous Iteration (C Engine)",
        "x_i^{(k+1)} = (b_i - Σ_{j≠i} a_{ij} x_j^{(k)}) / a_{ii}",
        "Computes all component updates simultaneously from the previous iteration vector x^{(k)} before updating x^{(k+1)}."
    ),
    'inverse': (
        "Gauss-Jordan Matrix Inversion (C Engine)",
        "[A | I_n]  ──(RREF)──►  [I_n | A⁻¹]   |   Verified by ||A A⁻¹ - I||_∞",
        "Augments A with the n×n identity matrix I and applies Gauss-Jordan elimination to transform the left block into I and the right block into A⁻¹."
    ),
}


class LinearSystemsTab(tk.Frame):
    def __init__(self, parent, go_home_callback):
        super().__init__(parent, bg=COLORS.bg_root)
        self.go_home_callback = go_home_callback
        self.steps = []
        self.current_step = 0
        self._in_result_view = False
        self.entries_A, self.entries_b = [], []
        self._saved_cells_A = {}
        self._saved_cells_b = {}
        self._last_solution_str = "---"
        self._last_residual_str = "---"
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

        SectionLabel(left_col, 'Matrix Solver Configuration (C Engine)', accent='amber').pack(anchor='w')

        card = tk.Frame(left_col, bg=COLORS.bg_card, padx=28, pady=20, highlightthickness=1, highlightbackground=COLORS.border)
        card.pack(pady=8, fill=tk.X)

        tk.Label(card, text="Solver Method", font=FONTS.SUBHEADING, bg=COLORS.bg_card, fg=COLORS.accent_cyan).pack(anchor='w', pady=(0, 8))
        self.method_var = tk.StringVar(value='gaussian')

        methods = [
            ('Gaussian Elimination', 'gaussian'),
            ('Gauss-Jordan Reduction', 'gauss_jordan'),
            ('LU Decomposition', 'lu'),
            ('Gauss-Seidel Iteration', 'gauss_seidel'),
            ('Jacobi Iteration', 'jacobi'),
            ('Matrix Inversion [A | I]', 'inverse')
        ]

        for text, val in methods:
            tk.Radiobutton(
                card, text=text, variable=self.method_var, value=val,
                bg=COLORS.bg_card, fg=COLORS.text_secondary, selectcolor=COLORS.bg_panel,
                font=FONTS.BODY, activebackground=COLORS.bg_card,
                activeforeground=COLORS.accent_cyan,
                command=self._toggle_inputs
            ).pack(anchor='w', pady=3)

        self.lbl_method_hint = tk.Label(
            card,
            text="",
            font=FONTS.SMALL,
            bg=COLORS.bg_card,
            fg=COLORS.text_muted,
            wraplength=310,
            justify='left'
        )
        self.lbl_method_hint.pack(anchor='w', pady=(6, 4))

        tk.Frame(card, height=1, bg=COLORS.border, width=310).pack(fill=tk.X, pady=12)

        self.options_container = tk.Frame(card, bg=COLORS.bg_card)
        self.options_container.pack(fill=tk.X)

        self.tol_frame = tk.Frame(self.options_container, bg=COLORS.bg_card)
        tk.Label(self.tol_frame, text="Stopping Tolerance ε (%):", bg=COLORS.bg_card, fg=COLORS.text_secondary, font=FONTS.SUBHEADING).pack(anchor='w', pady=(0, 2))
        self.entry_tol = PremiumEntry(self.tol_frame, width=22, default='0.0001')
        self.entry_tol.pack(fill=tk.X, pady=(0, 8))

        tk.Label(self.tol_frame, text="Max Iterations:", bg=COLORS.bg_card, fg=COLORS.text_secondary, font=FONTS.SUBHEADING).pack(anchor='w', pady=(0, 2))
        self.entry_max_iter = PremiumEntry(self.tol_frame, width=22, default='100')
        self.entry_max_iter.pack(fill=tk.X, pady=(0, 10))

        self.size_frame_container = tk.Frame(self.options_container, bg=COLORS.bg_card)
        self.size_frame_container.pack(fill=tk.X)
        tk.Label(self.size_frame_container, text="System Dimension (N × N)", font=FONTS.SUBHEADING, bg=COLORS.bg_card, fg=COLORS.accent_amber).pack(anchor='w', pady=(0, 8))

        size_frame = tk.Frame(self.size_frame_container, bg=COLORS.bg_card)
        size_frame.pack(anchor='w')

        self.n_var = tk.IntVar(value=3)
        ChipButton(size_frame, "  −  ", command=lambda: self._change_size(-1), bg=COLORS.bg_panel).pack(side=tk.LEFT)
        tk.Label(size_frame, textvariable=self.n_var, font=FONTS.TITLE, bg=COLORS.bg_card, fg=COLORS.text_primary, width=3).pack(side=tk.LEFT, padx=8)
        ChipButton(size_frame, "  +  ", command=lambda: self._change_size(1), bg=COLORS.bg_panel).pack(side=tk.LEFT)
        tk.Label(size_frame, text="(2×2 up to 5×5)", font=FONTS.SMALL, bg=COLORS.bg_card, fg=COLORS.text_muted).pack(side=tk.LEFT, padx=(10, 0))

        # ── RIGHT COLUMN (Grid & Action) ──
        right_col = tk.Frame(content_wrapper, bg=COLORS.bg_root)
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20, 15), pady=5)

        SectionLabel(right_col, 'Augmented Matrix Editor [ A | b ]', accent='cyan').pack(anchor='w', pady=(34, 8))

        grid_container = tk.Frame(right_col, bg=COLORS.bg_card, padx=26, pady=20, highlightthickness=1, highlightbackground=COLORS.border)
        grid_container.pack(fill=tk.BOTH, expand=True)

        # Presets toolbar
        preset_bar = tk.Frame(grid_container, bg=COLORS.bg_card)
        preset_bar.pack(fill=tk.X, pady=(0, 14))
        tk.Label(preset_bar, text="Presets:", font=FONTS.SMALL, bg=COLORS.bg_card, fg=COLORS.text_muted).pack(side=tk.LEFT, padx=(0, 6))
        ChipButton(preset_bar, "Textbook 3×3", command=lambda: self._load_preset('textbook'), bg=COLORS.bg_panel).pack(side=tk.LEFT, padx=3)
        ChipButton(preset_bar, "Diag. Dominant", command=lambda: self._load_preset('diag_dom'), accent=COLORS.accent_cyan, bg=COLORS.bg_panel).pack(side=tk.LEFT, padx=3)
        ChipButton(preset_bar, "Symmetric SPD", command=lambda: self._load_preset('spd'), bg=COLORS.bg_panel).pack(side=tk.LEFT, padx=3)
        ChipButton(preset_bar, "Upper Tri.", command=lambda: self._load_preset('upper_tri'), bg=COLORS.bg_panel).pack(side=tk.LEFT, padx=3)
        ChipButton(preset_bar, "Hilbert Ill-Cond", command=lambda: self._load_preset('hilbert'), accent=COLORS.accent_amber, bg=COLORS.bg_panel).pack(side=tk.LEFT, padx=3)
        ChipButton(preset_bar, "Identity", command=lambda: self._load_preset('identity'), bg=COLORS.bg_panel).pack(side=tk.LEFT, padx=3)
        ChipButton(preset_bar, "Clear 0", command=lambda: self._load_preset('zeros'), bg=COLORS.bg_panel).pack(side=tk.LEFT, padx=3)

        self.grid_frame = tk.Frame(grid_container, bg=COLORS.bg_card)
        self.grid_frame.pack(expand=True)

        self.lbl_matrix_diag = tk.Label(
            grid_container,
            text="",
            font=FONTS.MONO_SMALL,
            bg=COLORS.bg_card,
            fg=COLORS.accent_green,
            anchor='w'
        )
        self.lbl_matrix_diag.pack(fill=tk.X, pady=(12, 0))

        self._load_preset('textbook')
        self._toggle_inputs()

        action_bar = tk.Frame(right_col, bg=COLORS.bg_root)
        action_bar.pack(pady=(16, 4))
        GlowButton(action_bar, text='▶ SOLVE LINEAR SYSTEM (C ENGINE)', command=self._run_solver, accent='amber', width=340, height=54, bg=COLORS.bg_root).pack()

        # ── RESULT SCREEN ──
        self.screen_graph = tk.Frame(self, bg=COLORS.bg_root)

        dash_bar = tk.Frame(self.screen_graph, bg=COLORS.bg_root, pady=10, padx=20)
        dash_bar.pack(fill=tk.X)
        IconButton(dash_bar, '← BACK TO MATRIX', command=self._go_back, font=FONTS.SUBHEADING).pack(side=tk.LEFT, padx=(0, 16))

        self.stat_op = StatCard(dash_bar, "Current Operation", COLORS.accent_amber)
        self.stat_op.pack(side=tk.LEFT, padx=4)
        self.stat_sol = StatCard(dash_bar, "Solution Vector x", COLORS.accent_green)
        self.stat_sol.pack(side=tk.LEFT, padx=4)
        self.stat_res = StatCard(dash_bar, "Residual ||Ax - b||∞", COLORS.accent_cyan)
        self.stat_res.pack(side=tk.LEFT, padx=4)

        # Playback controls & Color guide bar
        ctrl_bar = tk.Frame(self.screen_graph, bg=COLORS.bg_root, padx=20, pady=4)
        ctrl_bar.pack(fill=tk.X)

        self.step_player = StepControlBar(
            ctrl_bar,
            on_step_change=self._select_step,
            get_total_steps=lambda: len(self.steps),
            get_current_step=lambda: self.current_step
        )
        self.step_player.pack(side=tk.LEFT)
        ChipButton(ctrl_bar, text="📖 Working Steps & Equation", command=self._show_working_steps, accent=COLORS.accent_amber, bg=COLORS.bg_card).pack(side=tk.LEFT, padx=(10, 4))

        legend_frame = tk.Frame(ctrl_bar, bg=COLORS.bg_card, padx=12, pady=6, highlightthickness=1, highlightbackground=COLORS.border)
        legend_frame.pack(side=tk.RIGHT)
        for dot_col, lbl_txt in [
            (COLORS.accent_amber, "● Diagonal Pivot"),
            (COLORS.accent_cyan, "● Matrix A"),
            (COLORS.accent_green, "● Vector b / A⁻¹"),
            (COLORS.accent_red, "■ Modified in Step"),
        ]:
            tk.Label(legend_frame, text=lbl_txt, font=FONTS.SMALL, bg=COLORS.bg_card, fg=dot_col, padx=6).pack(side=tk.LEFT)

        main_res = tk.Frame(self.screen_graph, bg=COLORS.bg_root)
        main_res.pack(fill=tk.BOTH, expand=True, padx=20, pady=(6, 16))

        graph_container = tk.Frame(main_res, bg=COLORS.bg_card, highlightthickness=1, highlightbackground=COLORS.border)
        graph_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.fig = Figure(figsize=(8.6, 5.6), facecolor=COLORS.plot_face)
        self.fig.subplots_adjust(left=0.05, bottom=0.05, right=0.95, top=0.95)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(COLORS.plot_axes)

        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_container)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        table_frame = tk.Frame(main_res, bg=COLORS.bg_card, highlightthickness=1, highlightbackground=COLORS.border)
        table_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(14, 0))

        self.tree = ttk.Treeview(table_frame, columns=('step', 'action'), show='headings', height=22)
        for col, head, w in zip(self.tree['columns'], ('Step', 'Row / Iterative Operation'), (52, 275)):
            self.tree.heading(col, text=head)
            self.tree.column(col, width=w, anchor='w' if col == 'action' else 'center')

        tree_scroll = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.Y)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)

    def _toggle_inputs(self):
        m = self.method_var.get()
        title, eq_s, desc_s = MATRIX_METHOD_INFO.get(m, ("Matrix Solver", "", ""))
        self.lbl_method_hint.config(text=f"{title}\nFormula: {eq_s}\n{desc_s}")
        if m in ('gauss_seidel', 'jacobi'):
            self.tol_frame.pack(fill=tk.X, before=self.size_frame_container)
        else:
            self.tol_frame.pack_forget()
        self._inspect_matrix_properties()

    def _snapshot_current_grid(self):
        for i, row in enumerate(self.entries_A):
            for j, e in enumerate(row):
                self._saved_cells_A[(i, j)] = e.get()
        for i, e in enumerate(self.entries_b):
            self._saved_cells_b[i] = e.get()

    def _change_size(self, delta):
        new_n = self.n_var.get() + delta
        if 2 <= new_n <= 5:
            self._snapshot_current_grid()
            self.n_var.set(new_n)
            self._build_grid(preserve=True)
            self._inspect_matrix_properties()

    def _build_grid(self, preserve=False):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        n = self.n_var.get()
        self.entries_A, self.entries_b = [], []

        for j in range(n):
            tk.Label(self.grid_frame, text=f"x{j+1}", font=FONTS.MONO_SMALL, bg=COLORS.bg_card, fg=COLORS.accent_cyan).grid(row=0, column=j, pady=(0, 4))
        tk.Label(self.grid_frame, text="b", font=FONTS.MONO_SMALL, bg=COLORS.bg_card, fg=COLORS.accent_green).grid(row=0, column=n + 1, pady=(0, 4))

        for i in range(n):
            row_entries = []
            for j in range(n):
                default_val = self._saved_cells_A.get((i, j), '1' if i == j else '0') if preserve else ('1' if i == j else '0')
                e = PremiumEntry(self.grid_frame, width=7, default=default_val)
                e.grid(row=i + 1, column=j, padx=4, pady=4)
                e._entry.bind('<KeyRelease>', lambda ev: self._inspect_matrix_properties())
                row_entries.append(e)
            self.entries_A.append(row_entries)
            tk.Frame(self.grid_frame, width=2, bg=COLORS.border).grid(row=i + 1, column=n, padx=8, sticky='ns')
            default_b = self._saved_cells_b.get(i, str(i + 1)) if preserve else str(i + 1)
            e_b = PremiumEntry(self.grid_frame, width=7, default=default_b)
            e_b.grid(row=i + 1, column=n + 1, padx=4, pady=4)
            e_b._entry.bind('<KeyRelease>', lambda ev: self._inspect_matrix_properties())
            self.entries_b.append(e_b)

    def _load_preset(self, preset_name):
        if preset_name == 'textbook':
            self.n_var.set(3)
            A = [[2, 1, -1], [-3, -1, 2], [-2, 1, 2]]
            b = [8, -11, -3]
        elif preset_name == 'diag_dom':
            self.n_var.set(3)
            A = [[10, -1, 2], [-1, 11, -1], [2, -1, 10]]
            b = [6, 25, -11]
        elif preset_name == 'spd':
            self.n_var.set(3)
            A = [[4, 1, 1], [1, 3, 0], [1, 0, 2]]
            b = [6, 4, 3]
        elif preset_name == 'upper_tri':
            self.n_var.set(3)
            A = [[2, 3, -1], [0, 4, 2], [0, 0, 5]]
            b = [7, 10, 15]
        elif preset_name == 'hilbert':
            self.n_var.set(3)
            A = [[1.0, 0.5, 0.333333], [0.5, 0.333333, 0.25], [0.333333, 0.25, 0.2]]
            b = [1.833333, 1.083333, 0.783333]
        elif preset_name == 'identity':
            n = self.n_var.get()
            A = [[1 if i == j else 0 for j in range(n)] for i in range(n)]
            b = [i + 1 for i in range(n)]
        else:
            n = self.n_var.get()
            A = [[0 for _ in range(n)] for _ in range(n)]
            b = [0 for _ in range(n)]

        self._saved_cells_A.clear()
        self._saved_cells_b.clear()
        n = len(A)
        for i in range(n):
            for j in range(n):
                self._saved_cells_A[(i, j)] = str(A[i][j])
            self._saved_cells_b[i] = str(b[i])
        self._build_grid(preserve=True)
        self._inspect_matrix_properties()

    def _read_matrix_flat(self):
        n = self.n_var.get()
        flat_A = []
        flat_b = []
        for i in range(n):
            for j in range(n):
                raw = self.entries_A[i][j].get().strip()
                v = float(raw) if raw else 0.0
                if not math.isfinite(v):
                    raise ValueError("Non-finite entry")
                flat_A.append(v)
            raw_b = self.entries_b[i].get().strip()
            vb = float(raw_b) if raw_b else 0.0
            if not math.isfinite(vb):
                raise ValueError("Non-finite entry")
            flat_b.append(vb)
        return n, flat_A, flat_b

    def _inspect_matrix_properties(self):
        try:
            n, flat_A, _ = self._read_matrix_flat()
            lines = run_matrix_engine(["diagnostics", n, *flat_A])
            det, cond, is_sym, is_dd, is_spd = 0.0, float('inf'), 0, 0, 0
            for line in lines:
                parts = line.split(',')
                if parts[0] == 'DIAG' and len(parts) >= 5:
                    det = safe_float(parts[1])
                    cond = safe_float(parts[2])
                    is_sym = int(parts[3])
                    is_dd = int(parts[4])
                    if len(parts) >= 6:
                        is_spd = int(parts[5])

            props = []
            if abs(det) < 1e-11:
                props.append("⚠ Singular / Near-Singular (det ≈ 0)")
                col = COLORS.accent_red
            else:
                props.append(f"✓ Nonsingular (det = {det:.3g}, κ∞ = {cond:.3g})")
                col = COLORS.accent_green

            if is_dd:
                props.append("Diagonally Dominant")
            elif self.method_var.get() == 'gauss_seidel':
                props.append("Not Diag. Dominant (GS may diverge)")
                col = COLORS.accent_amber

            if is_spd:
                props.append("Symmetric Positive Definite (SPD)")
            elif is_sym:
                props.append("Symmetric")

            self.lbl_matrix_diag.config(text=f"C Diagnostics ({n}×{n}):  " + "  •  ".join(props), fg=col)
        except Exception:
            self.lbl_matrix_diag.config(text="⚠ Enter valid numeric coefficients in all matrix cells.", fg=COLORS.accent_red)

    def _run_solver(self):
        self.focus_set()
        try:
            n, flat_A, flat_b = self._read_matrix_flat()
        except Exception:
            messagebox.showwarning("Invalid Matrix Entries", "All matrix cells must contain valid finite numbers.")
            return

        m = self.method_var.get()
        try:
            tol = float(self.entry_tol.get())
            max_iter = int(self.entry_max_iter.get())
            if tol <= 0 or max_iter <= 0:
                raise ValueError()
        except Exception:
            messagebox.showwarning("Invalid Parameters", "Tolerance must be positive and Max Iterations must be a positive integer.")
            return

        def worker():
            try:
                args = [m, str(n), *[str(v) for v in flat_A]]
                if m != 'inverse':
                    args.extend([str(v) for v in flat_b])
                    args.append(str(tol))
                    args.append(str(max_iter))
                lines = run_matrix_engine(args)
                self.after(0, lambda: self._handle_matrix_results("\n".join(lines)))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("C Matrix Solver Error", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _handle_matrix_results(self, stdout_text):
        error_msg = self._parse_solver_output(stdout_text)
        if error_msg:
            messagebox.showerror("C Matrix Solver Error", error_msg)
            return

        if not self.steps:
            messagebox.showwarning("No Steps Produced", "The C matrix solver did not produce any transformation steps.")
            return

        self._populate_results_view()

    def _populate_results_view(self):
        self.stat_sol.set(self._last_solution_str)
        self.stat_res.set(self._last_residual_str)

        self.tree.delete(*self.tree.get_children())
        for i, step in enumerate(self.steps):
            action_text = step.get('op_text', '')
            if not action_text:
                action_text = step.get('desc', 'State Update')
            self.tree.insert('', 'end', iid=str(i), values=(i, action_text))

        self.screen_input.pack_forget()
        self.screen_graph.pack(fill=tk.BOTH, expand=True)
        self._in_result_view = True

        if self.steps:
            self._select_step(min(self.current_step, len(self.steps) - 1))

    def _parse_solver_output(self, output):
        self.steps = []
        current_desc, op_text, target_row, target_row_2 = "Initial Configuration", "", -1, -1
        temp_matrix, expected_rows = [], 0
        backsolve_summary = []
        self._last_solution_str = "---"
        self._last_residual_str = "---"

        for line in output.splitlines():
            parts = line.split(',')
            if not parts:
                continue

            if parts[0] == 'ERROR':
                return ",".join(parts[1:])
            elif parts[0] == 'DIAG' and len(parts) >= 5:
                det = safe_float(parts[1])
                if self.method_var.get() == 'inverse':
                    self._last_solution_str = f"det(A) = {det:.4g}  (Invertible)"
            elif parts[0] == 'SOLUTION':
                sol_vals = [safe_float(v) for v in parts[1:]]
                sol_parts = ", ".join(f"x{i+1}={v:.3f}" for i, v in enumerate(sol_vals))
                self._last_solution_str = f"[{sol_parts}]"
            elif parts[0] == 'RESIDUAL' and len(parts) >= 2:
                res_v = safe_float(parts[1])
                if self.method_var.get() == 'inverse':
                    self._last_residual_str = f"||AA⁻¹ - I|| = {res_v:.2e}"
                else:
                    self._last_residual_str = f"{res_v:.3e}"
            elif parts[0] == 'SWAP':
                r1, r2 = int(parts[1]), int(parts[3])
                current_desc = f"Swapped Row {r1+1} and Row {r2+1}"
                op_text = f"R{r1+1} ↔ R{r2+1}"
                target_row, target_row_2 = r1, r2
            elif parts[0] == 'ELIMINATE':
                src, tgt, factor = int(parts[1]), int(parts[2]), float(parts[4])
                current_desc = f"Eliminated Row {tgt+1} using Row {src+1}"
                sign = "+" if factor < 0 else "-"
                op_text = f"R{tgt+1} → R{tgt+1} {sign} {abs(factor):.2f} R{src+1}"
                target_row, target_row_2 = tgt, -1
            elif parts[0] == 'NORMALIZE':
                tgt, diag = int(parts[1]), float(parts[2])
                current_desc = f"Normalized Row {tgt+1}"
                op_text = f"R{tgt+1} → R{tgt+1} / {diag:.2f}"
                target_row, target_row_2 = tgt, -1
            elif parts[0] == 'BACKSOLVE':
                tgt = int(parts[1])
                val = float(parts[2])
                current_desc = f"Back-Substitution: x_{tgt+1} = {val:.4f}"
                op_text = f"x_{tgt+1} = {val:.4f}"
                target_row, target_row_2 = tgt, -1
                if self.method_var.get() == 'gaussian':
                    backsolve_summary.append(f"$x_{{{tgt+1}}} = {val:.5f}$")
            elif parts[0] == 'FORWARDSOLVE':
                tgt = int(parts[1])
                current_desc = f"Forward-Substitution: y_{tgt+1} = {float(parts[2]):.4f}"
                op_text = f"y_{tgt+1} = {float(parts[2]):.4f}"
                target_row, target_row_2 = tgt, -1
            elif parts[0] == 'INFO':
                current_desc = parts[1]
                op_text, target_row, target_row_2 = "", -1, -1

            elif parts[0] == 'MATRIX':
                temp_matrix = []
                expected_rows = int(parts[2])
            elif parts[0] == 'ROW':
                temp_matrix.append([float(x) for x in parts[2:]])
                if len(temp_matrix) == expected_rows:
                    self.steps.append({
                        'type': 'matrix',
                        'matrix': temp_matrix,
                        'desc': current_desc,
                        'op_text': op_text,
                        'target_row': target_row,
                        'target_row_2': target_row_2
                    })

            elif parts[0] == 'GS_ITER_START':
                current_desc = f"Gauss-Seidel Iteration {parts[1]}"
                temp_matrix = []
            elif parts[0] == 'GS_EQ':
                clean_eq = ",".join(parts[1:])
                clean_eq = clean_eq.replace(r'\big[', '[').replace(r'\big]', ']')
                clean_eq = clean_eq.replace(r'\%', '').replace('%', '')
                clean_eq = clean_eq.replace(r'\\epsilon', r'\epsilon')
                temp_matrix.append(clean_eq)

            elif parts[0] == 'GS_ITER_END':
                self.steps.append({'type': 'equations', 'data': temp_matrix, 'desc': current_desc, 'op_text': current_desc})

        if backsolve_summary:
            self.steps.append({
                'type': 'equations',
                'data': list(reversed(backsolve_summary)),
                'desc': 'Back-Substitution Solution Vector',
                'op_text': 'Back-Substitution Complete'
            })

        return None

    def _select_step(self, idx):
        if not self.steps:
            return
        self.current_step = max(0, min(len(self.steps) - 1, idx))
        iid = str(self.current_step)
        if self.tree.exists(iid):
            self.tree.selection_set(iid)
            self.tree.see(iid)
        self._draw_matrix(self.current_step)
        self.step_player.update_counter()

    def _draw_matrix(self, idx):
        self.ax.clear()
        self.ax.axis('off')
        if not self.steps:
            return

        step_data = self.steps[idx]
        self.stat_op.set(f"{step_data['desc']}")

        if step_data.get('type') == 'equations':
            eqs = step_data['data']
            n_eq = len(eqs)
            spacing = min(0.18, 0.8 / n_eq) if n_eq > 0 else 0.15

            self.ax.text(0.02, 0.96, step_data['desc'], color=COLORS.accent_amber, fontsize=14, fontweight='bold', ha='left', va='center')
            for i, eq in enumerate(eqs):
                self.ax.text(
                    0.04, 0.84 - i * spacing, eq,
                    color=COLORS.accent_cyan,
                    fontsize=15, ha='left', va='center'
                )
            self.ax.set_xlim(0, 1)
            self.ax.set_ylim(0, 1)

        else:
            mat = step_data['matrix']
            prev_mat = self.steps[idx - 1]['matrix'] if idx > 0 and self.steps[idx - 1].get('type') == 'matrix' else None

            n = self.n_var.get()
            rows, cols = len(mat), len(mat[0]) if mat else 0

            if "Ly = Pb" in step_data['desc'] or "y_" in step_data.get('op_text', ''):
                self.ax.text(-0.9, -(rows - 1) / 2.0, "L =", color=COLORS.accent_cyan, fontsize=22, fontweight='bold', va='center', ha='right')
            elif "Ux = y" in step_data['desc'] or "x_" in step_data.get('op_text', ''):
                self.ax.text(-0.9, -(rows - 1) / 2.0, "U =", color=COLORS.accent_cyan, fontsize=22, fontweight='bold', va='center', ha='right')

            for i in range(rows):
                for j in range(cols):
                    val = mat[i][j]
                    color = COLORS.accent_green if j >= n and cols > n else COLORS.accent_cyan
                    if i == j and j < n:
                        color = COLORS.accent_amber

                    changed = False
                    if prev_mat and i < len(prev_mat) and j < len(prev_mat[i]):
                        if abs(val - prev_mat[i][j]) > 1e-9:
                            changed = True

                    text_val = "0.00" if abs(val) < 1e-10 else f"{val:.2f}"
                    if changed:
                        self.ax.text(
                            j, -i, text_val,
                            color=COLORS.text_primary, ha='center', va='center',
                            fontfamily='Consolas', fontsize=19, fontweight='heavy',
                            bbox=dict(facecolor=COLORS.accent_red, alpha=0.42, edgecolor=COLORS.accent_red, boxstyle='round,pad=0.25')
                        )
                    else:
                        self.ax.text(
                            j, -i, text_val,
                            color=color, ha='center', va='center',
                            fontfamily='Consolas', fontsize=18, fontweight='bold'
                        )

            if cols > n:
                self.ax.plot([n - 0.5, n - 0.5], [0.5, -rows + 0.5], color=COLORS.border, lw=2, ls='--')

            self.ax.plot([-0.55, -0.4], [0.5, 0.5], color=COLORS.text_secondary, lw=2.2)
            self.ax.plot([-0.55, -0.55], [0.5, -rows + 0.5], color=COLORS.text_secondary, lw=2.2)
            self.ax.plot([-0.55, -0.4], [-rows + 0.5, -rows + 0.5], color=COLORS.text_secondary, lw=2.2)

            self.ax.plot([cols - 0.6, cols - 0.45], [0.5, 0.5], color=COLORS.text_secondary, lw=2.2)
            self.ax.plot([cols - 0.45, cols - 0.45], [0.5, -rows + 0.5], color=COLORS.text_secondary, lw=2.2)
            self.ax.plot([cols - 0.6, cols - 0.45], [-rows + 0.5, -rows + 0.5], color=COLORS.text_secondary, lw=2.2)

            op_text = step_data.get('op_text', '')
            tr1 = step_data.get('target_row', -1)
            tr2 = step_data.get('target_row_2', -1)
            if op_text and tr1 != -1:
                self.ax.text(cols - 0.15, -tr1, op_text, color=COLORS.accent_red, fontsize=14, va='center', fontweight='bold')
                if tr2 != -1:
                    self.ax.text(cols - 0.15, -tr2, op_text, color=COLORS.accent_red, fontsize=14, va='center', fontweight='bold')

            self.ax.set_xlim(-1.8, cols + 2.4)
            self.ax.set_ylim(-rows, 1)

        self.canvas.draw_idle()

    def _go_back(self):
        self.step_player.stop_play()
        self._in_result_view = False
        self.screen_graph.pack_forget()
        self.screen_input.pack(fill=tk.BOTH, expand=True)

    def _show_working_steps(self):
        m = self.method_var.get()
        title, eq_s, desc_s = MATRIX_METHOD_INFO.get(m, ("Matrix Solver", "", ""))
        lines = [f"Final Solution: {self._last_solution_str}   |   Residual Check: {self._last_residual_str}"]
        for i, st in enumerate(self.steps):
            op = st.get('op_text') or st.get('desc', '')
            lines.append(f"Step {i}:  {st.get('desc', '')}   [{op}]")
            if st.get('type') == 'equations':
                for eq_line in st.get('data', []):
                    lines.append(f"      {eq_line}")
            elif st.get('type') == 'matrix':
                for r_idx, row in enumerate(st.get('matrix', [])):
                    row_fmt = "  ".join(f"{v:8.4f}" for v in row)
                    lines.append(f"      Row {r_idx+1}: [ {row_fmt} ]")
        show_working_steps_modal(self, title, eq_s, desc_s, lines)

    def _on_tree_select(self, event):
        selected = self.tree.selection()
        if selected:
            self.current_step = int(selected[0])
            self._draw_matrix(self.current_step)
            self.step_player.update_counter()

    def handle_keypress(self, event):
        if not self._in_result_view or not self.steps:
            return
        if event.keysym in ('Right', 'space'):
            self.step_player.step_next()
        elif event.keysym == 'Left':
            self.step_player.step_prev()

    def get_state(self):
        self._snapshot_current_grid()
        return {
            'method': self.method_var.get(),
            'tol': self.entry_tol.get(),
            'max_iter': self.entry_max_iter.get(),
            'n': self.n_var.get(),
            'cells_A': dict(self._saved_cells_A),
            'cells_b': dict(self._saved_cells_b),
            'steps': list(self.steps),
            'current_step': self.current_step,
            'in_result_view': self._in_result_view,
            'sol_str': self._last_solution_str,
            'res_str': self._last_residual_str,
        }

    def set_state(self, state):
        if not state:
            return
        self.method_var.set(state.get('method', 'gaussian'))
        self.entry_tol.set(state.get('tol', '0.0001'))
        self.entry_max_iter.set(state.get('max_iter', '100'))
        self.n_var.set(state.get('n', 3))
        self._saved_cells_A = dict(state.get('cells_A', {}))
        self._saved_cells_b = dict(state.get('cells_b', {}))
        self._build_grid(preserve=True)
        self._toggle_inputs()

        self.steps = state.get('steps', [])
        self.current_step = state.get('current_step', 0)
        self._last_solution_str = state.get('sol_str', '---')
        self._last_residual_str = state.get('res_str', '---')
        if state.get('in_result_view') and self.steps:
            self._populate_results_view()
