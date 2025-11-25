from enum import Enum

# --- Configuration & Styling ---
APP_WIDTH = 350
APP_HEIGHT = 350
TAB_SIZE = 24  # Width or Height depending on orientation
BG_COLOR = "#1e1e2e"
QUAD_LINES_COLOR = "#313244"
TEXT_COLOR = "#cdd6f4"
ACCENT_COLOR = "#89b4fa"
DOT_COLOR = "#f38ba8"
DOT_SIZE = 14

STYLESHEET = f"""
    QWidget {{
        font-family: 'Segoe UI', sans-serif;
        color: "#cdd6f4";
    }}
    QLineEdit, QTextEdit {{
        background-color: #313244;
        border: 1px solid #45475a;
        border-radius: 4px;
        padding: 5px;
        color: white;
    }}
    QPushButton {{
        background-color: "#89b4fa";
        color: #1e1e2e;
        border: none;
        border-radius: 4px;
        padding: 5px;
        font-weight: bold;
    }}
    QPushButton:hover {{
        background-color: #b4befe;
    }}
    QPushButton#deleteBtn {{
        background-color: #f38ba8;
        color: #1e1e2e;
    }}
    QPushButton#addBtn {{
        border-radius: 15px;
        font-size: 16px;
        padding: 0;
    }}
"""

class DockSide(Enum):
    LEFT = 1
    RIGHT = 2
    TOP = 3
    BOTTOM = 4
