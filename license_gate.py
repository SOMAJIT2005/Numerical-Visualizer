import tkinter as tk
from tkinter import messagebox
from config import COLORS, FONTS
import license_manager

class LicenseGate(tk.Toplevel):
    def __init__(self, parent, on_success):
        super().__init__(parent)
        self.parent = parent
        self.on_success = on_success
        self.title("Premium Activation Required")
        self.geometry("500x350")
        self.configure(bg=COLORS.bg)
        self.resizable(False, False)
        
        # Make this window "modal" (user can't click main window)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # UI Elements
        tk.Label(self, text="⚠", font=("Segoe UI Emoji", 40), bg=COLORS.bg, fg=COLORS.accent_red).pack(pady=(30, 10))
        tk.Label(self, text="Trial Period Expired", font=FONTS['title'], bg=COLORS.bg, fg=COLORS.text_primary).pack()
        tk.Label(self, text="Access to the C-Powered Engine requires a valid key.", 
                 font=FONTS['body_std'], bg=COLORS.bg, fg=COLORS.text_secondary).pack(pady=10)

        self.entry = tk.Entry(self, width=30, font=FONTS['mono_large'], bg=COLORS.bg_mid, 
                              fg=COLORS.accent_cyan, insertbackground=COLORS.accent_cyan, 
                              relief='flat', justify='center')
        self.entry.pack(pady=20, ipady=8)
        
        btn = tk.Button(self, text="ACTIVATE PERMANENT ACCESS", font=FONTS['heading'], 
                        bg=COLORS.accent_cyan, fg=COLORS.bg, relief='flat', 
                        command=self.validate, cursor='hand2')
        btn.pack(pady=10, ipadx=20, ipady=5)

    def validate(self):
        if license_manager.unlock_app(self.entry.get()):
            messagebox.showinfo("Success", "Activation Successful! Welcome to Premium.")
            self.on_success()
            self.destroy()
        else:
            messagebox.showerror("Error", "Invalid Activation Key.")

    def on_close(self):
        self.parent.destroy()