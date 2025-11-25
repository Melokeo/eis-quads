from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtWidgets import QFrame, QMenu, QApplication
from PyQt6.QtGui import QAction
from config import DRAG_TAB_STYLESHEET, CONTEXT_MENU_STYLESHEET, UiConfig

class DraggableTab(QFrame):
    # Change signals to carry raw global position
    drag_started = pyqtSignal(QPoint) 
    drag_moved = pyqtSignal(QPoint)
    drag_ended = pyqtSignal()
    clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setFixedSize(UiConfig.TAB_SIZE, 60)
        self.setStyleSheet(DRAG_TAB_STYLESHEET)
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
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.dragging:
            # Emit raw global pos
            self.drag_moved.emit(event.globalPosition().toPoint())
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.dragging and event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            if (event.globalPosition().toPoint() - self.drag_start_pos).manhattanLength() < 5:
                self.clicked.emit()
            else:
                self.drag_ended.emit()
        else:
            super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setWindowFlags(menu.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # Apply the app's style to the menu
        menu.setStyleSheet(CONTEXT_MENU_STYLESHEET)
        
        close_action = QAction("Quit", self)
        close_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(close_action)
        
        menu.exec(event.globalPos())
