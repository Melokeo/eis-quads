import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from window import SlideWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        
    window = SlideWindow()
    window.show()
    sys.exit(app.exec())