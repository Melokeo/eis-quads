import sys
import json
import os
from enum import Enum
from dataclasses import dataclass, asdict
from PyQt6.QtCore import (Qt, QPoint, QRect, QPropertyAnimation, QEasingCurve, 
                          QSize, pyqtSignal, QTimer, QEvent)
from PyQt6.QtGui import (QColor, QPainter, QPen, QBrush, QFont, QPainterPath, 
                         QRadialGradient, QCursor, QAction)
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QLineEdit, QTextEdit, 
                             QGraphicsDropShadowEffect, QFrame, QMenu, QDialog)

# --- Configuration & Styling ---
APP_WIDTH = 450
APP_HEIGHT = 450
TAB_WIDTH = 20
BG_COLOR = "#1e1e2e"
QUAD_LINES_COLOR = "#313244"
TEXT_COLOR = "#cdd6f4"
ACCENT_COLOR = "#89b4fa"
DOT_COLOR = "#f38ba8"
DOT_SIZE = 16

STYLESHEET = f"""
    QWidget {{
        font-family: 'Segoe UI', sans-serif;
        color: {TEXT_COLOR};
    }}
    QLineEdit, QTextEdit {{
        background-color: #313244;
        border: 1px solid #45475a;
        border-radius: 4px;
        padding: 5px;
        color: white;
    }}
    QPushButton {{
        background-color: {ACCENT_COLOR};
        color: #1e1e2e;
        border: none;
        border-radius: 4px;
        padding: 5px 10px;
        font-weight: bold;
    }}
    QPushButton:hover {{
        background-color: #b4befe;
    }}
    QPushButton#deleteBtn {{
        background-color: #f38ba8;
        color: #1e1e2e;
    }}
    QPushButton#deleteBtn:hover {{
        background-color: #eba0ac;
    }}
    QLabel#Title {{
        font-size: 14px;
        font-weight: bold;
    }}
    QLabel#AxisLabel {{
        color: #6c7086;
        font-size: 10px;
        font-weight: bold;
    }}
"""

# --- Data Management ---
@dataclass
class Task:
    id: str
    title: str
    desc: str
    x: float  # 0.0 to 1.0 (relative to canvas)
    y: float  # 0.0 to 1.0
    
    def to_dict(self):
        return asdict(self)

class TaskManager:
    FILE_NAME = "tasks.json"

    @staticmethod
    def load_tasks():
        if not os.path.exists(TaskManager.FILE_NAME):
            return []
        try:
            with open(TaskManager.FILE_NAME, 'r') as f:
                data = json.load(f)
                return [Task(**t) for t in data]
        except:
            return []

    @staticmethod
    def save_tasks(tasks):
        with open(TaskManager.FILE_NAME, 'w') as f:
            json.dump([t.to_dict() for t in tasks], f)

# --- UI Components ---

class DetailPopup(QDialog):
    """Floating borderless popup for editing details"""
    data_changed = pyqtSignal(object, bool) # task, is_delete

    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self.task = task
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        container = QFrame()
        container.setStyleSheet(f"background-color: {BG_COLOR}; border: 1px solid {ACCENT_COLOR}; border-radius: 8px;")
        
        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        container.setGraphicsEffect(shadow)
        
        inner_layout = QVBoxLayout(container)

        self.title_edit = QLineEdit(task.title)
        self.title_edit.setPlaceholderText("Task Title")
        
        self.desc_edit = QTextEdit(task.desc)
        self.desc_edit.setPlaceholderText("Description...")
        self.desc_edit.setFixedHeight(60)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save)
        
        del_btn = QPushButton("Delete")
        del_btn.setObjectName("deleteBtn")
        del_btn.clicked.connect(self.delete)
        
        btn_layout.addWidget(del_btn)
        btn_layout.addWidget(save_btn)

        inner_layout.addWidget(self.title_edit)
        inner_layout.addWidget(self.desc_edit)
        inner_layout.addLayout(btn_layout)

        layout.addWidget(container)
        self.setFixedSize(250, 180)

    def save(self):
        self.task.title = self.title_edit.text()
        self.task.desc = self.desc_edit.toPlainText()
        self.data_changed.emit(self.task, False)
        self.close()

    def delete(self):
        self.data_changed.emit(self.task, True)
        self.close()

class TaskDot(QWidget):
    """The draggable dot representing a task"""
    moved = pyqtSignal()
    clicked = pyqtSignal(object) # sends self

    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self.task = task
        self.setFixedSize(100, 40) # Larger hit area, but we paint small
        self.dragging = False
        self.offset = QPoint()
        
        # Initial position will be set by parent based on task.x/y
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw Dot
        center_x = DOT_SIZE // 2 + 2
        center_y = DOT_SIZE // 2 + 2
        
        painter.setBrush(QBrush(QColor(DOT_COLOR)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, DOT_SIZE, DOT_SIZE)
        
        # Draw Label (Short)
        painter.setPen(QColor(TEXT_COLOR))
        font = QFont("Segoe UI", 9)
        painter.setFont(font)
        painter.drawText(QRect(DOT_SIZE + 5, 0, 80, DOT_SIZE + 4), 
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, 
                         self.task.title[:10] + ".." if len(self.task.title) > 10 else self.task.title)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.offset = event.pos()
            self.raise_() # Bring to front

    def mouseMoveEvent(self, event):
        if self.dragging and self.parent():
            # Calculate new position
            new_pos = self.mapToParent(event.pos()) - self.offset
            
            # Constrain to parent bounds
            p_width = self.parent().width()
            p_height = self.parent().height()
            
            x = max(0, min(new_pos.x(), p_width - DOT_SIZE))
            y = max(0, min(new_pos.y(), p_height - DOT_SIZE))
            
            self.move(x, y)
            
            # Update data model normalized coordinates
            self.task.x = x / p_width
            self.task.y = y / p_height
            
    def mouseReleaseEvent(self, event):
        if self.dragging:
            self.dragging = False
            self.moved.emit()
        elif event.button() == Qt.MouseButton.LeftButton:
            # It was a click, not a drag
            self.clicked.emit(self)

class MatrixCanvas(QWidget):
    """The background graph and container for dots"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks = []
        self.dots = []
        self.init_ui()

    def init_ui(self):
        self.tasks = TaskManager.load_tasks()
        self.refresh_dots()

    def refresh_dots(self):
        # Clear existing
        for dot in self.dots:
            dot.deleteLater()
        self.dots = []

        # Recreate
        for task in self.tasks:
            self.add_dot_widget(task)

    def add_dot_widget(self, task):
        dot = TaskDot(task, self)
        dot.moved.connect(self.save_data)
        dot.clicked.connect(self.show_details)
        self.dots.append(dot)
        
        # Position it
        # We delay positioning slightly to ensure geometry is calculated, 
        # or calculate based on fixed app size since it's fixed.
        x = int(task.x * APP_WIDTH)
        y = int(task.y * APP_HEIGHT)
        dot.move(x, y)
        dot.show()

    def add_new_task(self):
        import uuid
        # Default to center
        new_task = Task(str(uuid.uuid4()), "New Task", "", 0.5, 0.5)
        self.tasks.append(new_task)
        self.add_dot_widget(new_task)
        self.save_data()

    def save_data(self):
        TaskManager.save_tasks(self.tasks)

    def show_details(self, dot_widget):
        # Position popup near the dot
        popup = DetailPopup(dot_widget.task, self)
        
        # Global position calculation
        global_pos = dot_widget.mapToGlobal(QPoint(DOT_SIZE + 10, 0))
        popup.move(global_pos)
        
        popup.data_changed.connect(self.handle_task_change)
        popup.exec()

    def handle_task_change(self, task, is_delete):
        if is_delete:
            self.tasks = [t for t in self.tasks if t.id != task.id]
            self.refresh_dots()
        else:
            # Update visual label
            for dot in self.dots:
                if dot.task.id == task.id:
                    dot.update()
                    break
        self.save_data()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw Background
        painter.fillRect(self.rect(), QColor(BG_COLOR))
        
        w = self.width()
        h = self.height()
        cx = w // 2
        cy = h // 2

        # Draw Axis Lines
        pen = QPen(QColor(QUAD_LINES_COLOR))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawLine(cx, 0, cx, h)
        painter.drawLine(0, cy, w, cy)

        # Draw Labels
        text_pen = QPen(QColor(ACCENT_COLOR))
        painter.setPen(text_pen)
        font = QFont("Segoe UI", 12, QFont.Weight.Bold)
        painter.setFont(font)
        
        # Quadrant Labels
        painter.setOpacity(0.3)
        painter.drawText(QRect(0, 0, cx, cy), Qt.AlignmentFlag.AlignCenter, "SCHEDULE")
        painter.drawText(QRect(cx, 0, cx, cy), Qt.AlignmentFlag.AlignCenter, "DO NOW")
        painter.drawText(QRect(0, cy, cx, cy), Qt.AlignmentFlag.AlignCenter, "DELETE")
        painter.drawText(QRect(cx, cy, cx, cy), Qt.AlignmentFlag.AlignCenter, "DELEGATE")
        
        # Axis Indicators
        painter.setOpacity(1.0)
        label_font = QFont("Segoe UI", 8)
        painter.setFont(label_font)
        painter.setPen(QColor("#6c7086"))
        
        # X Axis
        painter.drawText(10, cy - 5, "Low Urgency")
        painter.drawText(w - 70, cy - 5, "High Urgency")
        
        # Y Axis (Top is High Importance in typical graphs, but 0,0 is top-left in Qt)
        # Let's map Visuals: Top = High Importance. Bottom = Low Importance.
        painter.drawText(cx + 5, 15, "High Importance")
        painter.drawText(cx + 5, h - 10, "Low Importance")

# --- Main Window Container ---

class SlideWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        self.is_expanded = False
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Window Flags
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                            Qt.WindowType.WindowStaysOnTopHint | 
                            Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Layout
        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setLayout(self.main_layout)

        # 1. The Tab (Handle)
        self.tab = QFrame()
        self.tab.setFixedSize(TAB_WIDTH, 80)
        self.tab.setStyleSheet(f"""
            QFrame {{
                background-color: {ACCENT_COLOR};
                border-top-left-radius: 10px;
                border-bottom-left-radius: 10px;
            }}
            QFrame:hover {{
                background-color: #b4befe;
            }}
        """)
        self.tab.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tab.mousePressEvent = self.toggle_slide

        # Tab Container (To center the tab vertically)
        self.tab_container = QWidget()
        self.tab_container.setFixedWidth(TAB_WIDTH)
        tc_layout = QVBoxLayout(self.tab_container)
        tc_layout.setContentsMargins(0, 0, 0, 0)
        tc_layout.addStretch()
        tc_layout.addWidget(self.tab)
        tc_layout.addStretch()

        # 2. The Content (Matrix)
        self.content_area = QWidget()
        self.content_area.setFixedSize(APP_WIDTH, APP_HEIGHT)
        self.content_area.setStyleSheet(f"background-color: {BG_COLOR}; border-left: 1px solid {QUAD_LINES_COLOR};")
        
        ca_layout = QVBoxLayout(self.content_area)
        ca_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QWidget()
        header.setFixedHeight(40)
        h_layout = QHBoxLayout(header)
        title = QLabel("Eisenhower Matrix")
        title.setObjectName("Title")
        add_btn = QPushButton("+")
        add_btn.setFixedSize(30, 30)
        add_btn.clicked.connect(self.add_task_trigger)
        
        h_layout.addWidget(title)
        h_layout.addStretch()
        h_layout.addWidget(add_btn)
        
        self.matrix = MatrixCanvas()
        
        ca_layout.addWidget(header)
        ca_layout.addWidget(self.matrix)

        self.main_layout.addWidget(self.tab_container)
        self.main_layout.addWidget(self.content_area)

        # Initial Position logic
        self.update_position_geometry()
        
        # Apply Styles
        self.setStyleSheet(STYLESHEET)
        
        # Event Filter for Focus Loss
        QApplication.instance().installEventFilter(self)

    def update_position_geometry(self):
        screen = QApplication.primaryScreen().geometry()
        self.screen_width = screen.width()
        self.screen_height = screen.height()
        
        # Y position: Center of screen
        self.y_pos = (self.screen_height - APP_HEIGHT) // 2
        
        # X positions
        self.x_hidden = self.screen_width - TAB_WIDTH
        self.x_shown = self.screen_width - (APP_WIDTH + TAB_WIDTH)
        
        self.setGeometry(self.x_hidden, self.y_pos, APP_WIDTH + TAB_WIDTH, APP_HEIGHT)

    def toggle_slide(self, event=None):
        start = self.pos()
        if self.is_expanded:
            end = QPoint(self.x_hidden, self.y_pos)
            self.is_expanded = False
        else:
            end = QPoint(self.x_shown, self.y_pos)
            self.is_expanded = True
            self.activateWindow()
            self.content_area.setFocus()

        self.anim.setStartValue(start)
        self.anim.setEndValue(end)
        self.anim.start()

    def slide_in(self):
        if self.is_expanded:
            self.toggle_slide()

    def add_task_trigger(self):
        self.matrix.add_new_task()

    def eventFilter(self, obj, event):
        # Detect global focus change or clicks outside
        if event.type() == QEvent.Type.WindowDeactivate:
            # If we lost focus to another window, slide back in
            if self.is_expanded:
                self.slide_in()
                return True
        return super().eventFilter(obj, event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Ensure High DPI scaling
    if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    window = SlideWindow()
    window.show()
    
    sys.exit(app.exec())