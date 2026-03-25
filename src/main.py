import sys
import os

# Fix Qt monitor interface error on some Windows systems
# Must be set BEFORE importing PySide6
os.environ["QT_QPA_PLATFORM"] = "windows"
os.environ["QT_LOGGING_RULES"] = "qt.qpa.screen=false"

# Ensure the 'src' directory and project root are in path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.dirname(current_dir))

from PySide6.QtWidgets import QApplication
from ui.main_window import MultiPackagerApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MultiPackagerApp()
    window.show()
    sys.exit(app.exec())
