import sys
import os

def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Dev mode: Resources are in src/resources relative to this utils.py
        # src/core/utils.py -> src/core -> src -> src/resources
        base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources")

    return os.path.join(base_path, relative_path)
