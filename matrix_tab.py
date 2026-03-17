import threading
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess, os, numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from config import COLORS, FONTS, resource_path
from widgets import GlowButton, IconButton, PremiumEntry, SectionLabel

class LinearSystemsTab(tk.Frame):
    def __init__(self, parent, go_home_callback):
        super().__init__(parent, bg=COLORS.bg)
        self.go_home_callback = go_home_callback
        self.steps = []
        self.current_step = 0
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
        SectionLabel(left_col, 'Matrix Configuration').pack(anchor='w')
        
        # Reduced padding slightly to prevent stretching
        card = tk.Frame(left_col, bg=COLORS.card, padx=35, pady=25, highlightthickness=1, highlightbackground=COLORS.border)
        card.pack(pady=15)

        tk.Label(card, text="Solver Method", font=FONTS['subheading'], bg=COLORS.card, fg=COLORS.accent_cyan).pack(anchor='w', pady=(0, 10))
        self.method_var = tk.StringVar(value='gaussian')
        
        methods = [('Gaussian Elimination', 'gaussian'), ('Gauss-Jordan', 'gauss_jordan'),
                   ('LU Decomposition', 'lu'), ('Gauss-Seidel Iteration', 'gauss_seidel')]
        
        for text, val in methods:
            tk.Radiobutton(card, text=text, variable=self.method_var, value=val, 
                           bg=COLORS.card, fg=COLORS.text_secondary, selectcolor=COLORS.bg_panel,
                           font=FONTS['heading'], activebackground=COLORS.card, 
                           activeforeground=COLORS.accent_cyan,
                           command=self._toggle_inputs).pack(anchor='w', pady=3)

        tk.Frame(card, height=1, bg=COLORS.border, width=300).pack(pady=15)

        self.options_container = tk.Frame(card, bg=COLORS.card)
        self.options_container.pack(fill=tk.X)

        # Tolerance & Max Iterations Frame
        self.tol_frame = tk.Frame(self.options_container, bg=COLORS.card)
        tk.Label(self.tol_frame, text="Tolerance (ε):", bg=COLORS.card, fg=COLORS.text_secondary, font=FONTS['subheading']).pack(anchor='w', pady=(0, 2))
        self.entry_tol = PremiumEntry(self.tol_frame, width=20, default='0.0001')
        self.entry_tol.pack(anchor='w', pady=(0, 10))

        tk.Label(self.tol_frame, text="Max Iterations:", bg=COLORS.card, fg=COLORS.text_secondary, font=FONTS['subheading']).pack(anchor='w', pady=(0, 2))
        self.entry_max_iter = PremiumEntry(self.tol_frame, width=20, default='100')
        self.entry_max_iter.pack(anchor='w', pady=(0, 10))

        # Size Configuration Frame
        self.size_frame_container = tk.Frame(self.options_container, bg=COLORS.card)
        self.size_frame_container.pack(fill=tk.X)
        tk.Label(self.size_frame_container, text="Matrix Size (N x N)", font=FONTS['subheading'], bg=COLORS.card, fg=COLORS.accent_amber).pack(anchor='w', pady=(0, 10))
        
        size_frame = tk.Frame(self.size_frame_container, bg=COLORS.card)
        size_frame.pack(anchor='w')
        
        self.n_var = tk.IntVar(value=3)
        IconButton(size_frame, "  -  ", font=FONTS['heading'], command=lambda: self._change_size(-1)).pack(side=tk.LEFT)
        tk.Label(size_frame, textvariable=self.n_var, font=FONTS['title'], bg=COLORS.card, fg=COLORS.text_primary, width=3).pack(side=tk.LEFT, padx=10)
        IconButton(size_frame, "  +  ", font=FONTS['heading'], command=lambda: self._change_size(1)).pack(side=tk.LEFT)

        self._toggle_inputs()

        # ── RIGHT COLUMN (Grid & Action) ──
        right_col = tk.Frame(content_wrapper, bg=COLORS.bg)
        right_col.pack(side=tk.LEFT, padx=(60, 0), anchor='n', pady=75) # pady=75 to perfectly align with the card content
        
        grid_container = tk.Frame(right_col, bg=COLORS.bg_panel, padx=30, pady=30, highlightthickness=1, highlightbackground=COLORS.border)
        grid_container.pack()
        
        tk.Label(grid_container, text="Augmented Matrix [ A | b ]", font=FONTS['heading'], bg=COLORS.bg_panel, fg=COLORS.text_secondary).pack(pady=(0, 20))
        self.grid_frame = tk.Frame(grid_container, bg=COLORS.bg_panel)
        self.grid_frame.pack()
        self._build_grid()

        # MOVED: Solve System button correctly placed under the Augmented Matrix
        GlowButton(right_col, text='▶ SOLVE SYSTEM', command=self._run_solver, width=340, height=65, bg=COLORS.bg).pack(pady=(40, 0))

        # ── RESULT SCREEN ──
        self.screen_graph = tk.Frame(self, bg=COLORS.bg)
        dash_bar = tk.Frame(self.screen_graph, bg=COLORS.bg, pady=15, padx=20)
        dash_bar.pack(fill=tk.X)
        IconButton(dash_bar, '← BACK', command=self._go_back).pack(side=tk.LEFT, padx=(0, 20))
        
        self.lbl_operation = tk.Label(dash_bar, text="Initial State", font=FONTS['heading'], bg=COLORS.bg, fg=COLORS.accent_amber)
        self.lbl_operation.pack(side=tk.LEFT, padx=20)

        main_res = tk.Frame(self.screen_graph, bg=COLORS.bg)
        main_res.pack(fill=tk.BOTH, expand=True, padx=40, pady=(0, 40))

        self.fig = Figure(figsize=(10, 6), facecolor=COLORS.bg)
        self.ax = self.fig.add_subplot(111); self.ax.set_facecolor(COLORS.plot_axes)
        self.canvas = FigureCanvasTkAgg(self.fig, master=main_res)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _toggle_inputs(self):
        if self.method_var.get() == 'gauss_seidel':
            self.tol_frame.pack(fill=tk.X, before=self.size_frame_container)
        else:
            self.tol_frame.pack_forget()

    def _change_size(self, delta):
        new_n = self.n_var.get() + delta
        if 2 <= new_n <= 5: 
            self.n_var.set(new_n); self._build_grid()

    def _build_grid(self):
        for widget in self.grid_frame.winfo_children(): widget.destroy()
        n = self.n_var.get()
        self.entries_A, self.entries_b = [], []
        
        for i in range(n):
            row_entries = []
            for j in range(n):
                e = PremiumEntry(self.grid_frame, width=6, default='1' if i == j else '0')
                e.grid(row=i, column=j, padx=5, pady=5)
                row_entries.append(e)
            self.entries_A.append(row_entries)
            tk.Frame(self.grid_frame, width=2, bg=COLORS.border_mid).grid(row=i, column=n, padx=10, sticky='ns')
            e_b = PremiumEntry(self.grid_frame, width=6, default=str(i+1))
            e_b.grid(row=i, column=n+1, padx=5, pady=5)
            self.entries_b.append(e_b)


    def _run_solver(self):
        self.focus_set()

        def worker():
            try:
                # Use resource_path to find the packed matrix engine
                exe = resource_path(os.path.join('build', 'matrix_engine.exe'))
                args = [exe, self.method_var.get(), str(self.n_var.get())]
                
                for row in self.entries_A:
                    for e in row: args.append(e.get() if e.get() else '0')
                for e in self.entries_b: args.append(e.get() if e.get() else '0')
                
                args.append(self.entry_tol.get())
                args.append(self.entry_max_iter.get())

                res = subprocess.run(args, capture_output=True, text=True)
                
                # Update UI safely from the background
                self.after(0, lambda: self._handle_matrix_results(res))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _handle_matrix_results(self, res):
        # Move the parsing and UI switching here
        self._parse_solver_output(res.stdout)
        self.screen_input.pack_forget()
        self.screen_graph.pack(fill=tk.BOTH, expand=True)
        self.current_step = 0
        self._draw_matrix(self.current_step)

    def _parse_solver_output(self, output):
        self.steps = []
        current_desc, op_text, target_row, target_row_2 = "Initial Configuration", "", -1, -1
        temp_matrix, expected_rows = [], 0
        
        for line in output.splitlines():
            parts = line.split(',')
            if not parts: continue
            
            if parts[0] == 'SWAP':
                r1, r2 = int(parts[1]), int(parts[3])
                current_desc = f"Swapped Row {r1+1} and Row {r2+1}"
                op_text = f"R{r1+1} ↔ R{r2+1}"; target_row = r1; target_row_2 = r2
            elif parts[0] == 'ELIMINATE':
                src, tgt, factor = int(parts[1]), int(parts[2]), float(parts[4])
                current_desc = f"Eliminated Row {tgt+1} using Row {src+1}"
                sign = "+" if factor < 0 else "-"
                op_text = f"R{tgt+1} → R{tgt+1} {sign} {abs(factor):.2f} R{src+1}"
                target_row = tgt; target_row_2 = -1
            elif parts[0] == 'NORMALIZE':
                tgt, diag = int(parts[1]), float(parts[2])
                current_desc = f"Normalized Row {tgt+1}"
                op_text = f"R{tgt+1} → R{tgt+1} / {diag:.2f}"; target_row = tgt; target_row_2 = -1
            elif parts[0] == 'BACKSOLVE':
                tgt = int(parts[1])
                current_desc = f"Back-Substitution: x_{tgt+1} = {float(parts[2]):.4f}"
                op_text = f"x_{tgt+1} Solved"; target_row = tgt; target_row_2 = -1
            elif parts[0] == 'FORWARDSOLVE':
                tgt = int(parts[1])
                current_desc = f"Forward-Substitution: y_{tgt+1} = {float(parts[2]):.4f}"
                op_text = f"y_{tgt+1} Solved"; target_row = tgt; target_row_2 = -1
            elif parts[0] == 'INFO':
                current_desc = parts[1]
                op_text, target_row, target_row_2 = "", -1, -1
                
            elif parts[0] == 'MATRIX':
                temp_matrix = []; expected_rows = int(parts[2])
            elif parts[0] == 'ROW':
                temp_matrix.append([float(x) for x in parts[2:]])
                if len(temp_matrix) == expected_rows:
                    self.steps.append({'type': 'matrix', 'matrix': temp_matrix, 'desc': current_desc,
                                       'op_text': op_text, 'target_row': target_row, 'target_row_2': target_row_2})
                    
            elif parts[0] == 'GS_ITER_START':
                current_desc = f"Gauss-Seidel Iteration {parts[1]}"; temp_matrix = [] 
            elif parts[0] == 'GS_EQ':
                clean_eq = ",".join(parts[1:])
                clean_eq = clean_eq.replace(r'\big[', '[').replace(r'\big]', ']')
                clean_eq = clean_eq.replace(r'\%', '').replace('%', '') 
                clean_eq = clean_eq.replace(r'\\epsilon', r'\epsilon') 
                temp_matrix.append(clean_eq)
                
            elif parts[0] == 'GS_ITER_END':
                self.steps.append({'type': 'equations', 'data': temp_matrix, 'desc': current_desc})

    def _draw_matrix(self, idx):
        self.ax.clear(); self.ax.axis('off')
        if not self.steps: return
        
        step_data = self.steps[idx]
        self.lbl_operation.config(text=f"Step {idx+1}/{len(self.steps)}: {step_data['desc']}")
        
        if step_data.get('type') == 'equations':
            eqs = step_data['data']
            n_eq = len(eqs)
            spacing = min(0.18, 0.8 / n_eq) if n_eq > 0 else 0.15
            
            for i, eq in enumerate(eqs):
                self.ax.text(0.02, 0.9 - i*spacing, eq, color=COLORS.accent_cyan, 
                             fontsize=15, ha='left', va='center')
            self.ax.set_xlim(0, 1); self.ax.set_ylim(0, 1)
            
        else:
            mat = step_data['matrix']
            prev_mat = self.steps[idx-1]['matrix'] if idx > 0 and self.steps[idx-1].get('type') == 'matrix' else None
            
            n = self.n_var.get()
            rows, cols = len(mat), len(mat[0]) if mat else 0
            
            if "Ly = Pb" in step_data['desc'] or "y_" in step_data.get('op_text', ''):
                self.ax.text(-1, 0.5, "L =", color=COLORS.accent_cyan, fontsize=24, fontweight='bold', va='center', ha='right')
            elif "Ux = y" in step_data['desc'] or "x_" in step_data.get('op_text', ''):
                self.ax.text(-1, 0.5, "U =", color=COLORS.accent_cyan, fontsize=24, fontweight='bold', va='center', ha='right')

            for i in range(rows):
                for j in range(cols):
                    val = mat[i][j]
                    color = COLORS.accent_green if j == cols - 1 and cols > n else COLORS.accent_cyan
                    if i == j and j < n: color = COLORS.accent_amber 
                    
                    changed = False
                    if prev_mat and i < len(prev_mat) and j < len(prev_mat[i]):
                        if abs(val - prev_mat[i][j]) > 1e-9: changed = True

                    text_val = "0.00" if abs(val) < 1e-10 else f"{val:.2f}"
                    if changed:
                        self.ax.text(j, -i, text_val, color=COLORS.text_primary, ha='center', va='center', fontfamily='Consolas', fontsize=20, fontweight='heavy', bbox=dict(facecolor=COLORS.accent_red, alpha=0.4, edgecolor='none', boxstyle='round,pad=0.2'))
                    else:
                        self.ax.text(j, -i, text_val, color=color, ha='center', va='center', fontfamily='Consolas', fontsize=18, fontweight='bold')
                    
            if cols > n: self.ax.plot([n - 0.5, n - 0.5], [0.5, -rows + 0.5], color=COLORS.border_mid, lw=2, ls='--')
            
            self.ax.plot([-0.5, -0.5], [0.5, -rows + 0.5], color=COLORS.text_secondary, lw=2)
            self.ax.plot([cols - 0.5, cols - 0.5], [0.5, -rows + 0.5], color=COLORS.text_secondary, lw=2)

            op_text, tr1, tr2 = step_data.get('op_text', ''), step_data.get('target_row', -1), step_data.get('target_row_2', -1)
            if op_text and tr1 != -1:
                self.ax.text(cols + 0.2, -tr1, op_text, color=COLORS.accent_red, fontsize=15, va='center', fontweight='bold')
                if tr2 != -1: self.ax.text(cols + 0.2, -tr2, op_text, color=COLORS.accent_red, fontsize=15, va='center', fontweight='bold')

            self.ax.set_xlim(-2, cols + 2.5); self.ax.set_ylim(-rows, 1)
            
        self.canvas.draw_idle()

    def _go_back(self): self.screen_graph.pack_forget(); self.screen_input.pack(fill=tk.BOTH, expand=True)

    def handle_keypress(self, event):
        if not self.steps: return
        if event.keysym in ('Right', 'space'): self.current_step = min(len(self.steps)-1, self.current_step+1)
        elif event.keysym == 'Left': self.current_step = max(0, self.current_step-1)
        self._draw_matrix(self.current_step)