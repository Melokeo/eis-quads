import uuid
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QColor, QPainter, QPen, QFont, QCursor
from PyQt6.QtWidgets import QWidget, QPushButton, QDialog, QFrame
from config import UiConfig
from models import Task, TaskManager
from items import TaskDot
from dialogs import NameInput, DetailPopup

class MatrixCanvas(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks = []
        self.dots = []
        self.locked = False
        self.init_ui()

        # minimal add button
        self.add_btn = QPushButton("+", self)
        self.add_btn.setObjectName("addBtn")
        self.add_btn.setFixedSize(30, 30)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.clicked.connect(self.add_new_task)
        self.add_btn.hide()
        # position set in resizeEvent

    def init_ui(self):
        self.tasks = TaskManager.load_tasks()
        self.refresh_dots()

    def resizeEvent(self, event):
        # place add button in top right corner
        self.add_btn.move(self.width() - 40, 10)
        # reposition dots based on new size
        for dot in self.dots:
            dot.update_position()
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
        
        # final pass to resolve overlaps after all dots added
        for dot in self.dots:
            dot.update_position()

    def add_dot_widget(self, task):
        dot = TaskDot(task, self)
        dot.moved.connect(self.on_dot_moved)
        # dot.clicked.connect(self.show_details) # detail page hidden for now
        self.dots.append(dot)
        dot.update_position()
        dot.show()

    def on_dot_moved(self):
        # Update all dots to resolve overlaps dynamically
        for dot in self.dots:
            dot.update_position()
        self.save_data()

    def add_new_task(self, x=0.5, y=0.5):
        # show input dialog
        dialog = NameInput(self)
        # center dialog on cursor or center of widget
        if self.rect().contains(self.mapFromGlobal(QCursor.pos())):
            dialog.move(QCursor.pos())
        else:
            global_pos = self.mapToGlobal(self.rect().center())
            dialog.move(global_pos.x() - 100, global_pos.y() - 20)
            
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.input.text().strip():
            name = dialog.input.text().strip()
            new_task = Task(str(uuid.uuid4()), name, "", x, y)
            self.tasks.append(new_task)
            self.add_dot_widget(new_task)
            self.save_data()

    def save_data(self):
        TaskManager.save_tasks(self.tasks)

    def show_details(self, dot_widget):
        popup = DetailPopup(dot_widget.task, self)
        global_pos = dot_widget.mapToGlobal(QPoint(UiConfig.DOT_SIZE + 10, 0))
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
                    dot.update_position()
                    break
        self.save_data()

    def clear_all_tasks(self):
        self.tasks = []
        self.refresh_dots()
        self.save_data()

    def reload_tasks(self):
        self.tasks = TaskManager.load_tasks()
        self.refresh_dots()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2

        # axes
        pen = QPen(QColor(UiConfig.QUAD_LINES_COLOR))
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

    def set_locked(self, locked: bool):
        self.locked = locked
