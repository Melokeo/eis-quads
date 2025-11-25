import json
import os
import shutil
from pathlib import Path
from PyQt6.QtCore import Qt, QPoint, QPointF, QPropertyAnimation, QEasingCurve, QEvent
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QApplication, QFileDialog
from config import UiConfig, STYLESHEET, DockSide, get_storage_dir
from tab import DraggableTab
from matrix import MatrixCanvas
from models import TaskManager

class SlideWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.dock_side = DockSide.RIGHT
        self.is_expanded = False
        self.drag_offset = QPoint() 
        self.key_buffer = ""
        self.should_save = True
        self.ignore_deactivation = False

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                            Qt.WindowType.WindowStaysOnTopHint | 
                            Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # components
        self.tab = DraggableTab()
        self.tab.drag_started.connect(self.handle_drag_start) 
        self.tab.drag_moved.connect(self.handle_drag_move)
        self.tab.drag_ended.connect(self.handle_drag_end)
        self.tab.clicked.connect(self.toggle_slide)

        self.content = MatrixCanvas()
        self.content.setFixedSize(UiConfig.APP_WIDTH, UiConfig.APP_HEIGHT)
        self.content.setStyleSheet(f"background-color: {UiConfig.BG_COLOR}; border: 1px solid {UiConfig.QUAD_LINES_COLOR};")

        self.layout_container = QWidget(self)
        self.layout_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.main_layout = QHBoxLayout(self.layout_container)
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(0)
        
        self.setStyleSheet(STYLESHEET)
        QApplication.instance().installEventFilter(self)
        
        self.load_state()
        self.snap_to_screen_edge()
        TaskManager.create_backup()

    def handle_drag_start(self, global_pos):
        # calculate where the mouse is relative to the window top-left
        self.drag_offset = global_pos - self.pos()

    def handle_drag_move(self, global_pos):
        # move window to match mouse pos minus the initial offset
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
        if self.main_layout is not None:
            self.main_layout.removeWidget(self.tab)
            self.main_layout.removeWidget(self.content)
            self.tab.setParent(self.layout_container)
            self.content.setParent(self.layout_container)
            QWidget().setLayout(self.main_layout) # destroy old layout
        
        is_vertical = self.dock_side in [DockSide.LEFT, DockSide.RIGHT]
        
        if is_vertical:
            self.main_layout = QHBoxLayout(self.layout_container)
            self.tab.setFixedSize(UiConfig.TAB_SIZE, 60)
            align = Qt.AlignmentFlag.AlignVCenter
            size = (UiConfig.APP_WIDTH + UiConfig.TAB_SIZE, UiConfig.APP_HEIGHT)
        else:
            self.main_layout = QVBoxLayout(self.layout_container)
            self.tab.setFixedSize(60, UiConfig.TAB_SIZE)
            align = Qt.AlignmentFlag.AlignHCenter
            size = (UiConfig.APP_WIDTH, UiConfig.APP_HEIGHT + UiConfig.TAB_SIZE)

        ttl = ttr = tbl = tbr = 0
        
        if self.dock_side == DockSide.LEFT:   
            ttr = tbr = 10
        elif self.dock_side == DockSide.RIGHT: 
            ttl = tbl = 10
        elif self.dock_side == DockSide.TOP:   
            tbl = tbr = 10
        elif self.dock_side == DockSide.BOTTOM: 
            ttl = ttr = 10

        tab_radius_style = content_radius_style = (f"border-top-left-radius: {ttl}px; border-top-right-radius: {ttr}px; "
                            f"border-bottom-left-radius: {tbl}px; border-bottom-right-radius: {tbr}px;")

        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.tab.setStyleSheet(f"""
            QFrame {{
                background-color: {UiConfig.TAB_COLOR};
                {tab_radius_style}
            }}
            QFrame:hover {{
                background-color: #aedabf;
            }}
        """)
        
        self.content.setStyleSheet(f"background-color: {UiConfig.BG_COLOR}; border: 1px solid {UiConfig.QUAD_LINES_COLOR}; {content_radius_style}")
        self.content.set_radii(ttl, ttr, tbl, tbr)

        # determine widget order: content first for Left/Top, tab first for Right/Bottom
        widgets = [self.content, self.tab] if self.dock_side in [DockSide.LEFT, DockSide.TOP] else [self.tab, self.content]
        for w in widgets:
            self.main_layout.addWidget(w)
            
        self.main_layout.setAlignment(self.tab, align)
        
        self.resize(*size)
        self.layout_container.resize(*size)
            
    def get_state_path(self):
        return get_storage_dir() / "window_state.json"

    def load_state(self):
        try:
            path = self.get_state_path()
            if path.exists():
                with open(path, "r") as f:
                    data = json.load(f)
                    self.move(data.get("x", 100), data.get("y", 100))
                    
                    # load background state
                    bg_image = data.get("bg_image")
                    if bg_image and os.path.exists(bg_image):
                        self.content.set_background(bg_image)
                        self.content.bg_offset = QPointF(data.get("bg_x", 0), data.get("bg_y", 0))
                        self.content.bg_scale = data.get("bg_scale", 1.0)
                        self.content.bg_opacity = data.get("bg_opacity", 0.3)
        except Exception:
            pass

    def get_hidden_pos(self, s_geo):
        # clamp current position to screen bounds for the orthogonal axis
        clamped_x = max(s_geo.left(), min(self.x(), s_geo.right() - UiConfig.APP_WIDTH))
        clamped_y = max(s_geo.top(), min(self.y(), s_geo.bottom() - UiConfig.APP_HEIGHT))
        
        if self.dock_side == DockSide.LEFT:
            return QPoint(s_geo.left() - UiConfig.APP_WIDTH, clamped_y)
        elif self.dock_side == DockSide.RIGHT:
            return QPoint(s_geo.right() - UiConfig.TAB_SIZE, clamped_y)
        elif self.dock_side == DockSide.TOP:
            return QPoint(clamped_x, s_geo.top() - UiConfig.APP_HEIGHT)
        elif self.dock_side == DockSide.BOTTOM:
            return QPoint(clamped_x, s_geo.bottom() - UiConfig.TAB_SIZE)

    def get_shown_pos(self, s_geo):
        current = self.get_hidden_pos(s_geo) # Use current 'orthagonal' coord
        
        if self.dock_side == DockSide.LEFT:
            return QPoint(s_geo.left(), current.y())
        elif self.dock_side == DockSide.RIGHT:
            return QPoint(s_geo.right() - (UiConfig.APP_WIDTH + UiConfig.TAB_SIZE), current.y())
        elif self.dock_side == DockSide.TOP:
            return QPoint(current.x(), s_geo.top())
        elif self.dock_side == DockSide.BOTTOM:
            return QPoint(current.x(), s_geo.bottom() - (UiConfig.APP_HEIGHT + UiConfig.TAB_SIZE))
        
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
            if not self.ignore_deactivation:
                self.toggle_slide()
            return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            QApplication.instance().quit()
            return
        
        # Consume Alt key to prevent system menu interference during scrolling
        if event.key() == Qt.Key.Key_Alt:
            event.accept()
            return
        
        if event.key() == Qt.Key.Key_F5:
            self.content.reload_tasks()
            return

        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if self.content.bg_adjusting:
                self.content.bg_adjusting = False
                self.content.update()
                return

        # Undo/Redo shortcuts
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_Y:
                self.content.redo()
                return
            elif event.key() == Qt.Key.Key_Z:
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    self.content.redo()
                else:
                    self.content.undo()
                return

        text = event.text()
        if text:
            self.key_buffer += text
            # keep buffer manageable, we only need the tail
            if len(self.key_buffer) > 10:
                self.key_buffer = self.key_buffer[-10:]
            
            if self.key_buffer.endswith("clr"):
                self.content.clear_all_tasks()
                self.key_buffer = ""
            elif self.key_buffer.endswith("exit"):
                QApplication.instance().quit()
            elif self.key_buffer.endswith("lock"):
                self.content.set_locked(True)
                self.key_buffer = ""
            elif self.key_buffer.endswith("free"):
                self.content.set_locked(False)
                self.key_buffer = ""
            elif self.key_buffer.endswith("reload"):
                self.content.reload_tasks()
                self.key_buffer = ""
            elif self.key_buffer.endswith("undo"):
                self.content.undo()
                self.key_buffer = ""
            elif self.key_buffer.endswith("redo"):
                self.content.redo()
                self.key_buffer = ""
            elif self.key_buffer.endswith("nosave"):
                self.should_save = False
                TaskManager.restore_backup()
                QApplication.instance().quit()
            elif self.key_buffer.endswith("recover"):
                TaskManager.restore_backup()
                self.content.reload_tasks()
                self.key_buffer = ""
            elif self.key_buffer.endswith("bg"):
                self.ignore_deactivation = True
                file_path, _ = QFileDialog.getOpenFileName(self, "Select Background", "", "Images (*.png *.jpg *.jpeg *.bmp)")
                self.ignore_deactivation = False
                self.activateWindow()
                self.content.setFocus()
                
                if file_path:
                    try:
                        storage_dir = get_storage_dir()
                        ext = os.path.splitext(file_path)[1]
                        dest_path = storage_dir / f"background{ext}"
                        shutil.copy2(file_path, dest_path)
                        self.content.set_background(str(dest_path))
                        self.content.bg_adjusting = True
                    except Exception:
                        pass
                self.key_buffer = ""

    def closeEvent(self, event):
        # save current position before closing
        if self.should_save:
            try:
                state = {
                    "x": self.x(), 
                    "y": self.y(),
                    "bg_image": self.content.bg_path,
                    "bg_x": int(self.content.bg_offset.x()),
                    "bg_y": int(self.content.bg_offset.y()),
                    "bg_scale": self.content.bg_scale,
                    "bg_opacity": self.content.bg_opacity
                }
                with open(self.get_state_path(), "w") as f:
                    json.dump(state, f, indent=4)
            except Exception:
                pass
        super().closeEvent(event)
