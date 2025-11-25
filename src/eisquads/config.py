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

class DockSide(Enum):
    LEFT = 1
    RIGHT = 2
    TOP = 3
    BOTTOM = 4
