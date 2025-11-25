from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QBrush, QFont
from PyQt6.QtWidgets import QWidget
from config import UiConfig
from models import Task

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

    def get_color(self):
        # determine quadrant based on current normalized position
        # x axis: left (low urg) / right (high urg)
        # y axis: top (high imp) / bottom (low imp)
        
        x = self.task.x
        y = self.task.y
        
        is_urg = x > 0.5
        is_imp = y < 0.5
        
        if is_urg and is_imp:
            return "#ff5555" # red (urg/imp)
        elif is_urg and not is_imp:
            return "#f9e2af" # dim yellow (urg/not imp)
        elif not is_urg and is_imp:
            return "#fab387" # orange (imp)
        else:
            return "#585b70" # grey (not urg/not imp)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # draw dot with dynamic color
        painter.setBrush(QBrush(QColor(self.get_color())))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 6, UiConfig.DOT_SIZE, UiConfig.DOT_SIZE)
        
        # draw label
        painter.setPen(QColor(UiConfig.TEXT_COLOR))
        font = QFont("Segoe UI", 9)
        painter.setFont(font)
        label = self.task.title
        if len(label) > 12: label = label[:12] + ".."
        painter.drawText(QRect(UiConfig.DOT_SIZE + 4, 0, 100, 30), 
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
            
            x = max(0, min(new_pos.x(), p_w - UiConfig.DOT_SIZE))
            y = max(0, min(new_pos.y(), p_h - UiConfig.DOT_SIZE))
            self.move(x, y)
            
            # update task coordinates immediately for color calculation
            self.task.x = x / p_w
            self.task.y = y / p_h
            
            # force repaint to show new color
            self.update()
            
    def _resolve_overlap(self, current_pos, axis_pos, size):
        if current_pos < axis_pos and (current_pos + size) > axis_pos:
            center = current_pos + size / 2
            if center < axis_pos:
                return axis_pos - size - 2
            else:
                return axis_pos + 2
        return current_pos

    def mouseReleaseEvent(self, event):
        if self.dragging:
            self.dragging = False
            
            if self.parent():
                p_w, p_h = self.parent().width(), self.parent().height()
                axis_x, axis_y = p_w // 2, p_h // 2
                
                new_x = self._resolve_overlap(self.x(), axis_x, UiConfig.DOT_SIZE)
                new_y = self._resolve_overlap(self.y(), axis_y, UiConfig.DOT_SIZE)
                
                if new_x != self.x() or new_y != self.y():
                    self.move(int(new_x), int(new_y))
                    self.task.x = new_x / p_w
                    self.task.y = new_y / p_h
                    self.update()

            self.moved.emit()
            
        elif event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self)
