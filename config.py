import matplotlib as mpl

class Theme:
    def __init__(self):
        self.bg           = '#07090f'
        self.bg_mid       = '#0c1018'
        self.bg_panel     = '#0f1520'
        self.card         = '#111927'
        self.card_hover   = '#182030'
        self.card_active  = '#1c2840'
        self.border       = '#1a2540'
        self.border_mid   = '#243558'
        self.border_glow  = '#2a4a80'
        self.text_primary   = '#dce8f5'
        self.text_secondary = '#6a88b0'
        self.text_muted     = '#2e4060'
        self.accent_cyan    = '#00d4ff'
        self.accent_amber   = '#f0a020'
        self.accent_green   = '#00e5a0'
        self.accent_red     = '#ff4560'
        self.plot_bg        = '#07090f'
        self.plot_axes      = '#0c1018'
        self.plot_grid      = '#1a2540'

    def apply_matplotlib(self):
        mpl.rcParams.update({
            'figure.facecolor': self.plot_bg,
            'axes.facecolor': self.plot_axes,
            'axes.edgecolor': self.border_mid,
            'axes.labelcolor': self.text_secondary,
            'axes.spines.top': False,
            'axes.spines.right': False,
            'xtick.color': self.text_muted,
            'ytick.color': self.text_muted,
            'grid.color': self.plot_grid,
            'grid.linestyle': '--',
            'text.color': self.text_primary,
            'figure.dpi': 110,
            'font.family': 'Trebuchet MS',
        })

COLORS = Theme()
FONTS = {
    'hero': ("Georgia", 32, "bold"),
    'hero_sub': ("Trebuchet MS", 14),
    'title': ("Georgia", 22, "bold"),
    'heading': ("Trebuchet MS", 17, "bold"),
    'subheading': ("Trebuchet MS", 13, "bold"),
    'body_std': ("Trebuchet MS", 11),
    'body_small': ("Trebuchet MS", 10),
    'mono_large': ("Cascadia Code", 16, "bold"),
    'mono_small': ("Cascadia Code", 10),
}

def safe_float(val_str):
    v = str(val_str).upper()
    if "NAN" in v or "IND" in v: return float('nan')
    return float(val_str)

import sys
import os

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)