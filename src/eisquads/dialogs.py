from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QTextEdit, QPushButton, QFrame, QGraphicsDropShadowEffect)
from PyQt6.QtGui import QColor
from config import INPUT_STYLESHEET, DETAIL_POPUP_STYLESHEET
from models import Task

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
        self.input.setStyleSheet(INPUT_STYLESHEET)
        self.input.returnPressed.connect(self.accept)
        layout.addWidget(self.input)

    def showEvent(self, event):
        super().showEvent(event)
        self.input.setFocus()

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
        container.setStyleSheet(DETAIL_POPUP_STYLESHEET)
        
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
