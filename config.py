"""
config.py — Design System, Palettes, Typography & Resource Helpers
for Numerical Methods Interactive Learning Lab (MIT Edition).
All mathematical evaluations and numerical algorithms are executed in compiled C engines.
"""
import os
import sys


class ThemePalette:
    def __init__(self, mode='dark'):
        self.set_mode(mode)

    def toggle(self):
        self.set_mode('light' if self.mode == 'dark' else 'dark')

    def set_mode(self, mode='dark'):
        self.mode = mode
        if mode == 'light':
            self.bg_root        = '#F1F5F9'
            self.bg_panel       = '#FFFFFF'
            self.bg_card        = '#F8FAFC'
            self.bg_card_hover  = '#E2E8F0'
            self.bg_input       = '#FFFFFF'
            self.bg_canvas      = '#FFFFFF'

            self.accent_cyan    = '#0284C7'
            self.accent_cyan_h  = '#0369A1'
            self.accent_amber   = '#D97706'
            self.accent_amber_h = '#B45309'
            self.accent_green   = '#059669'
            self.accent_red     = '#DC2626'
            self.accent_purple  = '#7C3AED'
            self.accent_pink    = '#DB2777'
            self.accent_blue    = '#2563EB'

            self.text_primary   = '#0F172A'
            self.text_secondary = '#334155'
            self.text_muted     = '#64748B'

            self.border         = '#CBD5E1'
            self.border_focus   = '#0284C7'
            self.border_subtle  = '#E2E8F0'

            self.plot_face      = '#FFFFFF'
            self.plot_axes      = '#F8FAFC'
            self.plot_grid      = '#CBD5E1'
            self.plot_zero      = '#64748B'
        else:
            self.bg_root        = '#0B0F19'
            self.bg_panel       = '#111827'
            self.bg_card        = '#1A2234'
            self.bg_card_hover  = '#232E45'
            self.bg_input       = '#0F1624'
            self.bg_canvas      = '#0D1321'

            self.accent_cyan    = '#06B6D4'
            self.accent_cyan_h  = '#22D3EE'
            self.accent_amber   = '#F59E0B'
            self.accent_amber_h = '#FBBF24'
            self.accent_green   = '#10B981'
            self.accent_red     = '#EF4444'
            self.accent_purple  = '#8B5CF6'
            self.accent_pink    = '#EC4899'
            self.accent_blue    = '#3B82F6'

            self.text_primary   = '#F1F5F9'
            self.text_secondary = '#94A3B8'
            self.text_muted     = '#64748B'

            self.border         = '#1E293B'
            self.border_focus   = '#06B6D4'
            self.border_subtle  = '#162032'

            self.plot_face      = '#0D1321'
            self.plot_axes      = '#111827'
            self.plot_grid      = '#1E293B'
            self.plot_zero      = '#334155'

        # Legacy aliases used across widgets and tabs
        self.bg          = self.bg_root
        self.card        = self.bg_card
        self.bg_mid      = self.bg_panel
        self.card_hover  = self.bg_card_hover
        self.card_active = self.bg_card_hover
        self.border_mid  = self.border
        self.border_glow = self.border_focus
        self.plot_bg     = self.plot_face


COLORS = ThemePalette('dark')


class FontRegistry(dict):
    FAMILY_SANS = 'Segoe UI'
    FAMILY_MONO = 'Consolas'

    HERO        = (FAMILY_SANS, 24, 'bold')
    TITLE       = (FAMILY_SANS, 20, 'bold')
    SUBTITLE    = (FAMILY_SANS, 11)
    HEADING     = (FAMILY_SANS, 13, 'bold')
    SUBHEADING  = (FAMILY_SANS, 10, 'bold')
    BODY        = (FAMILY_SANS, 10)
    BODY_BOLD   = (FAMILY_SANS, 10, 'bold')
    SMALL       = (FAMILY_SANS, 9)
    TINY        = (FAMILY_SANS, 8)
    TINY_BOLD   = (FAMILY_SANS, 8, 'bold')

    MONO        = (FAMILY_MONO, 10)
    MONO_BOLD   = (FAMILY_MONO, 10, 'bold')
    MONO_SMALL  = (FAMILY_MONO, 9)
    MONO_LARGE  = (FAMILY_MONO, 13, 'bold')

    STAT_VALUE  = (FAMILY_MONO, 15, 'bold')
    STAT_LABEL  = (FAMILY_SANS, 8, 'bold')
    BUTTON      = (FAMILY_SANS, 10, 'bold')
    CHIP        = (FAMILY_SANS, 8, 'bold')

    def __init__(self):
        super().__init__({
            'hero': self.HERO,
            'title': self.TITLE,
            'subtitle': self.SUBTITLE,
            'heading': self.HEADING,
            'subheading': self.SUBHEADING,
            'body_std': self.BODY,
            'body': self.BODY,
            'body_bold': self.BODY_BOLD,
            'body_small': self.SMALL,
            'small': self.SMALL,
            'tiny': self.TINY,
            'mono': self.MONO,
            'mono_bold': self.MONO_BOLD,
            'mono_small': self.MONO_SMALL,
            'mono_large': self.MONO_LARGE,
            'stat_value': self.STAT_VALUE,
            'stat_label': self.STAT_LABEL,
            'button': self.BUTTON,
            'chip': self.CHIP,
        })


FONTS = FontRegistry()


def safe_float(val_str):
    """Safely convert a string from C engine output to float, handling NaN/Inf."""
    s = str(val_str).strip()
    if any(k in s.upper() for k in ('NAN', 'IND', 'INF')):
        return float('nan')
    try:
        return float(s)
    except ValueError:
        return float('nan')


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)
