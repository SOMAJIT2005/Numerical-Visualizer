import tkinter as tk
from config import COLORS, FONTS


def draw_rounded_rect(canvas, x1, y1, x2, y2, r, **kw):
    pts = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1, x1 + r, y1
    ]
    return canvas.create_polygon(pts, smooth=True, **kw)


class GlowButton(tk.Canvas):
    def __init__(self, parent, text, command=None, accent='cyan', width=190, height=42, bg=None, **kwargs):
        if bg is None:
            bg = COLORS.bg
        super().__init__(parent, width=width, height=height, bg=bg, highlightthickness=0, cursor='hand2', **kwargs)
        self._cmd, self._text = command, text
        self._width, self._height = width, height
        self._accent_type = accent
        self._parent_bg = bg

        self._draw(False)
        self.bind('<Enter>', lambda e: self._draw(True))
        self.bind('<Leave>', lambda e: self._draw(False))
        self.bind('<Button-1>', lambda e: self._cmd() if self._cmd else None)

    def _get_accent(self):
        if self._accent_type == 'amber':
            return COLORS.accent_amber
        if self._accent_type == 'green':
            return COLORS.accent_green
        return COLORS.accent_cyan

    def _draw(self, hover):
        self.delete('all')
        accent_color = self._get_accent()
        r = max(8, (self._height - 4) // 2)
        if hover:
            draw_rounded_rect(self, 2, 2, self._width - 3, self._height - 3, r, fill=accent_color, outline=accent_color)
            self.create_text(self._width // 2, self._height // 2, text=self._text, fill=COLORS.bg, font=FONTS['heading'])
        else:
            draw_rounded_rect(self, 2, 2, self._width - 3, self._height - 3, r, fill=self._parent_bg, outline=accent_color, width=2)
            self.create_text(self._width // 2, self._height // 2, text=self._text, fill=accent_color, font=FONTS['heading'])


class StatCard(tk.Frame):
    def __init__(self, parent, title, color, subtitle="", **kwargs):
        super().__init__(parent, bg=COLORS.card, highlightthickness=1, highlightbackground=COLORS.border, padx=14, pady=8, **kwargs)
        top = tk.Frame(self, bg=COLORS.card)
        top.pack(fill=tk.X)
        tk.Frame(top, width=6, height=6, bg=color).pack(side=tk.LEFT, padx=(0, 6), pady=2)
        tk.Label(top, text=title.upper(), font=FONTS['body_small'], bg=COLORS.card, fg=COLORS.text_secondary).pack(side=tk.LEFT, anchor='w')
        self.val_lbl = tk.Label(self, text="---", font=FONTS['mono_large'], bg=COLORS.card, fg=color)
        self.val_lbl.pack(anchor='w', pady=(2, 0))
        self.sub_lbl = None
        if subtitle:
            self.sub_lbl = tk.Label(self, text=subtitle, font=FONTS['body_small'], bg=COLORS.card, fg=COLORS.text_muted)
            self.sub_lbl.pack(anchor='w')

    def set(self, val, subtitle=None):
        if isinstance(val, float):
            self.val_lbl.config(text=f"{val:.5e}")
        else:
            self.val_lbl.config(text=str(val))
        if subtitle is not None and self.sub_lbl is not None:
            self.sub_lbl.config(text=subtitle)


class PremiumEntry(tk.Frame):
    def __init__(self, parent, width=20, default='', justify='center', **kwargs):
        super().__init__(parent, bg=COLORS.card)
        self._entry = tk.Entry(
            self,
            width=width,
            bg=COLORS.bg_mid,
            fg=COLORS.text_primary,
            font=FONTS['mono_small'],
            relief='flat',
            insertbackground=COLORS.accent_cyan,
            justify=justify,
            bd=0,
        )
        self._entry.insert(0, str(default))
        self._entry.pack(ipady=6, padx=4, fill=tk.X)
        self._line = tk.Frame(self, height=2, bg=COLORS.border)
        self._line.pack(fill=tk.X)
        self._entry.bind('<FocusIn>', lambda e: self._line.config(bg=COLORS.accent_cyan))
        self._entry.bind('<FocusOut>', lambda e: self._line.config(bg=COLORS.border))

    def get(self):
        return self._entry.get()

    def set(self, val):
        self._entry.delete(0, tk.END)
        self._entry.insert(0, str(val))


class SectionLabel(tk.Frame):
    def __init__(self, parent, text, accent='cyan', bg=None, **kwargs):
        use_bg = bg if bg else COLORS.bg
        super().__init__(parent, bg=use_bg, **kwargs)
        bar_color = COLORS.accent_cyan if accent == 'cyan' else (COLORS.accent_amber if accent == 'amber' else COLORS.accent_green)
        tk.Frame(self, width=3, bg=bar_color).pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        tk.Label(self, text=text, font=FONTS['subheading'], bg=use_bg, fg=COLORS.text_secondary).pack(side=tk.LEFT)


class IconButton(tk.Button):
    def __init__(self, parent, text, command=None, font=None, **kwargs):
        use_font = font if font else FONTS['subheading']
        use_fg = kwargs.pop('fg', COLORS.text_secondary)
        use_bg = kwargs.pop('bg', COLORS.bg)
        super().__init__(
            parent,
            text=text,
            command=command,
            bg=use_bg,
            fg=use_fg,
            font=use_font,
            relief='flat',
            activebackground=COLORS.card_hover,
            activeforeground=COLORS.accent_cyan,
            bd=0,
            cursor='hand2',
            **kwargs
        )
        self._default_bg = use_bg
        self._default_fg = use_fg
        self.bind('<Enter>', lambda e: self.config(fg=COLORS.accent_cyan))
        self.bind('<Leave>', lambda e: self.config(fg=self._default_fg))


class ChipButton(tk.Button):
    """Compact preset/action button with subtle border and hover state."""
    def __init__(self, parent, text, command=None, accent=None, bg=None, **kwargs):
        use_bg = bg if bg else COLORS.bg_mid
        fg_col = accent if accent else COLORS.text_secondary
        super().__init__(
            parent,
            text=text,
            command=command,
            bg=use_bg,
            fg=fg_col,
            font=FONTS['body_small'],
            relief='flat',
            bd=0,
            padx=8,
            pady=3,
            cursor='hand2',
            activebackground=COLORS.card_active,
            activeforeground=COLORS.accent_cyan,
            highlightthickness=1,
            highlightbackground=COLORS.border,
            **kwargs
        )
        self._base_bg = use_bg
        self._base_fg = fg_col
        self.bind('<Enter>', lambda e: self.config(bg=COLORS.card_hover, fg=COLORS.accent_cyan, highlightbackground=COLORS.accent_cyan))
        self.bind('<Leave>', lambda e: self.config(bg=self._base_bg, fg=self._base_fg, highlightbackground=COLORS.border))


class StepControlBar(tk.Frame):
    """Universal step playback controller: First, Prev, Play/Pause, Next, Last, and Step Counter."""
    def __init__(self, parent, on_step_change, get_total_steps, get_current_step, bg=None):
        use_bg = bg if bg else COLORS.card
        super().__init__(parent, bg=use_bg, padx=10, pady=6, highlightthickness=1, highlightbackground=COLORS.border)
        self.on_step_change = on_step_change
        self.get_total_steps = get_total_steps
        self.get_current_step = get_current_step
        self._playing = False
        self._timer_id = None
        self._delay_ms = 650

        btn_cfg = dict(bg=COLORS.bg_mid)
        self.btn_first = ChipButton(self, "⏮ First", command=self.step_first, **btn_cfg)
        self.btn_first.pack(side=tk.LEFT, padx=2)

        self.btn_prev = ChipButton(self, "◀ Prev", command=self.step_prev, **btn_cfg)
        self.btn_prev.pack(side=tk.LEFT, padx=2)

        self.btn_play = ChipButton(self, "▶ Play", command=self.toggle_play, accent=COLORS.accent_cyan, **btn_cfg)
        self.btn_play.pack(side=tk.LEFT, padx=4)

        self.btn_next = ChipButton(self, "Next ▶", command=self.step_next, **btn_cfg)
        self.btn_next.pack(side=tk.LEFT, padx=2)

        self.btn_last = ChipButton(self, "Last ⏭", command=self.step_last, **btn_cfg)
        self.btn_last.pack(side=tk.LEFT, padx=2)

        self.lbl_counter = tk.Label(self, text="Step 0 / 0", font=FONTS['mono_small'], bg=use_bg, fg=COLORS.accent_amber, padx=10)
        self.lbl_counter.pack(side=tk.LEFT)

    def update_counter(self):
        total = self.get_total_steps()
        curr = self.get_current_step()
        if total <= 0:
            self.lbl_counter.config(text="Step 0 / 0")
        else:
            self.lbl_counter.config(text=f"Step {curr + 1} / {total}")

    def step_first(self):
        self.stop_play()
        if self.get_total_steps() > 0:
            self.on_step_change(0)
            self.update_counter()

    def step_prev(self):
        self.stop_play()
        total = self.get_total_steps()
        if total > 0:
            self.on_step_change(max(0, self.get_current_step() - 1))
            self.update_counter()

    def step_next(self):
        self.stop_play()
        total = self.get_total_steps()
        if total > 0:
            self.on_step_change(min(total - 1, self.get_current_step() + 1))
            self.update_counter()

    def step_last(self):
        self.stop_play()
        total = self.get_total_steps()
        if total > 0:
            self.on_step_change(total - 1)
            self.update_counter()

    def toggle_play(self):
        if self._playing:
            self.stop_play()
        else:
            total = self.get_total_steps()
            if total <= 0:
                return
            if self.get_current_step() >= total - 1:
                self.on_step_change(0)
                self.update_counter()
            self._playing = True
            self.btn_play.config(text="⏸ Pause")
            self._schedule_tick()

    def stop_play(self):
        self._playing = False
        if self._timer_id is not None:
            try:
                self.after_cancel(self._timer_id)
            except Exception:
                pass
            self._timer_id = None
        if self.btn_play.winfo_exists():
            self.btn_play.config(text="▶ Play")

    def _schedule_tick(self):
        if not self._playing:
            return
        total = self.get_total_steps()
        curr = self.get_current_step()
        if curr < total - 1:
            self.on_step_change(curr + 1)
            self.update_counter()
            self._timer_id = self.after(self._delay_ms, self._schedule_tick)
        else:
            self.stop_play()


class MethodBanner(tk.Frame):
    """Displays the active method's governing equation, description, and a button to view full working steps."""
    def __init__(self, parent, on_show_steps=None, bg=None):
        use_bg = bg if bg else COLORS.card
        super().__init__(parent, bg=use_bg, padx=12, pady=8, highlightthickness=1, highlightbackground=COLORS.border)
        top = tk.Frame(self, bg=use_bg)
        top.pack(fill=tk.X)
        self.lbl_title = tk.Label(top, text="", font=FONTS['subheading'], bg=use_bg, fg=COLORS.accent_cyan, anchor='w')
        self.lbl_title.pack(side=tk.LEFT)
        if on_show_steps:
            ChipButton(
                top,
                text="📖 Full Working Steps & Equation",
                command=on_show_steps,
                accent=COLORS.accent_amber,
                bg=COLORS.bg_mid
            ).pack(side=tk.RIGHT)
        self.lbl_eq = tk.Label(self, text="", font=FONTS['mono_small'], bg=use_bg, fg=COLORS.accent_green, anchor='w', justify='left')
        self.lbl_eq.pack(fill=tk.X, pady=(3, 1))
        self.lbl_desc = tk.Label(self, text="", font=FONTS['body_small'], bg=use_bg, fg=COLORS.text_secondary, anchor='w', justify='left', wraplength=680)
        self.lbl_desc.pack(fill=tk.X)

    def set_method(self, title, equation, description):
        self.lbl_title.config(text=title)
        self.lbl_eq.config(text=f"Equation:  {equation}")
        self.lbl_desc.config(text=description)


def show_working_steps_modal(parent, title, equation, description, steps_lines):
    """Opens a modal window displaying the method's governing equation, description, and every step's arithmetic substitution."""
    win = tk.Toplevel(parent)
    win.title(f"Working Steps & Mathematical Derivation — {title}")
    win.geometry("820x600")
    win.configure(bg=COLORS.bg)
    win.transient(parent.winfo_toplevel())

    hdr = tk.Frame(win, bg=COLORS.card, padx=22, pady=14, highlightthickness=1, highlightbackground=COLORS.border)
    hdr.pack(fill=tk.X)
    tk.Label(hdr, text=f"📖 {title}", font=FONTS['heading'], bg=COLORS.card, fg=COLORS.accent_cyan).pack(anchor='w')
    tk.Label(hdr, text=f"Governing Equation:  {equation}", font=FONTS['mono_small'], bg=COLORS.card, fg=COLORS.accent_green).pack(anchor='w', pady=(4, 2))
    tk.Label(hdr, text=description, font=FONTS['body_std'], bg=COLORS.card, fg=COLORS.text_secondary, wraplength=760, justify='left').pack(anchor='w')

    body = tk.Frame(win, bg=COLORS.bg, padx=20, pady=12)
    body.pack(fill=tk.BOTH, expand=True)

    txt = tk.Text(
        body,
        bg=COLORS.card,
        fg=COLORS.text_primary,
        font=FONTS['mono_small'],
        padx=18,
        pady=14,
        relief='flat',
        wrap=tk.WORD,
        highlightthickness=1,
        highlightbackground=COLORS.border
    )
    scroll = tk.Scrollbar(body, orient='vertical', command=txt.yview)
    txt.configure(yscrollcommand=scroll.set)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    txt.tag_configure('hdr', font=FONTS['subheading'], foreground=COLORS.accent_amber, spacing1=6, spacing3=4)
    txt.tag_configure('eq', font=FONTS['mono_small'], foreground=COLORS.accent_cyan)
    txt.tag_configure('step', font=FONTS['mono_small'], foreground=COLORS.text_primary, spacing1=2, spacing3=2)

    txt.insert(tk.END, "1. GOVERNING EQUATION & METHOD OVERVIEW\n", 'hdr')
    txt.insert(tk.END, f"   Formula:      {equation}\n", 'eq')
    txt.insert(tk.END, f"   Description:  {description}\n\n", 'step')
    txt.insert(tk.END, "2. STEP-BY-STEP WORKING SUBSTITUTION (COMPUTED IN C ENGINE)\n", 'hdr')

    if not steps_lines:
        txt.insert(tk.END, "   Run the solver first to generate step-by-step numerical substitutions.\n", 'step')
    else:
        for line in steps_lines:
            txt.insert(tk.END, f"   {line}\n", 'step')

    txt.configure(state='disabled')

    ftr = tk.Frame(win, bg=COLORS.bg, pady=8)
    ftr.pack(fill=tk.X)

    def copy_all():
        win.clipboard_clear()
        win.clipboard_append(txt.get('1.0', tk.END))

    ChipButton(ftr, text="📋 Copy Full Working Solution", command=copy_all, accent=COLORS.accent_green, bg=COLORS.card).pack(side=tk.LEFT, padx=(20, 8))
    ChipButton(ftr, text="Close Window", command=win.destroy, accent=COLORS.accent_cyan, bg=COLORS.card).pack(side=tk.RIGHT, padx=20)

