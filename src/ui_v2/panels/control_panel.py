from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QMessageBox, QDialog, QLineEdit
from PySide6.QtCore import Qt, Signal
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.manual_pose_dialog import ManualPoseDialog

class ControlPanel(QWidget):
    """
    工作流控制面板 (Workflow Control Panel)
    用于启停 建图(SLAM) 和 导航(Navigation)，并提供保存地图的功能。
    设计要求：按钮具有清晰的主次级和互斥禁用层级。
    """
    
    # 向外抛出的控制信号
    sig_start_mapping = Signal()
    sig_stop_mapping = Signal()
    sig_save_map = Signal()
    
    sig_start_navigation = Signal()
    sig_stop_navigation = Signal()
    
    sig_set_initial_pose = Signal()
    sig_set_goal_pose = Signal()
    
    # 携带直接输入坐标的信号
    sig_manual_initial_pose = Signal(float, float, float)
    sig_manual_goal = Signal(float, float, float)
    
    # SSH 系统操作信号
    sig_start_chassis = Signal()
    sig_start_mqtt_node = Signal()
    
    # 地图管理信号
    sig_download_map = Signal()
    sig_upload_map = Signal()
    
    # 初始位姿保存/恢复信号
    sig_save_initial_pose = Signal()
    sig_recall_initial_pose = Signal()

    def __init__(self, store, parent=None):
        super().__init__(parent)
        self.store = store
        self.setProperty("class", "PanelWidget")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedWidth(240)
        
        self.setup_ui()
        self.bind_store()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        title_label = QLabel("WORKFLOW")
        title_label.setStyleSheet("color: #858585; font-weight: bold; letter-spacing: 1px;")
        layout.addWidget(title_label)

        # ---------- 1. 建图组 ----------
        map_label = QLabel("建图 SLAM")
        map_label.setStyleSheet("color: #d4d4d4; font-size: 13px; margin-top: 5px;")
        layout.addWidget(map_label)
        
        self.btn_toggle_mapping = QPushButton("启动建图")
        self.btn_toggle_mapping.setProperty("class", "PrimaryAction")
        self.btn_toggle_mapping.clicked.connect(self._on_mapping_clicked)
        layout.addWidget(self.btn_toggle_mapping)
        
        self.btn_save_map = QPushButton("保存地图 (至机器人)")
        self.btn_save_map.clicked.connect(self.sig_save_map.emit)
        self.btn_save_map.setEnabled(False) # 默认禁用
        layout.addWidget(self.btn_save_map)

        # ---------- 2. 导航组 ----------
        nav_label = QLabel("导航 Navigation2")
        nav_label.setStyleSheet("color: #d4d4d4; font-size: 13px; margin-top: 10px;")
        layout.addWidget(nav_label)
        
        self.btn_toggle_navigation = QPushButton("启动导航")
        self.btn_toggle_navigation.setProperty("class", "PrimaryAction")
        self.btn_toggle_navigation.clicked.connect(self._on_navigation_clicked)
        layout.addWidget(self.btn_toggle_navigation)
        
        # 导航交互子菜单 (横向)
        nav_action_layout = QHBoxLayout()
        nav_action_layout.setSpacing(8)
        
        self.btn_initial_pose = QPushButton("设置位姿")
        self.btn_initial_pose.clicked.connect(self.sig_set_initial_pose.emit)
        self.btn_initial_pose.setEnabled(False)
        self.btn_initial_pose.setToolTip("在地图上点击并拖拽以设定小车的初始位姿")
        
        self.btn_goal_pose = QPushButton("发送目标")
        self.btn_goal_pose.clicked.connect(self.sig_set_goal_pose.emit)
        self.btn_goal_pose.setEnabled(False)
        self.btn_goal_pose.setToolTip("在地图上点击并拖拽以设定导航目标")
        
        nav_action_layout.addWidget(self.btn_initial_pose)
        nav_action_layout.addWidget(self.btn_goal_pose)
        layout.addLayout(nav_action_layout)

        # 手动输入坐标子菜单 (第二排)
        manual_action_layout = QHBoxLayout()
        manual_action_layout.setSpacing(8)
        
        self.btn_manual_initial = QPushButton("手动初位")
        self.btn_manual_initial.clicked.connect(self._on_manual_initial)
        self.btn_manual_initial.setEnabled(False)
        self.btn_manual_initial.setToolTip("手动输入详细的 X, Y, Yaw 小车初始位姿")
        
        self.btn_manual_goal = QPushButton("手动目标")
        self.btn_manual_goal.clicked.connect(self._on_manual_goal)
        self.btn_manual_goal.setEnabled(False)
        self.btn_manual_goal.setToolTip("手动输入详细的 X, Y, Yaw 目标点")
        
        manual_action_layout.addWidget(self.btn_manual_initial)
        manual_action_layout.addWidget(self.btn_manual_goal)
        layout.addLayout(manual_action_layout)

        # 位姿保存/恢复
        pose_save_layout = QHBoxLayout()
        pose_save_layout.setSpacing(8)
        
        self.btn_save_pose = QPushButton("保存位姿")
        self.btn_save_pose.setToolTip("保存当前初始位姿到文件")
        self.btn_save_pose.setEnabled(False)
        self.btn_save_pose.clicked.connect(self.sig_save_initial_pose.emit)
        
        self.btn_recall_pose = QPushButton("恢复位姿")
        self.btn_recall_pose.setToolTip("从文件恢复上次保存的初始位姿")
        self.btn_recall_pose.setEnabled(False)
        self.btn_recall_pose.clicked.connect(self.sig_recall_initial_pose.emit)
        
        pose_save_layout.addWidget(self.btn_save_pose)
        pose_save_layout.addWidget(self.btn_recall_pose)
        layout.addLayout(pose_save_layout)

        # ---------- 3. 地图管理组 ----------
        map_mgr_label = QLabel("地图管理")
        map_mgr_label.setStyleSheet("color: #d4d4d4; font-size: 13px; margin-top: 10px;")
        layout.addWidget(map_mgr_label)
        
        # 地图名称输入
        map_name_layout = QHBoxLayout()
        map_name_layout.setSpacing(8)
        self.input_map_name = QLineEdit("my_map")
        self.input_map_name.setPlaceholderText("地图名称")
        self.input_map_name.setStyleSheet("background: #2d2d30; color: #d4d4d4; border: 1px solid #3e3e42; border-radius: 4px; padding: 4px 8px;")
        map_name_layout.addWidget(QLabel("名称:"))
        map_name_layout.addWidget(self.input_map_name)
        layout.addLayout(map_name_layout)
        
        # 下载/上传按钮
        map_io_layout = QHBoxLayout()
        map_io_layout.setSpacing(8)
        
        self.btn_download_map = QPushButton("⬇ 下载地图")
        self.btn_download_map.clicked.connect(self.sig_download_map.emit)
        
        self.btn_upload_map = QPushButton("⬆ 上传地图")
        self.btn_upload_map.clicked.connect(self.sig_upload_map.emit)
        
        map_io_layout.addWidget(self.btn_download_map)
        map_io_layout.addWidget(self.btn_upload_map)
        layout.addLayout(map_io_layout)

        # ---------- 4. SSH 系统操作组 ----------
        sys_label = QLabel("系统操作")
        sys_label.setStyleSheet("color: #d4d4d4; font-size: 13px; margin-top: 10px;")
        layout.addWidget(sys_label)
        
        self.btn_start_chassis = QPushButton("启动底盘 (Bringup)")
        self.btn_start_chassis.setProperty("class", "PrimaryAction")
        self.btn_start_chassis.clicked.connect(self.sig_start_chassis.emit)
        layout.addWidget(self.btn_start_chassis)
        
        self.btn_start_mqtt = QPushButton("启动 MQTT 节点")
        self.btn_start_mqtt.setProperty("class", "PrimaryAction")
        self.btn_start_mqtt.clicked.connect(self.sig_start_mqtt_node.emit)
        layout.addWidget(self.btn_start_mqtt)

    def bind_store(self):
        self.store.mapping_state_changed.connect(self._on_mapping_state_changed)
        self.store.navigation_state_changed.connect(self._on_navigation_state_changed)

    # ---------- UI 点击响应 (发射意图) ----------

    def _on_mapping_clicked(self):
        if not self.store.mapping_running:
            self.sig_start_mapping.emit()
        else:
            self.sig_stop_mapping.emit()

    def _on_navigation_clicked(self):
        if not self.store.navigation_running:
            self.sig_start_navigation.emit()
        else:
            self.sig_stop_navigation.emit()
            
    def _on_manual_initial(self):
        dlg = ManualPoseDialog(mode="initial", parent=self)
        if dlg.exec_() == QDialog.Accepted:
            x, y, yaw = dlg.get_values()
            self.sig_manual_initial_pose.emit(x, y, yaw)

    def _on_manual_goal(self):
        dlg = ManualPoseDialog(mode="goal", parent=self)
        if dlg.exec_() == QDialog.Accepted:
            x, y, yaw = dlg.get_values()
            self.sig_manual_goal.emit(x, y, yaw)

    # ---------- 响应 Store 状态改变 (重绘自适应) ----------

    def _on_mapping_state_changed(self, is_running: bool):
        if is_running:
            self.btn_toggle_mapping.setText("停止建图")
            self.btn_toggle_mapping.setProperty("class", "DangerAction")
            self.btn_save_map.setEnabled(True)
            self.btn_toggle_navigation.setEnabled(False) # 互斥锁定导航
        else:
            self.btn_toggle_mapping.setText("启动建图")
            self.btn_toggle_mapping.setProperty("class", "PrimaryAction")
            self.btn_save_map.setEnabled(False)
            self.btn_toggle_navigation.setEnabled(True)
            
        # 刷新 QSS (由于手动修改了 class property，需要 unpolish/polish)
        self.btn_toggle_mapping.style().unpolish(self.btn_toggle_mapping)
        self.btn_toggle_mapping.style().polish(self.btn_toggle_mapping)

    def _on_navigation_state_changed(self, is_running: bool):
        if is_running:
            self.btn_toggle_navigation.setText("停止导航")
            self.btn_toggle_navigation.setProperty("class", "DangerAction")
            self.btn_initial_pose.setEnabled(True)
            self.btn_goal_pose.setEnabled(True)
            self.btn_manual_initial.setEnabled(True)
            self.btn_manual_goal.setEnabled(True)
            self.btn_save_pose.setEnabled(True)
            self.btn_recall_pose.setEnabled(True)
            self.btn_toggle_mapping.setEnabled(False) # 互斥锁定建图
        else:
            self.btn_toggle_navigation.setText("启动导航")
            self.btn_toggle_navigation.setProperty("class", "PrimaryAction")
            self.btn_initial_pose.setEnabled(False)
            self.btn_goal_pose.setEnabled(False)
            self.btn_manual_initial.setEnabled(False)
            self.btn_manual_goal.setEnabled(False)
            self.btn_save_pose.setEnabled(False)
            self.btn_recall_pose.setEnabled(False)
            self.btn_toggle_mapping.setEnabled(True)
            
        self.btn_toggle_navigation.style().unpolish(self.btn_toggle_navigation)
        self.btn_toggle_navigation.style().polish(self.btn_toggle_navigation)

    def get_map_name(self) -> str:
        return self.input_map_name.text()
