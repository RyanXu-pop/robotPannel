import os
import sys
import logging
import asyncio
from typing import Optional
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox
from PySide6.QtCore import Qt, Slot, QTimer

# 核心与网络
from src.core.constants import PATHS_CONFIG, PARAMS_CONFIG, CONFIG
from src.network.mqtt_agent import MqttAgent
from src.network.async_ssh_manager import AsyncSSHManager
from src.controllers.map_manager import MapManager
from src.controllers.workflow_controller import WorkflowController
from src.controllers.navigation_controller import NavigationController
from src.controllers.teleop_controller import TeleopController
from src.controllers.pose_recorder import PoseRecorder
from src.ui.system_setting import SystemSetting

# V2 引入
from .theme import apply_theme
from .robot_state_hub import RobotStateHub
from .map.map_view import MapGraphicsView
from .panels.telemetry_panel import TelemetryPanel
from .panels.control_panel import ControlPanel
from .panels.teleop_panel import TeleopPanel
from .panels.pose_panel import PoseRecordPanel
from .panels.unified_drawer import UnifiedDrawer

class MyMainWindow(QMainWindow):
    """
    UI V2 主窗口
    采用单向数据流 (MVVM)：
      MqttAgent -> Store -> Panels/MapView
    """
    def __init__(self, mqtt_agent=None):
        super().__init__()
        # 全局应用暗色主题
        from PySide6.QtWidgets import QApplication
        apply_theme(QApplication.instance())
        
        self.setWindowTitle("ROS2 Control Panel V2")
        self.setMinimumSize(1024, 768)

        # 1. 核心状态池 (Single Source of Truth)
        self.store = RobotStateHub(self)
        
        # 2. 网络设施初始化
        self.async_ssh = AsyncSSHManager()
        self.mqtt_agent = mqtt_agent if mqtt_agent is not None else MqttAgent()
        
        # 3. 控制器初始化
        self.map_mgr = MapManager(map_bounds=PARAMS_CONFIG['map_bounds'])
        self.workflow_ctrl = WorkflowController(self.async_ssh, self.map_mgr, self)
        self.nav_ctrl = NavigationController(mqtt_agent=self.mqtt_agent)
        self.teleop_ctrl = TeleopController(mqtt_agent=self.mqtt_agent, parent=self)
        record_xlsx_path = PATHS_CONFIG.get('record_xlsx', 'pose_records.xlsx')
        self.pose_recorder = PoseRecorder(record_xlsx_path, parent=self)
        
        # 4. 界面构建
        self._setup_ui()
        
        # 5. 信号绑定 (数据总线)
        self._bind_signals()
        
        # 6. 加载地初始数据
        self._load_initial_data()
        
        # 7. 启动 MQTT
        try:
            self.mqtt_agent.connect_broker()
            logging.info("[V2] MqttAgent started.")
        except Exception as e:
            logging.error(f"[V2] MqttAgent connect failed: {e}")

    def _setup_ui(self):
        """构建现代悬浮 UI 布局"""
        # Central Widget 作为底层画布容器
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        # 完全填满窗口
        base_layout = QVBoxLayout(central_widget)
        base_layout.setContentsMargins(0, 0, 0, 0)
        
        # 核心地图视图
        self.map_view = MapGraphicsView()
        base_layout.addWidget(self.map_view)
        
        # --- 悬浮操作区设定 (Absolute Positioning Overlay) ---
        # 通过将 Panel 的 parent 设置为 map_view 并指定坐标，实现不占用布局空间的纯粹叠加
        
        # 右上角：遥测展板
        self.telemetry_panel = TelemetryPanel(self.store)
        self.control_panel = ControlPanel(self.store, self.map_view)
        
        # 因为我们现在用抽屉装它们，原有的抽屉把手不需要了，
        # 我们可以在组装前去掉它们内部的折叠逻辑，或者直接嵌入。
        # 这里为保持最少修改，我们让它们各自保持展开即可。
        self.teleop_panel = TeleopPanel()
        self.teleop_panel.toggle_drawer() # 强行展开内部
        self.teleop_panel.header_btn.hide() # 隐藏内部标题
        
        self.pose_panel = PoseRecordPanel()
        self.pose_panel.toggle_drawer() # 强行展开内部
        self.pose_panel.header_btn.hide() # 隐藏内部标题

        # 左侧定位统一抽屉
        self.unified_drawer = UnifiedDrawer(self.map_view)
        self.unified_drawer.add_panel(self.telemetry_panel)
        self.unified_drawer.add_panel(self.control_panel)
        self.unified_drawer.add_panel(self.teleop_panel)
        self.unified_drawer.add_panel(self.pose_panel)
        
        # 顶部：系统设置与全屏按钮
        self.top_bar = QWidget(parent=self.map_view)
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setAlignment(Qt.AlignRight)
        
        self.btn_simulation = QPushButton("🟢 仿真")
        self.btn_simulation.setCheckable(True)
        self.btn_simulation.setStyleSheet("background: rgba(40,40,40,200); color: white; border-radius: 4px; padding: 6px 12px;")
        self.btn_simulation.clicked.connect(self._toggle_simulation)
        top_layout.addWidget(self.btn_simulation)
        
        self.btn_fullscreen = QPushButton("⛶ 全屏")
        self.btn_fullscreen.setStyleSheet("background: rgba(40,40,40,200); color: white; border-radius: 4px; padding: 6px 12px;")
        self.btn_fullscreen.clicked.connect(self._toggle_fullscreen)
        top_layout.addWidget(self.btn_fullscreen)
        
        self.btn_settings = QPushButton("⚙ 设置")
        self.btn_settings.setStyleSheet("background: #007acc; color: white; border-radius: 4px; padding: 6px 12px;")
        self.btn_settings.clicked.connect(self._show_system_settings)
        top_layout.addWidget(self.btn_settings)

        # 悬浮定位小车按钮 (Apple Maps Locate Me)
        self.btn_locate_me = QPushButton("📍")
        self.btn_locate_me.setParent(self.map_view)
        self.btn_locate_me.setCursor(Qt.PointingHandCursor)
        self.btn_locate_me.setStyleSheet("""
            QPushButton {
                background: rgba(45, 45, 48, 230);
                color: #007acc;
                border: 1px solid #3e3e42;
                border-radius: 20px;
                font-size: 20px;
                padding-bottom: 2px;
            }
            QPushButton:hover {
                background: #3e3e42;
                color: #0098ff;
            }
        """)
        self.btn_locate_me.setFixedSize(40, 40)
        self.btn_locate_me.clicked.connect(self._center_map_on_robot)
        
        # 利用 resizeEvent 动态调整悬浮组件位置
        self.map_view.installEventFilter(self)

    def eventFilter(self, obj, event):
        """动态更新悬浮窗坐标以实现响应式"""
        from PySide6.QtCore import QEvent
        if obj is self.map_view and event.type() == QEvent.Resize:
            w = event.size().width()
            h = event.size().height()
            
            # 定位顶部快捷栏
            self.top_bar.setGeometry(w - 250, 20, 230, 40)
            
            # 统一抽屉定位于左下角，类似 Apple Maps
            margin = 20
            drawer_h = int(h * 0.85) # 抽屉最大占屏幕高度 85%
            self.unified_drawer.set_max_height(drawer_h)
            
            # self.unified_drawer.height() 会随着动画改变
            self.unified_drawer.move(margin, h - self.unified_drawer.height() - margin)
            
            # 定位 Locate Me 按钮 (右下角)
            self.btn_locate_me.move(w - 60, h - 60)
            
        return super().eventFilter(obj, event)

    def _bind_signals(self):
        """核心数据流组装"""
        # ================== MQTT Data -> Store ==================
        self.mqtt_agent.pose_updated.connect(self.store.update_robot_pose)
        self.mqtt_agent.voltage_updated.connect(self.store.update_voltage)
        self.mqtt_agent.chassis_status_updated.connect(self.store.update_chassis_status)
        self.mqtt_agent.scan_updated.connect(lambda scan: self.store.update_scan(scan))
        self.mqtt_agent.path_updated.connect(self.store.update_path)
        self.mqtt_agent.map_updated.connect(self.store.update_map)
        
        # MQTT 连接状态 → Store + TelemetryPanel
        self.mqtt_agent.connection_status.connect(self._on_mqtt_connection_status)
        
        # Odom 数据 → 建图模式下更新位姿
        if hasattr(self.mqtt_agent, 'odom_updated'):
            self.mqtt_agent.odom_updated.connect(self._on_odom_data)

        # ================== Store -> MapView ==================
        self.store.map_data_changed.connect(self.map_view.update_map)
        self.store.global_path_changed.connect(self.map_view.update_path)
        
        def safely_update_robot(pose):
            if pose:
                self.map_view.update_robot_pose(pose.x, pose.y, pose.yaw)
                if self.pose_recorder.recording:
                    self.pose_recorder.append(pose.x, pose.y, 0.0, pose.yaw)
        self.store.robot_pose_changed.connect(safely_update_robot)
        
        def safely_update_scan(scan_dict):
            pose = self.store.current_pose
            if pose is not None and scan_dict:
                self.map_view.update_scan(scan_dict, pose.x, pose.y, pose.yaw)
        self.store.laser_scan_changed.connect(safely_update_scan)

        # ================== Unified Drawer Animations ==================
        def _reposition_drawer(h):
            if not self.map_view: return
            my_h = self.map_view.height()
            margin = 20
            self.unified_drawer.move(margin, my_h - h - margin)
        self.unified_drawer.height_changed.connect(_reposition_drawer)
        
        # ================== Pose Recorder / Navigation ==================
        self.pose_panel.sig_start_trace.connect(self.pose_recorder.start)
        self.pose_panel.sig_start_trace.connect(lambda: self.pose_panel.set_trace_active(True))
        
        def on_stop_trace():
            ok = self.pose_recorder.stop()
            self.pose_panel.set_trace_active(False)
            if ok:
                QMessageBox.information(self, "记录完成", "连续轨迹已保存至 pose_records.xlsx")
        self.pose_panel.sig_stop_trace.connect(on_stop_trace)
        
        def on_record_point():
            pose = self.store.current_pose
            if pose:
                self.pose_panel.add_point(pose.x, pose.y, pose.angle)
                logging.info(f"[PoseRecord] 手动打卡位置: {pose.x}, {pose.y}, {pose.angle}")
        self.pose_panel.sig_record_point.connect(on_record_point)
        
        import numpy as np
        self.pose_panel.sig_go_to_selected.connect(
            lambda x, y, yaw: self.nav_ctrl.set_goal_pose(x, y, yaw, np.eye(3))
        )
        self.pose_recorder.status_message.connect(lambda msg: logging.info(f"[PoseRecorder] {msg}"))
        
        # ================== UI Intents -> Controllers ==================
        # 接收并显示系统级全局通知
        def show_popup(msg):
            # Only pop up for final results, not intermediate "正在..." steps
            if "成功" in msg or "失败" in msg or "完成" in msg:
                QMessageBox.information(self, "系统提示", msg)
            else:
                self.statusBar().showMessage(msg, 3000)
                
        self.store.workflow_message.connect(show_popup)
        
        # 建图开关
        self.control_panel.sig_start_mapping.connect(self._do_start_mapping)
        self.control_panel.sig_stop_mapping.connect(self._do_stop_mapping)
        self.control_panel.sig_save_map.connect(self._do_save_map)
        
        # 导航开关
        self.control_panel.sig_start_navigation.connect(self._do_start_nav)
        self.control_panel.sig_stop_navigation.connect(self._do_stop_nav)
        
        # 交互设定
        self.control_panel.sig_set_initial_pose.connect(lambda: self.map_view.set_interaction_mode("initial_pose"))
        self.control_panel.sig_set_goal_pose.connect(lambda: self.map_view.set_interaction_mode("goal"))
        
        # 处理手动坐标输入
        import numpy as np
        identity_inv = np.eye(3)
        self.control_panel.sig_manual_initial_pose.connect(
            lambda x, y, yaw: self.nav_ctrl.set_initial_pose(x, y, yaw, identity_inv)
        )
        self.control_panel.sig_manual_goal.connect(
            lambda x, y, yaw: self.nav_ctrl.set_goal_pose(x, y, yaw, identity_inv)
        )
        # 地图回传意图处理器
        self.map_view.interaction_triggered.connect(self._on_map_interaction)

        # 工作流消息
        self.workflow_ctrl.status_message.connect(lambda msg: logging.info(f"[Workflow] {msg}"))
        self.workflow_ctrl.map_synced.connect(self._load_initial_data)
        
        # SSH 系统操作
        self.control_panel.sig_start_chassis.connect(self._do_start_chassis)
        self.control_panel.sig_start_mqtt_node.connect(self._do_start_mqtt_node)
        
        # 地图下载/上传
        self.control_panel.sig_download_map.connect(self._do_download_map)
        self.control_panel.sig_upload_map.connect(self._do_upload_map)
        
        # 初始位姿保存/恢复
        self.control_panel.sig_save_initial_pose.connect(self._do_save_initial_pose)
        self.control_panel.sig_recall_initial_pose.connect(self._do_recall_initial_pose)

    def _load_initial_data(self):
        """首次加载静态地图"""
        ok = self.map_mgr.load(PATHS_CONFIG['map_yaml'])
        if ok and self.map_mgr.map_data:
            from src.core.models import MapMetadata
            
            map_data = self.map_mgr.map_data
            img = map_data['image']
            
            meta = MapMetadata(
                resolution=map_data.get('resolution', 0.05),
                origin_x=map_data.get('origin', [0, 0, 0])[0],
                origin_y=map_data.get('origin', [0, 0, 0])[1],
                width=img.shape[1],
                height=img.shape[0],
                data=img
            )
            self.store.update_map(meta)

    # ---------------- 业务编排 ----------------
    
    @Slot()
    def _do_start_mapping(self):
        self.store.set_mapping_running(True)
        import asyncio
        asyncio.create_task(self.workflow_ctrl.execute_mapping_workflow())
        
    @Slot()
    def _do_stop_mapping(self):
        self.store.set_mapping_running(False)
        import asyncio
        asyncio.create_task(self.workflow_ctrl.execute_stop_mapping_workflow())

    @Slot()
    def _do_save_map(self):
        import asyncio
        asyncio.create_task(self.workflow_ctrl.execute_save_map_workflow())
        QMessageBox.information(self, "已下发", "地图保存指令已下发，请稍候...")

    @Slot()
    def _do_start_nav(self):
        self.store.set_navigation_running(True)
        import asyncio
        asyncio.create_task(self.workflow_ctrl.execute_navigation_workflow())

    @Slot()
    def _do_stop_nav(self):
        self.store.set_navigation_running(False)
        import asyncio
        asyncio.create_task(self.workflow_ctrl.execute_stop_navigation_workflow())

    @Slot(float, float, float, str)
    def _on_map_interaction(self, x: float, y: float, yaw: float, mode: str):
        import numpy as np
        # V2 地图直接工作在物理世界坐标系，所以逆变换矩阵为单位阵
        identity_inv = np.eye(3)
        if mode == 'initial_pose':
            self.nav_ctrl.set_initial_pose(x, y, yaw, identity_inv)
            logging.info(f"[_on_map_interaction] Sent initial pose: {x}, {y}, {yaw}")
        elif mode == 'goal':
            self.nav_ctrl.set_goal_pose(x, y, yaw, identity_inv)
            logging.info(f"[_on_map_interaction] Sent Nav goal: {x}, {y}, {yaw}")
            
    @Slot(float, float, float)
    def _on_manual_initial_pose(self, x: float, y: float, yaw: float):
        import numpy as np
        identity_inv = np.eye(3)
        self.nav_ctrl.set_initial_pose(x, y, yaw, identity_inv)
        logging.info(f"[Manual] Sent initial pose: x={x}, y={y}, yaw={yaw}")

    @Slot(float, float, float)
    def _on_manual_goal(self, x: float, y: float, yaw: float):
        import numpy as np
        identity_inv = np.eye(3)
        self.nav_ctrl.set_goal_pose(x, y, yaw, identity_inv)
        logging.info(f"[Manual] Sent nav goal: x={x}, y={y}, yaw={yaw}")

    def _center_map_on_robot(self):
        """将视角中心平滑移动到当前小车所在位置"""
        pose = self.store.current_pose
        if pose is not None and self.map_view:
            self.map_view.centerOn(pose.x, pose.y)

    # ---------------- 杂项设置与仿真 ----------------
    
    @Slot()
    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
            
    @Slot()
    def _show_system_settings(self):
        dialog = SystemSetting(current_config=CONFIG, parent=self)
        if dialog.exec():
            # Apply changes (naive reconnect for MQTT if needed)
            settings = dialog.get_settings()
            new_host = settings.get("ip", self.mqtt_agent.host)
            new_port = self.mqtt_agent.port
            try:
                new_port = int(settings.get("port", self.mqtt_agent.port))
            except: pass
            
            if new_host != self.mqtt_agent.host or new_port != self.mqtt_agent.port:
                self.mqtt_agent.update_connection(new_host, new_port)

    # 仿真子进程列表
    _sim_processes = []
    
    @Slot(bool)
    def _toggle_simulation(self, checked: bool):
        self.async_ssh.mock_mode = checked
        if checked:
            self.btn_simulation.setText("🔴 停止仿真")
            import subprocess
            scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'scripts')
            for name in ['mock_robot.py', 'mock_lidar.py']:
                p = os.path.join(scripts_dir, name)
                if os.path.isfile(p):
                    proc = subprocess.Popen([sys.executable, p], stdout=None, stderr=None)
                    self._sim_processes.append(proc)
        else:
            self.btn_simulation.setText("🟢 启动仿真")
            for p in self._sim_processes:
                p.terminate()
            self._sim_processes.clear()

    # ---------------- SSH 系统操作 ----------------
    @Slot()
    def _do_start_chassis(self):
        import asyncio
        asyncio.create_task(self.workflow_ctrl.execute_chassis_workflow())
        logging.info("[V2] Chassis bringup requested.")

    @Slot()
    def _do_start_mqtt_node(self):
        import asyncio
        asyncio.create_task(self.workflow_ctrl.execute_mqtt_workflow())
        logging.info("[V2] MQTT node start requested.")

    # ---------------- 地图下载/上传 ----------------
    @Slot()
    def _do_download_map(self):
        from PySide6.QtWidgets import QFileDialog
        save_dir = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if save_dir:
            import asyncio
            asyncio.create_task(self.workflow_ctrl.download_map(save_dir))
            QMessageBox.information(self, "已下发", f"地图将下载到: {save_dir}")

    @Slot()
    def _do_upload_map(self):
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(self, "选择地图文件", "", "地图 (*.yaml *.pgm *.png);;All (*)")
        if file_path:
            import asyncio
            asyncio.create_task(self.workflow_ctrl.upload_map(file_path))
            QMessageBox.information(self, "已下发", f"地图将上传: {file_path}")

    # ---------------- 初始位姿保存/恢复 ----------------
    @Slot()
    def _do_save_initial_pose(self):
        import json
        pose = self.store.current_pose
        if pose:
            data = {"x": pose.x, "y": pose.y, "yaw": pose.angle}
            path = PATHS_CONFIG.get('initial_pose_json', 'initial_pose.json')
            with open(path, 'w') as f:
                json.dump(data, f)
            logging.info(f"[V2] Saved initial pose to {path}: {data}")
            QMessageBox.information(self, "已保存", f"初始位姿已保存至 {path}")
        else:
            QMessageBox.warning(self, "无数据", "当前没有有效的机器人位姿")

    @Slot()
    def _do_recall_initial_pose(self):
        import json, numpy as np
        path = PATHS_CONFIG.get('initial_pose_json', 'initial_pose.json')
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            x, y, yaw = data['x'], data['y'], data['yaw']
            self.nav_ctrl.set_initial_pose(x, y, yaw, np.eye(3))
            logging.info(f"[V2] Recalled initial pose from {path}: {data}")
            QMessageBox.information(self, "已恢复", f"初始位姿已恢复: X={x:.2f} Y={y:.2f} Yaw={yaw:.2f}")
        except FileNotFoundError:
            QMessageBox.warning(self, "文件不存在", f"未找到保存文件: {path}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"恢复失败: {e}")

    # ---------------- MQTT 连接状态 ----------------
    def _on_mqtt_connection_status(self, connected: bool, message: str):
        logging.info(f"MQTT Status: {connected} - {message}")
        # 更新遥测面板的连接指示器
        if connected:
            self.telemetry_panel.indicator_circle.setStyleSheet("color: #3fb950; font-size: 16px;")
            self.telemetry_panel.status_label.setText("MQTT 已连接")
        else:
            self.telemetry_panel.indicator_circle.setStyleSheet("color: #f14c4c; font-size: 16px;")
            self.telemetry_panel.status_label.setText("MQTT 连接断开")

    # ---------------- Odom (建图模式) ----------------
    def _on_odom_data(self, pose):
        if self.store.mapping_running and pose:
            self.store.update_robot_pose(pose)

    # ---------------- 键盘遥控 (WASD) ----------------
    def keyPressEvent(self, event):
        if hasattr(self, 'teleop_ctrl'):
            self.teleop_ctrl.handle_key_press(event)
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if hasattr(self, 'teleop_ctrl'):
            self.teleop_ctrl.handle_key_release(event)
        super().keyReleaseEvent(event)

    # ---------------- 窗口关闭 ----------------
    def closeEvent(self, event):
        for p in self._sim_processes:
            p.terminate()
        try:
            loop = asyncio.get_event_loop()
            asyncio.ensure_future(self.async_ssh.close_async())
        except:
            pass
        event.accept()
