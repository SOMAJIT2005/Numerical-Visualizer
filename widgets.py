import tkinter as tk
from config import COLORS, FONTS

def draw_rounded_rect(canvas, x1, y1, x2, y2, r, **kw):
    pts = [x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r, x2, y2, x2-r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1, x1+r, y1]
    return canvas.create_polygon(pts, smooth=True, **kw)

# Replace ONLY the GlowButton class in your widgets.py
class GlowButton(tk.Canvas):
    def __init__(self, parent, text, command=None, accent='cyan', width=190, height=42, bg=COLORS.bg, **kwargs):
        super().__init__(parent, width=width, height=height, bg=bg, highlightthickness=0, cursor='hand2', **kwargs)
        self._cmd, self._text = command, text
        self._width, self._height = width, height
        self._accent_type = accent
        self._parent_bg = bg  # FIXED: Restored the parent background variable
        
        self._draw(False)
        self.bind('<Enter>', lambda e: self._draw(True))
        self.bind('<Leave>', lambda e: self._draw(False))
        self.bind('<Button-1>', lambda e: self._cmd() if self._cmd else None)

    def _draw(self, hover):
        self.delete('all')
        
        accent_color = COLORS.accent_cyan if self._accent_type == 'cyan' else COLORS.accent_amber
        
        if hover:
            draw_rounded_rect(self, 2, 2, self._width-3, self._height-3, (self._height-4)//2, fill=accent_color)
            self.create_text(self._width//2, self._height//2, text=self._text, fill=COLORS.bg, font=FONTS['heading'])
        else:
            draw_rounded_rect(self, 2, 2, self._width-3, self._height-3, (self._height-4)//2, fill=self._parent_bg, outline=accent_color)
            self.create_text(self._width//2, self._height//2, text=self._text, fill=accent_color, font=FONTS['heading'])
            
class StatCard(tk.Frame):
    def __init__(self, parent, title, color, **kwargs):
        super().__init__(parent, bg=COLORS.bg_panel, highlightthickness=1, highlightbackground=COLORS.border, padx=15, pady=8)
        tk.Label(self, text=title.upper(), font=FONTS['body_small'], bg=COLORS.bg_panel, fg=COLORS.text_secondary).pack(anchor='w')
        self.val_lbl = tk.Label(self, text="0.000", font=FONTS['mono_large'], bg=COLORS.bg_panel, fg=color)
        self.val_lbl.pack(anchor='w')

    def set(self, val):
        if isinstance(val, float): self.val_lbl.config(text=f"{val:.4e}")
        else: self.val_lbl.config(text=str(val))

class PremiumEntry(tk.Frame):
    def __init__(self, parent, width=20, default='', **kwargs):
        super().__init__(parent, bg=COLORS.card)
        self._entry = tk.Entry(self, width=width, bg=COLORS.bg_mid, fg=COLORS.text_primary, font=FONTS['mono_small'], relief='flat', insertbackground=COLORS.accent_cyan, justify='center', bd=0)
        self._entry.insert(0, default)
        # REDUCED ipady to save vertical space
        self._entry.pack(ipady=6, padx=4, fill=tk.X)
        self._line = tk.Frame(self, height=2, bg=COLORS.border)
        self._line.pack(fill=tk.X)
    def get(self): return self._entry.get()

class SectionLabel(tk.Frame):
    def __init__(self, parent, text, accent='cyan', **kwargs):
        super().__init__(parent, bg=COLORS.bg, **kwargs)
        tk.Frame(self, width=3, bg=COLORS.accent_cyan if accent=='cyan' else COLORS.accent_amber).pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        tk.Label(self, text=text, font=FONTS['subheading'], bg=COLORS.bg, fg=COLORS.text_secondary).pack(side=tk.LEFT)

class IconButton(tk.Button):
    def __init__(self, parent, text, command=None, font=None, **kwargs):
        use_font = font if font else FONTS['heading']
        # Extract custom 'fg' if it exists, otherwise use the default secondary text
        use_fg = kwargs.pop('fg', COLORS.text_secondary) 
        
        super().__init__(parent, text=text, command=command, bg=COLORS.bg, 
                         fg=use_fg, font=use_font, 
                         relief='flat', activebackground=COLORS.card_hover, 
                         activeforeground=COLORS.accent_cyan, bd=0, cursor='hand2', **kwargs)