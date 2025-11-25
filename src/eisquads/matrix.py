import uuid
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QColor, QPainter, QPen, QFont, QCursor
from PyQt6.QtWidgets import QWidget, QPushButton, QDialog
from config import BG_COLOR, QUAD_LINES_COLOR, DOT_SIZE
from models import Task, TaskManager
from items import TaskDot
from dialogs import NameInput, DetailPopup

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
