import logging
from typing import Dict, Any, Optional, List
from PySide6.QtCore import QObject, Signal, QTimer
import numpy as np

from src.core.models import RobotPose, MapMetadata

class RobotStateHub(QObject):
    """
    统一状态中心 (Single Source of Truth)
    取代原本分散在各个 UI 组件中的成员变量。所有的网络层数据接收后都写入 Store，
    UI 层只监听 Store 的信号进行重绘，实现严格的单向数据流 (MVVM)。
    """
    
    # --- 遥测状态信号 ---
    voltage_changed = Signal(float, float)      # (voltage_value, percentage)
    chassis_alive_changed = Signal(bool)        # 底盘是否在线
    robot_pose_changed = Signal(RobotPose)      # 机器人位姿更新
    laser_scan_changed = Signal(dict)           # 激光雷达点云更新
    global_path_changed = Signal(list)          # 导航全局路径更新
    map_data_changed = Signal(MapMetadata)      # 大地图实时更新
    
    # --- 工作流状态信号 ---
    mapping_state_changed = Signal(bool)        # 建图开关状态
    navigation_state_changed = Signal(bool)     # 导航开关状态
    workflow_message = Signal(str)              # 系统级状态消息投递
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 内部状态存储区
        self._state = {
            "chassis_alive": False,
            "voltage": 0.0,
            
            "mapping_running": False,
            "navigation_running": False,
            
            "robot_pose": None,
            "target_pose": None,  # (x, y, yaw)
            "initial_pose": None,
            
            "map_metadata": None,
            "laser_scan": None,
            "global_path": [],
        }
        
        # 数据看门狗：2 秒未收到心跳则强制离线
        self._watchdog = QTimer(self)
        self._watchdog.timeout.connect(self._on_watchdog_timeout)
        self._watchdog.start(2000)

    def _ping_watchdog(self):
        """任意遥测数据到达时，重置看门狗计数"""
        self._watchdog.start(2000)

    def _on_watchdog_timeout(self):
        """超时未收到任何数据"""
        if self._state["chassis_alive"]:
            self._state["chassis_alive"] = False
            self.chassis_alive_changed.emit(False)
            logging.warning("[Store] Watchdog Timeout: 底盘已离线")

    # ================= 状态写入 API (Actions) ================= #

    def update_voltage(self, voltage: float):
        self._ping_watchdog()
        self._state["voltage"] = voltage
        
        # 换算百分比 (线性 20-24V)
        percent = min(max((voltage - 20.0) / (24.0 - 20.0), 0), 1) * 100.0
        self.voltage_changed.emit(voltage, percent)

    def update_chassis_status(self, is_alive: bool):
        self._ping_watchdog()
        if self._state["chassis_alive"] != is_alive:
            self._state["chassis_alive"] = is_alive
            self.chassis_alive_changed.emit(is_alive)

    def update_robot_pose(self, pose: RobotPose):
        self._ping_watchdog()
        self._state["robot_pose"] = pose
        self.robot_pose_changed.emit(pose)
        
    def update_scan(self, scan_data: dict):
        self._ping_watchdog()
        self._state["laser_scan"] = scan_data
        self.laser_scan_changed.emit(scan_data)
        
    def update_path(self, path: list):
        self._ping_watchdog()
        self._state["global_path"] = path
        self.global_path_changed.emit(path)

    def update_map(self, map_meta: MapMetadata):
        self._ping_watchdog()
        self._state["map_metadata"] = map_meta
        self.map_data_changed.emit(map_meta)
        
    # ================= 工作流 API ================= #
    def set_mapping_running(self, running: bool):
        self._state["mapping_running"] = running
        self.mapping_state_changed.emit(running)
        if running:
            self.set_navigation_running(False)
            
    def set_navigation_running(self, running: bool):
        self._state["navigation_running"] = running
        self.navigation_state_changed.emit(running)
        if running:
            self.set_mapping_running(False)
            
    def broadcast_message(self, msg: str):
        """用于控制台输出的状态机通告"""
        self.workflow_message.emit(msg)

    # ================= 状态读取 API (Getters) ================= #
    @property
    def mapping_running(self) -> bool:
        return self._state["mapping_running"]
        
    @property
    def navigation_running(self) -> bool:
        return self._state["navigation_running"]
        
    @property
    def current_pose(self) -> Optional[RobotPose]:
        return self._state["robot_pose"]
