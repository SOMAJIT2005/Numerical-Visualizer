import winreg
import time
import hashlib
from secret_key import VALID_KEY_HASH

# Registry settings
REG_PATH = r"Software\ArkoNumericalSuite"
TRIAL_DURATION = 86400  # 24 hours

def get_status():
    """Returns (is_unlocked, remaining_seconds)"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ)
        status, _ = winreg.QueryValueEx(key, "Status")
        install_date, _ = winreg.QueryValueEx(key, "InstallDate")
        winreg.CloseKey(key)

        if status == "unlocked":
            return True, 0
        
        elapsed = time.time() - float(install_date)
        remaining = max(0, TRIAL_DURATION - elapsed)
        return False, remaining

    except FileNotFoundError:
        # First launch: Initialize Registry
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH)
        winreg.SetValueEx(key, "InstallDate", 0, winreg.REG_SZ, str(time.time()))
        winreg.SetValueEx(key, "Status", 0, winreg.REG_SZ, "trial")
        winreg.CloseKey(key)
        return False, TRIAL_DURATION

def unlock_app(provided_key):
    key_hash = hashlib.sha256(provided_key.strip().encode()).hexdigest()
    if key_hash == VALID_KEY_HASH:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "Status", 0, winreg.REG_SZ, "unlocked")
        winreg.CloseKey(key)
        return True
    return False