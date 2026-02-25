import math
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QMessageBox
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Signal

class PoseRecordPanel(QWidget):
    """
    位置记录面板。
    包含了连续轨迹记录（导出为 Excel）和单点打卡（ListWidget）的功能。
    采用了和 TeleopPanel 一样的 Apple Maps 风格丝滑抽屉设计。
    """
    
    height_changed = Signal(int)
    
    # 向外发出的意图信号
    sig_start_trace = Signal()
    sig_stop_trace = Signal()
    sig_record_point = Signal()
    sig_go_to_selected = Signal(float, float, float) # (x, y, yaw)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "PanelWidget")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedWidth(240)
        
        self._is_expanded = False # 默认折叠
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 1. 抽屉把手 Header
        self.header_btn = QPushButton("POSE RECORDER   ▲")
        self.header_btn.setCursor(Qt.PointingHandCursor)
        self.header_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #858585;
                font-weight: bold;
                letter-spacing: 1px;
                text-align: left;
                padding: 15px;
            }
            QPushButton:hover {
                color: #ffffff;
                background: rgba(255, 255, 255, 0.05);
            }
        """)
        self.header_btn.clicked.connect(self.toggle_drawer)
        self.main_layout.addWidget(self.header_btn)
        
        # 2. 内容区
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(15, 0, 15, 15)
        content_layout.setSpacing(10)
        
        # --- 连续轨迹记录 ---
        trace_label = QLabel("轨迹跟踪连录")
        trace_label.setStyleSheet("color: #d4d4d4; font-size: 13px; margin-top: 5px;")
        content_layout.addWidget(trace_label)
        
        trace_action_layout = QHBoxLayout()
        self.btn_start_trace = QPushButton("开始连录")
        self.btn_start_trace.setProperty("class", "PrimaryAction")
        self.btn_start_trace.clicked.connect(self.sig_start_trace.emit)
        
        self.btn_stop_trace = QPushButton("停止并保存")
        self.btn_stop_trace.setProperty("class", "DangerAction")
        self.btn_stop_trace.setEnabled(False)
        self.btn_stop_trace.clicked.connect(self.sig_stop_trace.emit)
        
        trace_action_layout.addWidget(self.btn_start_trace)
        trace_action_layout.addWidget(self.btn_stop_trace)
        content_layout.addLayout(trace_action_layout)
        
        # --- 单点打卡记录 ---
        point_label = QLabel("单点位姿记录")
        point_label.setStyleSheet("color: #d4d4d4; font-size: 13px; margin-top: 10px;")
        content_layout.addWidget(point_label)
        
        self.btn_record_point = QPushButton("打卡当前位姿")
        self.btn_record_point.clicked.connect(self.sig_record_point.emit)
        content_layout.addWidget(self.btn_record_point)
        
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                padding: 2px;
            }
            QListWidget::item:selected {
                background-color: #007acc;
                color: white;
            }
        """)
        self.list_widget.setFixedHeight(120)
        content_layout.addWidget(self.list_widget)
        
        list_action_layout = QHBoxLayout()
        self.btn_go_to = QPushButton("前往选中点")
        self.btn_go_to.clicked.connect(self._on_go_to)
        
        self.btn_delete = QPushButton("删除选中")
        self.btn_delete.clicked.connect(self._on_delete)
        
        list_action_layout.addWidget(self.btn_go_to)
        list_action_layout.addWidget(self.btn_delete)
        content_layout.addLayout(list_action_layout)
        
        self.main_layout.addWidget(self.content_widget)
        
        # 动画机制
        self.animation = QPropertyAnimation(self.content_widget, b"maximumHeight")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.InOutQuart)
        self.animation.valueChanged.connect(self._on_animation_step)
        
        self.content_widget.setMaximumHeight(0)

    def toggle_drawer(self):
        self._is_expanded = not self._is_expanded
        target_height = self.content_widget.sizeHint().height() if self._is_expanded else 0
        current_height = self.content_widget.maximumHeight()
        
        self.animation.setStartValue(current_height)
        self.animation.setEndValue(target_height)
        self.animation.start()
        
        self.header_btn.setText("POSE RECORDER   ▼" if self._is_expanded else "POSE RECORDER   ▲")
        
    def _on_animation_step(self, value):
        self.adjustSize()
        self.height_changed.emit(self.height())
        
    def _on_delete(self):
        items = self.list_widget.selectedItems()
        if not items: return
        for item in items:
            self.list_widget.takeItem(self.list_widget.row(item))
            
    def _on_go_to(self):
        items = self.list_widget.selectedItems()
        if not items: return
        # 格式解析：例如 "[08:12:33] X:1.20 Y:3.40 Yaw:0.50"
        text = items[0].text()
        try:
            parts = text.split(" ")
            x = float(parts[1].split(":")[1])
            y = float(parts[2].split(":")[1])
            yaw = float(parts[3].split(":")[1])
            self.sig_go_to_selected.emit(x, y, yaw)
        except Exception:
            pass
            
    def set_trace_active(self, active: bool):
        self.btn_start_trace.setEnabled(not active)
        self.btn_stop_trace.setEnabled(active)
        
    def add_point(self, x: float, y: float, yaw: float):
        import time
        t_str = time.strftime("%H:%M:%S")
        record_str = f"[{t_str}] X:{x:.2f} Y:{y:.2f} Yaw:{yaw:.2f}"
        self.list_widget.addItem(record_str)
        self.list_widget.scrollToBottom()
