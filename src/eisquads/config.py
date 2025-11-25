from enum import Enum
from dataclasses import dataclass

# --- configuration & styling ---
@dataclass
class UiConfig:
    APP_WIDTH = 360
    APP_HEIGHT = 250
    TAB_SIZE = 24  # width or height depending on orientation
    BG_COLOR = "#1e1e2e"
    QUAD_LINES_COLOR = "#5C5E7E"
    TEXT_COLOR = "#cdd6f4"
    ACCENT_COLOR = "#89b4fa"
    DOT_COLOR = "#f38ba8"
    DOT_SIZE = 14
    DOT_FONT = "Segoe UI"
    DOT_FONT_SIZE = 8

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

INPUT_STYLESHEET = f"""
background-color: {UiConfig.BG_COLOR}; 
color: {UiConfig.TEXT_COLOR};
border: 2px solid {UiConfig.ACCENT_COLOR}; 
border-radius: 8px;
padding: 5px;
font-size: 14px;
"""

DETAIL_POPUP_STYLESHEET = f"background-color: {UiConfig.BG_COLOR}; border: 1px solid {UiConfig.ACCENT_COLOR}; border-radius: 8px;"

DRAG_TAB_STYLESHEET = f"""
QFrame {{
    background-color: {UiConfig.ACCENT_COLOR};
    border-radius: 0px;
}}
QFrame:hover {{
    background-color: #b4befe;
}}
"""

CONTEXT_MENU_STYLESHEET = f"""
QMenu {{
    background-color: {UiConfig.BG_COLOR}; 
    color: {UiConfig.TEXT_COLOR}; 
    border: 1px solid {UiConfig.ACCENT_COLOR};
    border-radius: 10px;
}}
QMenu::item {{
    padding: 5px 20px;
    border-radius: 5px;
    margin: 2px 5px;
}}
QMenu::item:selected {{
    background-color: {UiConfig.ACCENT_COLOR};
    color: {UiConfig.BG_COLOR};
}}
"""

class DockSide(Enum):
    LEFT = 1
    RIGHT = 2
    TOP = 3
    BOTTOM = 4
