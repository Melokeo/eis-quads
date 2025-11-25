from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtWidgets import QFrame, QMenu, QApplication
from PyQt6.QtGui import QAction
from config import TAB_SIZE, ACCENT_COLOR, BG_COLOR, TEXT_COLOR

class DraggableTab(QFrame):
    # Change signals to carry raw global position
    drag_started = pyqtSignal(QPoint) 
    drag_moved = pyqtSignal(QPoint)
    drag_ended = pyqtSignal()
    clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setFixedSize(TAB_SIZE, 60)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {ACCENT_COLOR};
                border-radius: 0px;
            }}
            QFrame:hover {{
                background-color: #b4befe;
            }}
        """)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.dragging = False
        self.drag_start_pos = QPoint()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_start_pos = event.globalPosition().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            # Emit raw global pos
            self.drag_started.emit(self.drag_start_pos)
        elif event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def mouseMoveEvent(self, event):
        if self.dragging:
            # Emit raw global pos
            self.drag_moved.emit(event.globalPosition().toPoint())

    def mouseReleaseEvent(self, event):
        if self.dragging:
            self.dragging = False
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            if (event.globalPosition().toPoint() - self.drag_start_pos).manhattanLength() < 5:
                self.clicked.emit()
            else:
                self.drag_ended.emit()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        # Apply the app's style to the menu
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {BG_COLOR}; 
                color: {TEXT_COLOR}; 
                border: 1px solid {ACCENT_COLOR};
            }}
            QMenu::item {{
                padding: 5px 20px;
            }}
            QMenu::item:selected {{
                background-color: {ACCENT_COLOR};
                color: {BG_COLOR};
            }}
        """)
        
        close_action = QAction("Quit", self)
        close_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(close_action)
        
        menu.exec(event.globalPos())
