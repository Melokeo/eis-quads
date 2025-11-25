import uuid
from PyQt6.QtCore import Qt, QPoint, QPointF
from PyQt6.QtGui import QColor, QPainter, QPen, QFont, QCursor, QPainterPath
from PyQt6.QtWidgets import QWidget, QPushButton, QDialog, QFrame
from config import UiConfig
from models import Task, TaskManager
from items import TaskDot
from dialogs import NameInput, DetailPopup
import math

class MatrixCanvas(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks = []
        self.dots = []
        self.locked = False
        self.temp_link_start = None
        self.temp_link_end = None
        self.undo_stack = []
        self.redo_stack = []
        self.overlay = DependencyOverlay(self)
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
        self.overlay.resize(self.size())
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
        dot.link_started.connect(self.on_link_started)
        dot.link_dragging.connect(self.on_link_dragging)
        dot.link_ended.connect(self.on_link_ended)
        dot.drag_started.connect(self.on_dot_drag_start)
        # dot.clicked.connect(self.show_details) # detail page hidden for now
        self.dots.append(dot)
        dot.update_position()
        dot.show()
        self.overlay.raise_()

    def get_state(self):
        # Deep copy of tasks state
        return [
            Task(t.id, t.title, t.desc, t.x, t.y, t.completed, list(t.dependencies))
            for t in self.tasks
        ]

    def restore_state(self, state):
        # Restore tasks from state
        self.tasks = [
            Task(t.id, t.title, t.desc, t.x, t.y, t.completed, list(t.dependencies))
            for t in state
        ]
        self.refresh_dots()
        self.overlay.update()
        self.save_data()

    def push_undo(self, action_type, target_id=None):
        current_state = self.get_state()
        self.undo_stack.append({
            'state': current_state,
            'action': action_type,
            'target_id': target_id
        })
        
        # Cap the stack size to prevent memory bloat
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)
            
        self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack:
            return
            
        # Save current state to redo stack
        current_state = self.get_state()
        last_action = self.undo_stack.pop()
        
        self.redo_stack.append({
            'state': current_state,
            'action': last_action['action'],
            'target_id': last_action['target_id']
        })
        
        self.restore_state(last_action['state'])

    def redo(self):
        if not self.redo_stack:
            return
            
        # Save current state to undo stack
        current_state = self.get_state()
        next_action = self.redo_stack.pop()
        
        self.undo_stack.append({
            'state': current_state,
            'action': next_action['action'],
            'target_id': next_action['target_id']
        })
        
        self.restore_state(next_action['state'])

    def on_dot_drag_start(self, task_id):
        self.push_undo('move', task_id)

    def on_link_started(self, dot):
        self.temp_link_start = dot
        self.temp_link_end = dot.get_dot_center()
        self.overlay.update()

    def on_link_dragging(self, global_pos):
        self.temp_link_end = self.mapFromGlobal(global_pos)
        self.overlay.update()

    def on_link_ended(self, global_pos):
        end_pos = self.mapFromGlobal(global_pos)
        target = self.childAt(end_pos)
        
        # childAt might return the label or other parts, walk up to find TaskDot
        while target and not isinstance(target, TaskDot):
            target = target.parent()
            
        if target and isinstance(target, TaskDot) and target != self.temp_link_start:
            self.push_undo('link')
            # toggle dependency
            start_id = self.temp_link_start.task.id
            target_id = target.task.id
            
            if start_id in target.task.dependencies:
                target.task.dependencies.remove(start_id)
            else:
                # prevent cycles? nah, let chaos reign (or maybe just simple check)
                if target_id not in self.temp_link_start.task.dependencies:
                    target.task.dependencies.append(start_id)
            
            self.save_data()
            
        self.temp_link_start = None
        self.temp_link_end = None
        self.overlay.update()

    def on_dot_moved(self):
        # update all dots to resolve overlaps dynamically
        for dot in self.dots:
            dot.update_position()
        self.overlay.update() # repaint lines
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
            self.push_undo('add')
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
            # clean up dependencies
            for t in self.tasks:
                if task.id in t.dependencies:
                    t.dependencies.remove(task.id)
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

    def draw_dependencies(self, painter):
        # map id to dot center
        dot_map = {d.task.id: d for d in self.dots}
        
        pen = QPen(QColor(UiConfig.ACCENT_COLOR))
        pen.setWidth(2)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # draw existing links
        for dot in self.dots:
            start_center = dot.get_dot_center()
            for dep_id in dot.task.dependencies:
                if dep_id in dot_map:
                    end_dot = dot_map[dep_id]
                    end_center = end_dot.get_dot_center()
                    self.draw_curved_arrow(painter, end_center, start_center)

        # draw temp link
        if self.temp_link_start and self.temp_link_end:
            start = self.temp_link_start.get_dot_center()
            self.draw_curved_arrow(painter, start, self.temp_link_end)

    def draw_curved_arrow(self, painter, start, end):
        start = QPointF(start)
        end = QPointF(end)
        path = QPainterPath()
        path.moveTo(start)
        
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        
        # control point for curve
        ctrl = QPointF(start.x() + dx * 0.5, start.y())
        path.quadTo(ctrl, end)
        
        painter.drawPath(path)
        
        # arrowhead
        # calculate angle at end
        # derivative of quad bezier at t=1 is 2(P2 - P1) where P1 is ctrl, P2 is end
        # actually it's 2(1-t)(P1-P0) + 2t(P2-P1). At t=1, it's 2(P2-P1)
        
        arrow_dx = end.x() - ctrl.x()
        arrow_dy = end.y() - ctrl.y()
        angle = math.atan2(arrow_dy, arrow_dx)
        
        arrow_len = 10
        arrow_angle = math.pi / 6
        
        p1 = QPointF(end.x() - arrow_len * math.cos(angle - arrow_angle),
                     end.y() - arrow_len * math.sin(angle - arrow_angle))
        p2 = QPointF(end.x() - arrow_len * math.cos(angle + arrow_angle),
                     end.y() - arrow_len * math.sin(angle + arrow_angle))
        
        painter.setBrush(QColor(UiConfig.ACCENT_COLOR))
        painter.setPen(Qt.PenStyle.NoPen)
        
        arrow_path = QPainterPath()
        arrow_path.moveTo(end)
        arrow_path.lineTo(p1)
        arrow_path.lineTo(p2)
        arrow_path.closeSubpath()
        
        painter.drawPath(arrow_path)
        
        # restore pen
        pen = QPen(QColor(UiConfig.ACCENT_COLOR))
        pen.setWidth(2)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

    def set_locked(self, locked: bool):
        self.locked = locked

class DependencyOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.parent():
            self.parent().draw_dependencies(painter)
