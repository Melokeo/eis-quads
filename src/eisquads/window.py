import json
import os
from PyQt6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, QEvent
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QApplication
from config import APP_WIDTH, APP_HEIGHT, TAB_SIZE, BG_COLOR, QUAD_LINES_COLOR, ACCENT_COLOR, DockSide
from style import STYLESHEET
from tab import DraggableTab
from matrix import MatrixCanvas

class SlideWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.dock_side = DockSide.RIGHT
        self.is_expanded = False
        self.drag_offset = QPoint() # Store the offset here

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                            Qt.WindowType.WindowStaysOnTopHint | 
                            Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Components
        self.tab = DraggableTab()
        self.tab.drag_started.connect(self.handle_drag_start) # Connect start
        self.tab.drag_moved.connect(self.handle_drag_move)
        self.tab.drag_ended.connect(self.handle_drag_end)
        self.tab.clicked.connect(self.toggle_slide)

        self.content = MatrixCanvas()
        self.content.setFixedSize(APP_WIDTH, APP_HEIGHT)
        self.content.setStyleSheet(f"background-color: {BG_COLOR}; border: 1px solid {QUAD_LINES_COLOR};")

        self.layout_container = QWidget(self)
        self.main_layout = QHBoxLayout(self.layout_container)
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(0)
        
        self.setStyleSheet(STYLESHEET)
        QApplication.instance().installEventFilter(self)
        
        self.load_state()
        self.snap_to_screen_edge()

    def handle_drag_start(self, global_pos):
        # Calculate where the mouse is relative to the window top-left
        self.drag_offset = global_pos - self.pos()

    def handle_drag_move(self, global_pos):
        # Move window to match mouse pos minus the initial offset
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
        # explicitly remove widgets from layout so they aren't destroyed
        # with the layout. setParent alone is not enough in pyqt6.
        if self.main_layout is not None:
            self.main_layout.removeWidget(self.tab)
            self.main_layout.removeWidget(self.content)
            self.tab.setParent(self.layout_container)
            self.content.setParent(self.layout_container)
        
        # safe to destroy the old layout now
        QWidget().setLayout(self.main_layout)
        
        radius_style = ""
        
        # recreate layout based on dock side
        if self.dock_side in [DockSide.LEFT, DockSide.RIGHT]:
            self.main_layout = QHBoxLayout(self.layout_container)
            self.tab.setFixedSize(TAB_SIZE, 60)
            
            if self.dock_side == DockSide.LEFT:
                radius_style = "border-top-left-radius: 0px; border-bottom-left-radius: 0px; border-top-right-radius: 10px; border-bottom-right-radius: 10px;"
            else: 
                radius_style = "border-top-left-radius: 10px; border-bottom-left-radius: 10px; border-top-right-radius: 0px; border-bottom-right-radius: 0px;"
                
        else:
            self.main_layout = QVBoxLayout(self.layout_container)
            self.tab.setFixedSize(60, TAB_SIZE)
            
            if self.dock_side == DockSide.TOP:
                radius_style = "border-top-left-radius: 0px; border-top-right-radius: 0px; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px;"
            else: 
                radius_style = "border-top-left-radius: 10px; border-top-right-radius: 10px; border-bottom-left-radius: 0px; border-bottom-right-radius: 0px;"

        self.tab.setStyleSheet(f"""
            QFrame {{
                background-color: {ACCENT_COLOR};
                {radius_style}
            }}
            QFrame:hover {{
                background-color: #b4befe;
            }}
        """)

        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(0)

        # re-add items to the new layout
        if self.dock_side == DockSide.LEFT:
            self.main_layout.addWidget(self.content)
            self.main_layout.addWidget(self.tab)
            self.main_layout.setAlignment(self.tab, Qt.AlignmentFlag.AlignVCenter)
        elif self.dock_side == DockSide.RIGHT:
            self.main_layout.addWidget(self.tab)
            self.main_layout.addWidget(self.content)
            self.main_layout.setAlignment(self.tab, Qt.AlignmentFlag.AlignVCenter)
        elif self.dock_side == DockSide.TOP:
            self.main_layout.addWidget(self.content)
            self.main_layout.addWidget(self.tab)
            self.main_layout.setAlignment(self.tab, Qt.AlignmentFlag.AlignHCenter)
        elif self.dock_side == DockSide.BOTTOM:
            self.main_layout.addWidget(self.tab)
            self.main_layout.addWidget(self.content)
            self.main_layout.setAlignment(self.tab, Qt.AlignmentFlag.AlignHCenter)

        if self.dock_side in [DockSide.LEFT, DockSide.RIGHT]:
            self.resize(APP_WIDTH + TAB_SIZE, APP_HEIGHT)
            self.layout_container.resize(APP_WIDTH + TAB_SIZE, APP_HEIGHT)
        else:
            self.resize(APP_WIDTH, APP_HEIGHT + TAB_SIZE)
            self.layout_container.resize(APP_WIDTH, APP_HEIGHT + TAB_SIZE)

    def load_state(self):
        try:
            if os.path.exists("window_state.json"):
                with open("window_state.json", "r") as f:
                    data = json.load(f)
                    self.move(data.get("x", 100), data.get("y", 100))
        except Exception:
            pass

    def get_hidden_pos(self, s_geo):
        if self.dock_side == DockSide.LEFT:
            # Window at left edge. Content is left of Tab.
            # Shown: Content visible at 0. Tab at APP_WIDTH.
            # Hidden: Content at -APP_WIDTH. Tab at 0.
            # Position of Window top-left:
            return QPoint(s_geo.left() - APP_WIDTH, max(s_geo.top(), min(self.y(), s_geo.bottom() - APP_HEIGHT)))
        
        elif self.dock_side == DockSide.RIGHT:
            # Window at right edge. Tab | Content.
            # Hidden: Window at ScreenRight - TAB.
            return QPoint(s_geo.right() - TAB_SIZE, max(s_geo.top(), min(self.y(), s_geo.bottom() - APP_HEIGHT)))
            
        elif self.dock_side == DockSide.TOP:
            # Top edge. Content / Tab.
            # Hidden: Window Top at -APP_HEIGHT.
            return QPoint(max(s_geo.left(), min(self.x(), s_geo.right() - APP_WIDTH)), s_geo.top() - APP_HEIGHT)
            
        elif self.dock_side == DockSide.BOTTOM:
            # Bottom edge. Tab / Content.
            # Hidden: Window Top at ScreenBottom - TAB.
            return QPoint(max(s_geo.left(), min(self.x(), s_geo.right() - APP_WIDTH)), s_geo.bottom() - TAB_SIZE)

    def get_shown_pos(self, s_geo):
        current = self.get_hidden_pos(s_geo) # Use current 'orthagonal' coord
        
        if self.dock_side == DockSide.LEFT:
            return QPoint(s_geo.left(), current.y())
        elif self.dock_side == DockSide.RIGHT:
            return QPoint(s_geo.right() - (APP_WIDTH + TAB_SIZE), current.y())
        elif self.dock_side == DockSide.TOP:
            return QPoint(current.x(), s_geo.top())
        elif self.dock_side == DockSide.BOTTOM:
            return QPoint(current.x(), s_geo.bottom() - (APP_HEIGHT + TAB_SIZE))

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
            self.toggle_slide()
            return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            QApplication.instance().quit()

    def closeEvent(self, event):
        # save current position before closing
        with open("window_state.json", "w") as f:
            json.dump({"x": self.x(), "y": self.y()}, f)
        super().closeEvent(event)
