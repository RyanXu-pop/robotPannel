from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class TelemetryPanel(QWidget):
    """
    悬浮遥测展板 (Telemetry Dashboard)
    显示机器人的关键健康信息：连接状态、电压、坐标。
    独立且通过 Store 单向更新。
    """
    def __init__(self, store, parent=None):
        super().__init__(parent)
        self.store = store
        
        # 赋予全局通用卡片样式
        self.setProperty("class", "PanelWidget")
        # 允许自身 QSS 画背景
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        self.setup_ui()
        self.bind_store()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # 1. 标题模块
        title_label = QLabel("ROBOT TELEMETRY")
        title_font = QFont("Segoe UI", 10, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #858585; letter-spacing: 2px;")
        layout.addWidget(title_label)
        
        # 2. 连接状态区
        status_layout = QHBoxLayout()
        self.indicator_circle = QLabel("●")
        self.indicator_circle.setStyleSheet("color: #f14c4c; font-size: 16px;") # 默认红色
        self.status_label = QLabel("连接断开")
        self.status_label.setStyleSheet("color: #d4d4d4; font-size: 14px; font-weight: bold;")
        
        status_layout.addWidget(self.indicator_circle)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        # 3. 电压数据区
        volt_layout = QHBoxLayout()
        volt_icon = QLabel("⚡")
        volt_icon.setStyleSheet("color: #d29922; font-size: 16px;")
        self.volt_label = QLabel("N/A")
        self.volt_label.setStyleSheet("color: #d4d4d4; font-size: 14px;")
        
        volt_layout.addWidget(volt_icon)
        volt_layout.addWidget(self.volt_label)
        volt_layout.addStretch()
        layout.addLayout(volt_layout)
        
        # 3b. 电池进度条
        self.battery_bar = QProgressBar()
        self.battery_bar.setRange(0, 100)
        self.battery_bar.setValue(0)
        self.battery_bar.setTextVisible(False)
        self.battery_bar.setFixedHeight(6)
        self.battery_bar.setStyleSheet("""
            QProgressBar { background: #2d2d30; border: none; border-radius: 3px; }
            QProgressBar::chunk { background: #3fb950; border-radius: 3px; }
        """)
        layout.addWidget(self.battery_bar)
        
        # 4. 坐标区
        coord_layout = QHBoxLayout()
        coord_icon = QLabel("📍")
        coord_icon.setStyleSheet("color: #007acc; font-size: 16px;")
        self.coord_label = QLabel("X: 0.00  Y: 0.00  θ: 0°")
        self.coord_label.setStyleSheet("color: #d4d4d4; font-size: 13px; font-family: monospace;")
        
        coord_layout.addWidget(coord_icon)
        coord_layout.addWidget(self.coord_label)
        coord_layout.addStretch()
        layout.addLayout(coord_layout)
        
        # 设置自身固定宽度
        self.setFixedWidth(240)

    def bind_store(self):
        """将 UI 连接到统一 Store"""
        self.store.chassis_alive_changed.connect(self._on_chassis_status)
        self.store.voltage_changed.connect(self._on_voltage_changed)
        self.store.robot_pose_changed.connect(self._on_pose_changed)

    def _on_chassis_status(self, is_alive: bool):
        if is_alive:
            self.indicator_circle.setStyleSheet("color: #3fb950; font-size: 16px;")
            self.status_label.setText("底盘在线")
        else:
            self.indicator_circle.setStyleSheet("color: #f14c4c; font-size: 16px;")
            self.status_label.setText("底盘离线")
            # 移除这里的 self.volt_label.setText("N/A")，让电压显示和底盘在线状态解耦
            # 因为即使底盘程序判断"不在线"(未收到 odom)，仍可能会有电压数据到来

    def _on_voltage_changed(self, voltage: float, percent: float):
        color = "#3fb950" if voltage >= 24.0 else ("#f14c4c" if voltage <= 20.0 else "#d29922")
        self.volt_label.setText(f"{voltage:.2f} V ({int(percent)}%)")
        self.volt_label.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold;")
        self.battery_bar.setValue(int(percent))
        # 进度条颜色跟随电压警告
        chunk_color = color
        self.battery_bar.setStyleSheet(f"""
            QProgressBar {{ background: #2d2d30; border: none; border-radius: 3px; }}
            QProgressBar::chunk {{ background: {chunk_color}; border-radius: 3px; }}
        """)

    def _on_pose_changed(self, pose):
        import math
        deg = math.degrees(pose.angle)
        z = getattr(pose, 'z', 0.0)
        self.coord_label.setText(f"X:{pose.x:5.2f} Y:{pose.y:5.2f} Z:{z:5.2f} θ:{deg:4.0f}°")
