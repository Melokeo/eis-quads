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

# --- Data Management ---
@dataclass
class Task:
    id: str
    title: str
    desc: str
    x: float
    y: float
    
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

class NameInput(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.input = QLineEdit()
        self.input.setPlaceholderText("task name...")
        self.input.setFixedSize(200, 40)
        self.input.setStyleSheet(f"""
            background-color: {BG_COLOR}; 
            color: {TEXT_COLOR};
            border: 2px solid {ACCENT_COLOR}; 
            border-radius: 8px;
            padding: 5px;
            font-size: 14px;
        """)
        self.input.returnPressed.connect(self.accept)
        layout.addWidget(self.input)

class NameInput(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.input = QLineEdit()
        self.input.setPlaceholderText("task name...")
        self.input.setFixedSize(200, 40)
        self.input.setStyleSheet(f"""
            background-color: {BG_COLOR}; 
            color: {TEXT_COLOR};
            border: 2px solid {ACCENT_COLOR}; 
            border-radius: 8px;
            padding: 5px;
            font-size: 14px;
        """)
        self.input.returnPressed.connect(self.accept)
        layout.addWidget(self.input)

class TaskDot(QWidget):
    moved = pyqtSignal()
    clicked = pyqtSignal(object)

    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self.task = task
        self.setFixedSize(120, 30)
        self.dragging = False
        self.offset = QPoint()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # draw dot
        painter.setBrush(QBrush(QColor(DOT_COLOR)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 6, DOT_SIZE, DOT_SIZE)
        
        # draw label
        painter.setPen(QColor(TEXT_COLOR))
        font = QFont("Segoe UI", 9)
        painter.setFont(font)
        label = self.task.title
        if len(label) > 12: label = label[:12] + ".."
        painter.drawText(QRect(DOT_SIZE + 4, 0, 100, 30), 
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, 
                         label)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.offset = event.pos()
            self.raise_()

    def mouseMoveEvent(self, event):
        if self.dragging and self.parent():
            new_pos = self.mapToParent(event.pos()) - self.offset
            p_w, p_h = self.parent().width(), self.parent().height()
            
            x = max(0, min(new_pos.x(), p_w - DOT_SIZE))
            y = max(0, min(new_pos.y(), p_h - DOT_SIZE))
            self.move(x, y)
            
            self.task.x = x / p_w
            self.task.y = y / p_h
            
    def mouseReleaseEvent(self, event):
        if self.dragging:
            self.dragging = False
            
            # snap to quadrant center if near border (0.5)
            # threshold is 5% of normalized width
            threshold = 0.05
            snapped = False
            
            if abs(self.task.x - 0.5) < threshold:
                self.task.x = 0.25 if self.task.x < 0.5 else 0.75
                snapped = True
                
            if abs(self.task.y - 0.5) < threshold:
                self.task.y = 0.25 if self.task.y < 0.5 else 0.75
                snapped = True
            
            if snapped and self.parent():
                self.move(int(self.task.x * self.parent().width()), 
                          int(self.task.y * self.parent().height()))

            self.moved.emit()
            
        elif event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self)

class DetailPopup(QDialog):
    data_changed = pyqtSignal(object, bool)

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
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        container.setGraphicsEffect(shadow)
        
        inner_layout = QVBoxLayout(container)
        inner_layout.setSpacing(5)
        inner_layout.setContentsMargins(10, 10, 10, 10)

        self.title_edit = QLineEdit(task.title)
        self.title_edit.setPlaceholderText("Task Title")
        
        self.desc_edit = QTextEdit(task.desc)
        self.desc_edit.setPlaceholderText("Description...")
        self.desc_edit.setFixedHeight(60)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save)
        
        del_btn = QPushButton("Del")
        del_btn.setObjectName("deleteBtn")
        del_btn.clicked.connect(self.delete)
        
        btn_layout.addWidget(del_btn)
        btn_layout.addWidget(save_btn)

        inner_layout.addWidget(self.title_edit)
        inner_layout.addWidget(self.desc_edit)
        inner_layout.addLayout(btn_layout)

        layout.addWidget(container)
        self.setFixedSize(220, 160)

    def save(self):
        self.task.title = self.title_edit.text()
        self.task.desc = self.desc_edit.toPlainText()
        self.data_changed.emit(self.task, False)
        self.close()

    def delete(self):
        self.data_changed.emit(self.task, True)
        self.close()

class TaskDot(QWidget):
    moved = pyqtSignal()
    clicked = pyqtSignal(object)

    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self.task = task
        self.setFixedSize(120, 30)
        self.dragging = False
        self.offset = QPoint()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw Dot
        painter.setBrush(QBrush(QColor(DOT_COLOR)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 6, DOT_SIZE, DOT_SIZE)
        
        # Draw Label
        painter.setPen(QColor(TEXT_COLOR))
        font = QFont("Segoe UI", 9)
        painter.setFont(font)
        label = self.task.title
        if len(label) > 12: label = label[:12] + ".."
        painter.drawText(QRect(DOT_SIZE + 4, 0, 100, 30), 
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, 
                         label)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.offset = event.pos()
            self.raise_()

    def mouseMoveEvent(self, event):
        if self.dragging and self.parent():
            new_pos = self.mapToParent(event.pos()) - self.offset
            p_w, p_h = self.parent().width(), self.parent().height()
            
            x = max(0, min(new_pos.x(), p_w - DOT_SIZE))
            y = max(0, min(new_pos.y(), p_h - DOT_SIZE))
            self.move(x, y)
            
            self.task.x = x / p_w
            self.task.y = y / p_h
            
    def mouseReleaseEvent(self, event):
        if self.dragging:
            self.dragging = False
            self.moved.emit()
        elif event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self)

class MatrixCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks = []
        self.dots = []
        self.init_ui()

        # minimal Add Button embedded in canvas
        self.add_btn = QPushButton("+", self)
        self.add_btn.setObjectName("addBtn")
        self.add_btn.setFixedSize(30, 30)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.clicked.connect(self.add_new_task)
        # position will be set in resizeEvent

    def init_ui(self):
        self.tasks = TaskManager.load_tasks()
        self.refresh_dots()

    def resizeEvent(self, event):
        # place add button in top right corner
        self.add_btn.move(self.width() - 40, 10)
        # reposition dots based on new size
        for dot in self.dots:
            dot.move(int(dot.task.x * self.width()), int(dot.task.y * self.height()))
        super().resizeEvent(event)
        
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # normalize coordinates 0.0 - 1.0
            nx = event.pos().x() / self.width()
            ny = event.pos().y() / self.height()
            self.add_new_task(nx, ny)

    def refresh_dots(self):
        for dot in self.dots: dot.deleteLater()
        self.dots = []
        for task in self.tasks: self.add_dot_widget(task)

    def add_dot_widget(self, task):
        dot = TaskDot(task, self)
        dot.moved.connect(self.save_data)
        dot.clicked.connect(self.show_details)
        self.dots.append(dot)
        x = int(task.x * self.width())
        y = int(task.y * self.height())
        dot.move(x, y)
        dot.show()

    def add_new_task(self, x=0.5, y=0.5):
        # show minimal input dialog
        dialog = NameInput(self)
        # center dialog on cursor or center of widget
        if self.rect().contains(self.mapFromGlobal(QCursor.pos())):
            dialog.move(QCursor.pos())
        else:
            global_pos = self.mapToGlobal(self.rect().center())
            dialog.move(global_pos.x() - 100, global_pos.y() - 20)
            
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.input.text().strip():
            import uuid
            name = dialog.input.text().strip()
            new_task = Task(str(uuid.uuid4()), name, "", x, y)
            self.tasks.append(new_task)
            self.add_dot_widget(new_task)
            self.save_data()

    def save_data(self):
        TaskManager.save_tasks(self.tasks)

    def show_details(self, dot_widget):
        popup = DetailPopup(dot_widget.task, self)
        global_pos = dot_widget.mapToGlobal(QPoint(DOT_SIZE + 10, 0))
        popup.move(global_pos)
        popup.data_changed.connect(self.handle_task_change)
        popup.exec()

    def handle_task_change(self, task, is_delete):
        if is_delete:
            self.tasks = [t for t in self.tasks if t.id != task.id]
            self.refresh_dots()
        else:
            for dot in self.dots:
                if dot.task.id == task.id:
                    dot.update()
                    break
        self.save_data()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.fillRect(self.rect(), QColor(BG_COLOR))
        
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2

        # axes
        pen = QPen(QColor(QUAD_LINES_COLOR))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawLine(cx, 0, cx, h)
        painter.drawLine(0, cy, w, cy)

        # labels
        painter.setPen(QColor("#6c7086"))
        font = QFont("Segoe UI", 8, QFont.Weight.Bold)
        painter.setFont(font)
        
        # minimal labels
        painter.drawText(w - 30, cy - 5, "Urg")
        painter.drawText(cx + 5, 15, "Imp")

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

# main window
class SlideWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.dock_side = DockSide.RIGHT
        self.is_expanded = False
        self.drag_offset = QPoint() # Store the offset here

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                            Qt.WindowType.WindowStaysOnTopHint | 
                            Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Components
        self.tab = DraggableTab()
        self.tab.drag_started.connect(self.handle_drag_start) # Connect start
        self.tab.drag_moved.connect(self.handle_drag_move)
        self.tab.drag_ended.connect(self.handle_drag_end)
        self.tab.clicked.connect(self.toggle_slide)

        self.content = MatrixCanvas()
        self.content.setFixedSize(APP_WIDTH, APP_HEIGHT)
        self.content.setStyleSheet(f"background-color: {BG_COLOR}; border: 1px solid {QUAD_LINES_COLOR};")

        self.layout_container = QWidget(self)
        self.main_layout = QHBoxLayout(self.layout_container)
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(0)
        
        self.setStyleSheet(STYLESHEET)
        QApplication.instance().installEventFilter(self)
        
        self.snap_to_screen_edge()

    def handle_drag_start(self, global_pos):
        # Calculate where the mouse is relative to the window top-left
        self.drag_offset = global_pos - self.pos()

    def handle_drag_move(self, global_pos):
        # Move window to match mouse pos minus the initial offset
        self.move(global_pos - self.drag_offset)

    def handle_drag_end(self):
        self.snap_to_screen_edge()

    def snap_to_screen_edge(self):
        center = self.geometry().center()
        screen = QApplication.screenAt(center)
        if not screen: screen = QApplication.primaryScreen()
        
        s_geo = screen.geometry()
        
        dist_left = abs(center.x() - s_geo.left())
        dist_right = abs(center.x() - s_geo.right())
        dist_top = abs(center.y() - s_geo.top())
        dist_bottom = abs(center.y() - s_geo.bottom())
        
        min_dist = min(dist_left, dist_right, dist_top, dist_bottom)
        
        if min_dist == dist_left: self.dock_side = DockSide.LEFT
        elif min_dist == dist_right: self.dock_side = DockSide.RIGHT
        elif min_dist == dist_top: self.dock_side = DockSide.TOP
        elif min_dist == dist_bottom: self.dock_side = DockSide.BOTTOM
        
        self.update_layout(s_geo)
        
        self.is_expanded = False
        self.anim.setStartValue(self.pos())
        self.anim.setEndValue(self.get_hidden_pos(s_geo))
        self.anim.start()

    def update_layout(self, s_geo):
        # explicitly remove widgets from layout so they aren't destroyed
        # with the layout. setParent alone is not enough in pyqt6.
        if self.main_layout is not None:
            self.main_layout.removeWidget(self.tab)
            self.main_layout.removeWidget(self.content)
            self.tab.setParent(self.layout_container)
            self.content.setParent(self.layout_container)
        
        # safe to destroy the old layout now
        QWidget().setLayout(self.main_layout)
        
        radius_style = ""
        
        # recreate layout based on dock side
        if self.dock_side in [DockSide.LEFT, DockSide.RIGHT]:
            self.main_layout = QHBoxLayout(self.layout_container)
            self.tab.setFixedSize(TAB_SIZE, 60)
            
            if self.dock_side == DockSide.LEFT:
                radius_style = "border-top-left-radius: 0px; border-bottom-left-radius: 0px; border-top-right-radius: 10px; border-bottom-right-radius: 10px;"
            else: 
                radius_style = "border-top-left-radius: 10px; border-bottom-left-radius: 10px; border-top-right-radius: 0px; border-bottom-right-radius: 0px;"
                
        else:
            self.main_layout = QVBoxLayout(self.layout_container)
            self.tab.setFixedSize(60, TAB_SIZE)
            
            if self.dock_side == DockSide.TOP:
                radius_style = "border-top-left-radius: 0px; border-top-right-radius: 0px; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px;"
            else: 
                radius_style = "border-top-left-radius: 10px; border-top-right-radius: 10px; border-bottom-left-radius: 0px; border-bottom-right-radius: 0px;"

        self.tab.setStyleSheet(f"""
            QFrame {{
                background-color: {ACCENT_COLOR};
                {radius_style}
            }}
            QFrame:hover {{
                background-color: #b4befe;
            }}
        """)

        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(0)

        # re-add items to the new layout
        if self.dock_side == DockSide.LEFT:
            self.main_layout.addWidget(self.content)
            self.main_layout.addWidget(self.tab)
            self.main_layout.setAlignment(self.tab, Qt.AlignmentFlag.AlignVCenter)
        elif self.dock_side == DockSide.RIGHT:
            self.main_layout.addWidget(self.tab)
            self.main_layout.addWidget(self.content)
            self.main_layout.setAlignment(self.tab, Qt.AlignmentFlag.AlignVCenter)
        elif self.dock_side == DockSide.TOP:
            self.main_layout.addWidget(self.content)
            self.main_layout.addWidget(self.tab)
            self.main_layout.setAlignment(self.tab, Qt.AlignmentFlag.AlignHCenter)
        elif self.dock_side == DockSide.BOTTOM:
            self.main_layout.addWidget(self.tab)
            self.main_layout.addWidget(self.content)
            self.main_layout.setAlignment(self.tab, Qt.AlignmentFlag.AlignHCenter)

        if self.dock_side in [DockSide.LEFT, DockSide.RIGHT]:
            self.resize(APP_WIDTH + TAB_SIZE, APP_HEIGHT)
            self.layout_container.resize(APP_WIDTH + TAB_SIZE, APP_HEIGHT)
        else:
            self.resize(APP_WIDTH, APP_HEIGHT + TAB_SIZE)
            self.layout_container.resize(APP_WIDTH, APP_HEIGHT + TAB_SIZE)

    def get_hidden_pos(self, s_geo):
        if self.dock_side == DockSide.LEFT:
            # Window at left edge. Content is left of Tab.
            # Shown: Content visible at 0. Tab at APP_WIDTH.
            # Hidden: Content at -APP_WIDTH. Tab at 0.
            # Position of Window top-left:
            return QPoint(s_geo.left() - APP_WIDTH, max(s_geo.top(), min(self.y(), s_geo.bottom() - APP_HEIGHT)))
        
        elif self.dock_side == DockSide.RIGHT:
            # Window at right edge. Tab | Content.
            # Hidden: Window at ScreenRight - TAB.
            return QPoint(s_geo.right() - TAB_SIZE, max(s_geo.top(), min(self.y(), s_geo.bottom() - APP_HEIGHT)))
            
        elif self.dock_side == DockSide.TOP:
            # Top edge. Content / Tab.
            # Hidden: Window Top at -APP_HEIGHT.
            return QPoint(max(s_geo.left(), min(self.x(), s_geo.right() - APP_WIDTH)), s_geo.top() - APP_HEIGHT)
            
        elif self.dock_side == DockSide.BOTTOM:
            # Bottom edge. Tab / Content.
            # Hidden: Window Top at ScreenBottom - TAB.
            return QPoint(max(s_geo.left(), min(self.x(), s_geo.right() - APP_WIDTH)), s_geo.bottom() - TAB_SIZE)

    def get_shown_pos(self, s_geo):
        current = self.get_hidden_pos(s_geo) # Use current 'orthagonal' coord
        
        if self.dock_side == DockSide.LEFT:
            return QPoint(s_geo.left(), current.y())
        elif self.dock_side == DockSide.RIGHT:
            return QPoint(s_geo.right() - (APP_WIDTH + TAB_SIZE), current.y())
        elif self.dock_side == DockSide.TOP:
            return QPoint(current.x(), s_geo.top())
        elif self.dock_side == DockSide.BOTTOM:
            return QPoint(current.x(), s_geo.bottom() - (APP_HEIGHT + TAB_SIZE))

    def toggle_slide(self):
        screen = QApplication.screenAt(self.geometry().center())
        if not screen: screen = QApplication.primaryScreen()
        s_geo = screen.geometry()

        start = self.pos()
        if self.is_expanded:
            end = self.get_hidden_pos(s_geo)
            self.is_expanded = False
        else:
            end = self.get_shown_pos(s_geo)
            self.is_expanded = True
            self.activateWindow()
            self.content.setFocus()

        self.anim.setStartValue(start)
        self.anim.setEndValue(end)
        self.anim.start()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.WindowDeactivate and self.is_expanded:
            self.toggle_slide()
            return True
        return super().eventFilter(obj, event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    window = SlideWindow()
    window.show()
    sys.exit(app.exec())