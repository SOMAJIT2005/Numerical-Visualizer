import tkinter as tk


class LicenseGate(tk.Toplevel):
    """Deprecated: Trial and activation gate removed. Immediately invokes on_success if called."""
    def __init__(self, parent, on_success=None):
        super().__init__(parent)
        self.withdraw()
        if on_success:
            on_success()
        self.destroy()
