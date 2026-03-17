import tkinter as tk
from config import COLORS, FONTS
from widgets import GlowButton, draw_rounded_rect, IconButton

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
        for x in range(0, w, 52): self._bg_canvas.create_line(x, 0, x, h, fill=COLORS.border, tags='grid')
        for y in range(0, h, 52): self._bg_canvas.create_line(0, y, w, y, fill=COLORS.border, tags='grid')
        self._bg_canvas.create_oval(-200, -200, 600, 600, fill=COLORS.bg, outline='', tags='grid')
        self._bg_canvas.create_oval(w - 400, h - 400, w + 300, h + 300, fill=COLORS.bg, outline='', tags='grid')

    def _build_ui(self):
        container = tk.Frame(self, bg=COLORS.bg)
        container.pack(expand=True) 

        header = tk.Frame(container, bg=COLORS.bg)
        header.pack(pady=(0, 6))

        chip = tk.Canvas(header, width=220, height=26, bg=COLORS.bg, highlightthickness=0)
        chip.pack()
        draw_rounded_rect(chip, 2, 2, 218, 24, 11, fill=COLORS.card_active, outline=COLORS.border_glow)
        chip.create_text(110, 13, text='✦  C-Powered Computation Engine  ✦', font=FONTS['body_small'], fill=COLORS.accent_cyan)

        tk.Label(header, text='Numerical Analysis Suite', font=FONTS['hero'], bg=COLORS.bg, fg=COLORS.text_primary).pack(pady=(12, 10))

        div = tk.Canvas(container, height=2, bg=COLORS.bg, highlightthickness=0, width=480)
        div.pack(pady=(22, 36))
        div.create_line(0, 1, 200, 1, fill=COLORS.border_mid)
        div.create_line(200, 1, 240, 1, fill=COLORS.accent_cyan, width=2)
        div.create_line(240, 1, 280, 1, fill=COLORS.accent_amber, width=2)
        div.create_line(280, 1, 480, 1, fill=COLORS.border_mid)

        cards_row = tk.Frame(container, bg=COLORS.bg)
        cards_row.pack(fill=tk.BOTH, expand=True)

        # ── NEW INTERESTING CARD CONTENT ──
        self._make_card(cards_row, '📈', 'Root Finding Engine', 
                        ['Hunt down equation roots visually', 
                         'Real-time algorithm convergence', 
                         'Interactive zooming & error tracking'], 
                        'Visual Engine', 1, COLORS.accent_cyan)
        
        tk.Frame(cards_row, width=45, bg=COLORS.bg).pack(side=tk.LEFT)
        
        self._make_card(cards_row, '🧮', 'Linear Systems Engine', 
                        ['Crack multi-variable systems', 
                         'Step-by-step matrix transformations', 
                         'Live mathematical row operations'], 
                        'Matrix Solver', 2, COLORS.accent_amber)

        tk.Label(container, text='Use ← → arrow keys or Space to step through iterations', font=FONTS['body_small'], bg=COLORS.bg, fg=COLORS.text_muted).pack(pady=(35, 0))

        footer = tk.Frame(container, bg=COLORS.bg)
        footer.pack(pady=(45, 0))
        from widgets import IconButton
        IconButton(footer, text='ℹ About Software', command=self._show_about, font=FONTS['body_small'], fg=COLORS.text_muted).pack()

    def _make_card(self, parent, icon, title, lines, badge, target, accent):
        outer = tk.Frame(parent, bg=accent, padx=1, pady=1)
        outer.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        card = tk.Frame(outer, bg=COLORS.card, padx=40, pady=40)
        card.pack(fill=tk.BOTH, expand=True)

        tk.Frame(card, height=4, bg=accent).pack(fill=tk.X, pady=(0, 20))
        top_row = tk.Frame(card, bg=COLORS.card)
        top_row.pack(fill=tk.X)
        tk.Label(top_row, text=icon, font=('Segoe UI Emoji', 30), bg=COLORS.card, fg=accent).pack(side=tk.LEFT, padx=(0, 15))
        tk.Label(top_row, text=title, font=FONTS['heading'], bg=COLORS.card, fg=accent).pack(side=tk.LEFT, anchor='center')

        badge_c = tk.Canvas(card, width=100, height=26, bg=COLORS.card, highlightthickness=0)
        badge_c.pack(anchor='w', pady=(15, 20))
        # FIXED: Pulled badge boundaries inward (2, 2, 98, 24)
        draw_rounded_rect(badge_c, 2, 2, 98, 24, 11, fill=COLORS.bg_panel, outline=accent)
        badge_c.create_text(50, 13, text=badge, font=FONTS['body_small'], fill=accent)

        for ln in lines:
            row = tk.Frame(card, bg=COLORS.card)
            row.pack(fill=tk.X, pady=4)
            tk.Label(row, text='▸', font=FONTS['body_small'], bg=COLORS.card, fg=accent).pack(side=tk.LEFT, padx=(0, 10))
            tk.Label(row, text=ln, font=FONTS['body_std'], bg=COLORS.card, fg=COLORS.text_secondary, anchor='w').pack(side=tk.LEFT)

        btn = GlowButton(card, text='Launch Module  →', command=lambda t=target: self.notebook.select(t), 
                         accent='cyan' if accent == COLORS.accent_cyan else 'amber', width=220, height=45, bg=COLORS.card)
        btn.pack(pady=(35, 0))
        
    # ── UPDATED: ABOUT WINDOW WITH PERSONAL INFO ──
    def _show_about(self):
        about = tk.Toplevel(self)
        about.title("About Software")
        about.geometry("500x300")
        about.configure(bg=COLORS.bg)
        about.resizable(False, False)
        
        about.transient(self.winfo_toplevel())
        about.grab_set()

        tk.Label(about, text="Numerical Analysis Suite", font=FONTS['title'], bg=COLORS.bg, fg=COLORS.accent_cyan).pack(pady=(30, 5))
        tk.Label(about, text="Version 1.0.0 (Pro Edition)", font=FONTS['body_std'], bg=COLORS.bg, fg=COLORS.text_secondary).pack(pady=(0, 25))
        
        tk.Label(about, text="Lead Developer: Somajit Deb", font=FONTS['heading'], bg=COLORS.bg, fg=COLORS.accent_amber).pack(pady=(0, 5))
        tk.Label(about, text="Computer Science & Engineering", font=FONTS['body_std'], bg=COLORS.bg, fg=COLORS.text_primary).pack(pady=(0, 2))
        tk.Label(about, text="Khulna University", font=FONTS['subheading'], bg=COLORS.bg, fg=COLORS.text_secondary).pack(pady=(0, 25))

        IconButton(about, text="Close Window", command=about.destroy).pack()