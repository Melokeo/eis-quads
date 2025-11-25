from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QBrush, QFont
from PyQt6.QtWidgets import QWidget
from config import DOT_SIZE, TEXT_COLOR
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
            
            # update task coordinates immediately for color calculation
            self.task.x = x / p_w
            self.task.y = y / p_h
            
            # force repaint to show new color
            self.update()
            
    def mouseReleaseEvent(self, event):
        if self.dragging:
            self.dragging = False
            
            if self.parent():
                p_w = self.parent().width()
                p_h = self.parent().height()
                
                # Get current pixel positions
                curr_x = self.x()
                curr_y = self.y()
                
                # Define axis locations
                axis_x = p_w // 2
                axis_y = p_h // 2
                
                snapped = False
                new_x = curr_x
                new_y = curr_y
                
                # 1. Check Vertical Axis Overlap
                # Logic: Left side is left of axis, Right side is right of axis
                if curr_x < axis_x and (curr_x + DOT_SIZE) > axis_x:
                    snapped = True
                    # Decide direction based on where the center of the dot is
                    if (curr_x + DOT_SIZE / 2) < axis_x:
                        new_x = axis_x - DOT_SIZE - 2  # Push just left of axis
                    else:
                        new_x = axis_x + 2             # Push just right of axis

                # 2. Check Horizontal Axis Overlap
                if curr_y < axis_y and (curr_y + DOT_SIZE) > axis_y:
                    snapped = True
                    if (curr_y + DOT_SIZE / 2) < axis_y:
                        new_y = axis_y - DOT_SIZE - 2  # Push just above axis
                    else:
                        new_y = axis_y + 2             # Push just below axis
            
                if snapped:
                    self.move(int(new_x), int(new_y))
                    # Update normalized coordinates
                    self.task.x = new_x / p_w
                    self.task.y = new_y / p_h
                    self.update() # Force color refresh

            self.moved.emit()
            
        elif event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self)
