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
        
        # Dot position (top-left of the dot itself)
        dot_x = int(self.task.x * p_w)
        dot_y = int(self.task.y * p_h)
        
        ds = UiConfig.DOT_SIZE
        # Clamp dot to screen
        dot_x = max(0, min(dot_x, p_w - ds))
        dot_y = max(0, min(dot_y, p_h - ds))
        
        font = QFont(UiConfig.DOT_FONT, UiConfig.DOT_FONT_SIZE)
        fm = QFontMetrics(font)
        label = self.task.title
        
        MAX_W = 100
        rect = fm.boundingRect(QRect(0, 0, MAX_W, 0), Qt.TextFlag.TextWordWrap, label)
        text_w = rect.width() + 5
        text_h = rect.height()
        
        siblings = [c for c in self.parent().children() if isinstance(c, TaskDot) and c is not self and c.isVisible()]
        
        candidates = []
        for p_type in ['right', 'left', 'top', 'bottom']:
            candidates.append(self._create_candidate(p_type, dot_x, dot_y, text_w, text_h, ds))

        best = None
        min_score = float('inf')
        
        for cand in candidates:
            score = 0
            g = cand['geo']
            
            # 1. Screen bounds penalty
            if g.left() < 0: score += abs(g.left()) * 10
            if g.top() < 0: score += abs(g.top()) * 10
            if g.right() > p_w: score += (g.right() - p_w) * 10
            if g.bottom() > p_h: score += (g.bottom() - p_h) * 10
            
            # 2. Overlap penalty
            margin = 10  # stricter spacing
            g_inflated = g.adjusted(-margin, -margin, margin, margin)
            for sib in siblings:
                if g_inflated.intersects(sib.geometry()):
                    intersect = g_inflated.intersected(sib.geometry())
                    area = intersect.width() * intersect.height()
                    score += area * 5.0
            
            # 3. Preference penalty
            if cand['type'] in ['top', 'bottom']:
                score += 50
                
            if score < min_score:
                min_score = score
                best = cand
        
        if best:
            self.dot_local_pos = best['dot_local']
            self.text_rect = best['text_rect']
            self.text_align = best['align']
            self.setGeometry(best['geo'])
            self.update()

    def _create_candidate(self, p_type, dx, dy, tw, th, ds):
        pad = 5
        if p_type in ['top', 'bottom']:
            pad = 1  # Reduced padding for vertical layout

        if p_type == 'right':
            total_h = max(ds, th)
            w = ds + pad + tw
            h = total_h
            x = dx
            y = dy - (total_h - ds)//2
            dot_local = QPoint(0, (total_h - ds)//2)
            text_rect = QRect(ds + pad, 0, tw, total_h)
            align = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextWordWrap
            
        elif p_type == 'left':
            total_h = max(ds, th)
            w = tw + pad + ds
            h = total_h
            x = dx - tw - pad
            y = dy - (total_h - ds)//2
            dot_local = QPoint(tw + pad, (total_h - ds)//2)
            text_rect = QRect(0, 0, tw, total_h)
            align = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextWordWrap
            
        elif p_type == 'top':
            total_w = max(ds, tw)
            w = total_w
            h = th + pad + ds
            x = dx - (total_w - ds)//2
            y = dy - th - pad
            dot_local = QPoint((total_w - ds)//2, th + pad)
            text_rect = QRect(0, 0, total_w, th)
            align = Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom | Qt.TextFlag.TextWordWrap
            
        elif p_type == 'bottom':
            total_w = max(ds, tw)
            w = total_w
            h = ds + pad + th
            x = dx - (total_w - ds)//2
            y = dy
            dot_local = QPoint((total_w - ds)//2, 0)
            text_rect = QRect(0, ds + pad, total_w, th)
            align = Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap
            
        return {
            'type': p_type,
            'geo': QRect(int(x), int(y), int(w), int(h)),
            'dot_local': dot_local,
            'text_rect': text_rect,
            'align': align
        }

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

    def _resolve_dot_overlap(self, x, y, p_w, p_h):
        siblings = [c for c in self.parent().children() if isinstance(c, TaskDot) and c is not self and c.isVisible()]
        ds = UiConfig.DOT_SIZE
        min_dist = ds
        
        # Simple iterative solver to push away from overlapping dots
        for _ in range(5): # Try a few times to resolve
            moved = False
            for sib in siblings:
                sib_x = int(sib.task.x * p_w)
                sib_y = int(sib.task.y * p_h)
                
                dx = x - sib_x
                dy = y - sib_y
                dist_sq = dx*dx + dy*dy
                
                if dist_sq < min_dist*min_dist:
                    # Overlap detected
                    dist = (dist_sq)**0.5
                    if dist == 0:
                        dx = 1
                        dy = 0
                        dist = 1
                    
                    push = min_dist - dist + 1
                    push_x = (dx / dist) * push
                    push_y = (dy / dist) * push
                    
                    x += push_x
                    y += push_y
                    moved = True
            
            # Clamp to screen
            x = max(0, min(x, p_w - ds))
            y = max(0, min(y, p_h - ds))
            
            if not moved:
                break
                
        return int(x), int(y)

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
                
                # Resolve dot overlap
                new_x, new_y = self._resolve_dot_overlap(new_x, new_y, p_w, p_h)
                
                if new_x != curr_x or new_y != curr_y:
                    self.task.x = new_x / p_w
                    self.task.y = new_y / p_h
                    self.update_position()

            self.moved.emit()
            
        elif event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self)
