from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QBrush, QFont, QFontMetrics
from PyQt6.QtWidgets import QWidget
from config import UiConfig
from models import Task

class TaskDot(QWidget):
    moved = pyqtSignal()
    clicked = pyqtSignal(object)
    link_started = pyqtSignal(object)
    link_dragging = pyqtSignal(QPoint)
    link_ended = pyqtSignal(QPoint)
    drag_started = pyqtSignal(str) # emits task id
    drag_ended = pyqtSignal()

    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self.task = task
        self.dragging = False
        self.linking = False
        self.drag_start_global = QPoint()
        self.drag_start_dot_pos = QPoint()
        self.dot_local_pos = QPoint(0, 0)
        self.text_rect = QRect()
        self.text_align = Qt.AlignmentFlag.AlignLeft
        self.current_pos_type = 'right'
        self.update_position()
        self.show()

    def update_position(self):
        if not self.parent(): return
        
        p_w = self.parent().width()
        p_h = self.parent().height()
        
        # dot position (top-left of the dot itself)
        dot_x = int(self.task.x * p_w)
        dot_y = int(self.task.y * p_h)
        
        ds = UiConfig.DOT_SIZE
        # clamp dot to screen, lest it escapes into the void
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
        # generate candidates including aligned vertical ones
        for p_type in ['right', 'left', 'top-center', 'top-left', 'top-right', 'bottom-center', 'bottom-left', 'bottom-right']:
            candidates.append(self._create_candidate(p_type, dot_x, dot_y, text_w, text_h, ds))

        best = None
        min_score = float('inf')
        
        cx = p_w // 2
        cy = p_h // 2
        
        # determine dot quadrant (based on center)
        dot_cx = dot_x + ds // 2
        dot_cy = dot_y + ds // 2
        is_left = dot_cx < cx
        is_top = dot_cy < cy
        
        # define quadrant boundaries
        q_left = 0 if is_left else cx
        q_right = cx if is_left else p_w
        q_top = 0 if is_top else cy
        q_bottom = cy if is_top else p_h
        
        quadrant_rect = QRect(q_left, q_top, q_right - q_left, q_bottom - q_top)
        
        for cand in candidates:
            score = 0
            conflict_score = 0
            g = cand['geo']
            
            # 1. screen bounds penalty
            if g.left() < 0: conflict_score += abs(g.left()) * 10
            if g.top() < 0: conflict_score += abs(g.top()) * 10
            if g.right() > p_w: conflict_score += (g.right() - p_w) * 10
            if g.bottom() > p_h: conflict_score += (g.bottom() - p_h) * 10
            
            # 2. overlap penalty
            margin = 10  # stricter spacing
            g_inflated = g.adjusted(-margin, -margin, margin, margin)
            for sib in siblings:
                if g_inflated.intersects(sib.geometry()):
                    intersect = g_inflated.intersected(sib.geometry())
                    area = intersect.width() * intersect.height()
                    conflict_score += area * 5.0
            
            # 4. axis crossing penalty (strict quadrant enforcement)
            # check if candidate is fully contained within the quadrant
            if not quadrant_rect.contains(g):
                conflict_score += 10000 # massive penalty, do not cross the streams
            
            score += conflict_score

            # 3. preference penalty
            # we prefer side labels, top/bottom are a last resort
            if 'top' in cand['type'] or 'bottom' in cand['type']:
                score += 50
                # prefer centered if vertical
                if 'center' not in cand['type']:
                    score += 5
            
            # Hysteresis: stick to current if no conflict
            if cand['type'] == self.current_pos_type and conflict_score == 0:
                score -= 60

            if score < min_score:
                min_score = score
                best = cand
        
        if best:
            self.current_pos_type = best['type']
            self.dot_local_pos = best['dot_local']
            self.text_rect = best['text_rect']
            self.text_align = best['align']
            self.setGeometry(best['geo'])
            self.update()

    def _create_candidate(self, p_type, dx, dy, tw, th, ds):
        pad = 5
        if 'top' in p_type or 'bottom' in p_type:
            pad = 1

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
            
        elif 'top' in p_type:
            total_w = max(ds, tw)
            w = total_w
            h = th + pad + ds
            y = dy - th - pad
            
            if 'left' in p_type: # aligned left (expands right)
                x = dx
                dot_local = QPoint(0, th + pad)
                align = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom | Qt.TextFlag.TextWordWrap
            elif 'right' in p_type: # aligned right (expands left)
                x = dx + ds - total_w
                dot_local = QPoint(total_w - ds, th + pad)
                align = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom | Qt.TextFlag.TextWordWrap
            else: # center
                x = dx - (total_w - ds)//2
                dot_local = QPoint((total_w - ds)//2, th + pad)
                align = Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom | Qt.TextFlag.TextWordWrap
                
            text_rect = QRect(0, 0, total_w, th)
            
        elif 'bottom' in p_type:
            total_w = max(ds, tw)
            w = total_w
            h = ds + pad + th
            y = dy
            
            if 'left' in p_type: # aligned left (expands right)
                x = dx
                dot_local = QPoint(0, 0)
                align = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap
            elif 'right' in p_type: # aligned right (expands left)
                x = dx + ds - total_w
                dot_local = QPoint(total_w - ds, 0)
                align = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap
            else: # center
                x = dx - (total_w - ds)//2
                dot_local = QPoint((total_w - ds)//2, 0)
                align = Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap
                
            text_rect = QRect(0, ds + pad, total_w, th)
            
        return {
            'type': p_type,
            'geo': QRect(int(x), int(y), int(w), int(h)),
            'dot_local': dot_local,
            'text_rect': text_rect,
            'align': align
        }

    def get_color(self):
        if self.task.completed:
            return "#45475a" # completed tasks fade into obscurity

        # determine quadrant
        
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
        if self.task.completed:
            font.setStrikeOut(True)
            painter.setPen(QColor("#6c7086")) # dim text for completed
        painter.setFont(font)
        label = self.task.title
        
        painter.drawText(self.text_rect, 
                         self.text_align, 
                         label)

    def mouseDoubleClickEvent(self, event):
        if self.parent() and getattr(self.parent(), 'bg_adjusting', False):
            return

        if event.button() == Qt.MouseButton.LeftButton:
            if self.parent():
                self.parent().push_undo('complete')
            self.task.completed = not self.task.completed
            self.update()
            self.moved.emit()

    def mousePressEvent(self, event):
        if self.parent() and (getattr(self.parent(), 'locked', False) or getattr(self.parent(), 'bg_adjusting', False)):
            return

        if event.button() == Qt.MouseButton.MiddleButton:
            self.linking = True
            self.link_started.emit(self)
        elif event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_start_global = event.globalPosition().toPoint()
            self.drag_started.emit(self.task.id)
            
            if self.parent():
                p_w, p_h = self.parent().width(), self.parent().height()
                self.drag_start_dot_pos = QPoint(int(self.task.x * p_w), int(self.task.y * p_h))
            
            self.raise_()

    def mouseMoveEvent(self, event):
        if self.linking:
            self.link_dragging.emit(event.globalPosition().toPoint())
            return

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
                    # overlap detected
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
            
            # clamp to screen
            x = max(0, min(x, p_w - ds))
            y = max(0, min(y, p_h - ds))
            
            if not moved:
                break
                
        return int(x), int(y)

    def mouseReleaseEvent(self, event):
        if self.linking:
            self.linking = False
            self.link_ended.emit(event.globalPosition().toPoint())
            return

        if self.dragging:
            self.dragging = False
            self.drag_ended.emit()
            
            if self.parent():
                p_w, p_h = self.parent().width(), self.parent().height()
                axis_x, axis_y = p_w // 2, p_h // 2
                
                # use dot position from task
                curr_x = int(self.task.x * p_w)
                curr_y = int(self.task.y * p_h)
                
                new_x = self._resolve_overlap(curr_x, axis_x, UiConfig.DOT_SIZE)
                new_y = self._resolve_overlap(curr_y, axis_y, UiConfig.DOT_SIZE)
                
                # resolve dot overlap
                new_x, new_y = self._resolve_dot_overlap(new_x, new_y, p_w, p_h)
                
                if new_x != curr_x or new_y != curr_y:
                    self.task.x = new_x / p_w
                    self.task.y = new_y / p_h
                    self.update_position()

            self.moved.emit()
            
        elif event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self)

    def get_dot_center(self):
        ds = UiConfig.DOT_SIZE
        center_local = self.dot_local_pos + QPoint(ds // 2, ds // 2)
        return self.pos() + center_local
