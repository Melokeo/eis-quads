from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QBrush, QFont, QFontMetrics
from PyQt6.QtWidgets import QWidget
from config import UiConfig
from models import Task

class TaskDot(QWidget):
    moved = pyqtSignal()
    clicked = pyqtSignal(object)

    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self.task = task
        self.dragging = False
        self.drag_start_global = QPoint()
        self.drag_start_dot_pos = QPoint()
        self.dot_local_pos = QPoint(0, 0)
        self.text_rect = QRect()
        self.text_align = Qt.AlignmentFlag.AlignLeft
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_position()
        self.show()

    def update_position(self):
        if not self.parent(): return
        
        p_w = self.parent().width()
        p_h = self.parent().height()
        cx, cy = p_w // 2, p_h // 2
        
        dx = int(self.task.x * p_w)
        dy = int(self.task.y * p_h)
        
        # Clamp dot to screen
        dx = max(0, min(dx, p_w - UiConfig.DOT_SIZE))
        dy = max(0, min(dy, p_h - UiConfig.DOT_SIZE))
        
        in_right = dx > cx
        
        font = QFont(UiConfig.DOT_FONT, UiConfig.DOT_FONT_SIZE)
        fm = QFontMetrics(font)
        label = self.task.title
        
        MAX_W = 100
        rect = fm.boundingRect(QRect(0, 0, MAX_W, 0), Qt.TextFlag.TextWordWrap, label)
        text_w = rect.width() + 5
        text_h = rect.height()
        
        place_right = True
        
        if in_right:
            if dx + UiConfig.DOT_SIZE + text_w <= p_w:
                place_right = True
            elif dx - text_w >= cx:
                place_right = False
            else:
                place_right = True
        else:
            if dx - text_w >= 0:
                place_right = False
            elif dx + UiConfig.DOT_SIZE + text_w <= cx:
                place_right = True
            else:
                place_right = False
                
        ds = UiConfig.DOT_SIZE
        total_h = max(ds, text_h)
        
        if place_right:
            self.dot_local_pos = QPoint(0, (total_h - ds)//2)
            self.text_rect = QRect(ds + 5, 0, text_w, total_h)
            w = ds + 5 + text_w
            x = dx
            self.text_align = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextWordWrap
        else:
            self.dot_local_pos = QPoint(text_w + 5, (total_h - ds)//2)
            self.text_rect = QRect(0, 0, text_w, total_h)
            w = text_w + 5 + ds
            x = dx - text_w - 5
            self.text_align = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextWordWrap
            
        y = dy - (total_h - ds)//2
        
        self.setGeometry(x, y, w, total_h)
        self.update()

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
        painter.drawEllipse(self.dot_local_pos.x(), self.dot_local_pos.y(), UiConfig.DOT_SIZE, UiConfig.DOT_SIZE)
        
        # draw label
        painter.setPen(QColor(UiConfig.TEXT_COLOR))
        font = QFont(UiConfig.DOT_FONT, UiConfig.DOT_FONT_SIZE)
        painter.setFont(font)
        label = self.task.title
        
        painter.drawText(self.text_rect, 
                         self.text_align, 
                         label)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_start_global = event.globalPosition().toPoint()
            
            if self.parent():
                p_w, p_h = self.parent().width(), self.parent().height()
                self.drag_start_dot_pos = QPoint(int(self.task.x * p_w), int(self.task.y * p_h))
            
            self.raise_()

    def mouseMoveEvent(self, event):
        if self.dragging and self.parent():
            curr_global = event.globalPosition().toPoint()
            delta = curr_global - self.drag_start_global
            
            new_dot_x = self.drag_start_dot_pos.x() + delta.x()
            new_dot_y = self.drag_start_dot_pos.y() + delta.y()
            
            p_w, p_h = self.parent().width(), self.parent().height()
            
            new_dot_x = max(0, min(new_dot_x, p_w - UiConfig.DOT_SIZE))
            new_dot_y = max(0, min(new_dot_y, p_h - UiConfig.DOT_SIZE))
            
            self.task.x = new_dot_x / p_w
            self.task.y = new_dot_y / p_h
            
            self.update_position()
            self.moved.emit()
            
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
                
                # Use dot position from task, not widget position
                curr_x = int(self.task.x * p_w)
                curr_y = int(self.task.y * p_h)
                
                new_x = self._resolve_overlap(curr_x, axis_x, UiConfig.DOT_SIZE)
                new_y = self._resolve_overlap(curr_y, axis_y, UiConfig.DOT_SIZE)
                
                if new_x != curr_x or new_y != curr_y:
                    self.task.x = new_x / p_w
                    self.task.y = new_y / p_h
                    self.update_position()

            self.moved.emit()
            
        elif event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self)
