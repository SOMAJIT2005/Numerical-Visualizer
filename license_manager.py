# Licensing and trial restrictions have been removed for open educational access.

def get_status():
    """Always unlocked with no trial expiration."""
    return True, 0


def unlock_app(provided_key=""):
    """No-op unlock stub for backward compatibility."""
    return True
