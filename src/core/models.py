"""
models.py
---------
定义系统核心实体的数据模型（Strong Typing）。
利用 dataclasses 提供自动的 __init__、__repr__ 和静态类型支持，
取代在各个模块中散落的隐式字典传递，将运行时 KeyError 等风险扼杀于此。
"""

from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Any
from PySide6.QtCore import QObject, Signal



@dataclass
class RobotPose:
    """机器人位姿"""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    yaw: float = 0.0      # 朝向角（弧度）
    angle: float = 0.0    # 朝向角（角度，系统内为了直观经常使用）
    source: str = ""      # 数据来源：如 'amcl', 'odom'

    @classmethod
    def from_dict(cls, data: dict, default_source: str = "") -> "RobotPose":
        """从不可信字典安全构造类型实体，兼容新旧参数名"""
        if not isinstance(data, dict):
            return cls(source=default_source)
            
        import math
        
        # 提取并在类型边界处统一校验
        x = float(data.get("x", 0.0))
        y = float(data.get("y", 0.0))
        z = float(data.get("z", 0.0))
        if "yaw" in data and "angle" not in data:
            yaw = float(data["yaw"])
            if abs(yaw) > math.pi * 2:
                angle_deg = yaw
                yaw = math.radians(yaw)
            else:
                angle_deg = math.degrees(yaw)
        elif "angle" in data and "yaw" not in data:
            angle_deg = float(data["angle"])
            yaw = math.radians(angle_deg)
        else:
            yaw = float(data.get("yaw", 0.0))
            angle_deg = float(data.get("angle", math.degrees(yaw)))

        return cls(
            x=x,
            y=y,
            z=z,
            yaw=yaw,
            angle=angle_deg,
            source=data.get("source", default_source)
        )


@dataclass
class MapMetadata:
    """地图元数据（支持建图实时地图和静态配置地图）"""
    resolution: float = 0.05
    origin_x: float = 0.0
    origin_y: float = 0.0
    width: int = 0
    height: int = 0
    data: Optional[Any] = None  # NumPy array 或类似数据，供实时建图
    
    @classmethod
    def from_dict(cls, data: dict) -> "MapMetadata":
        if not isinstance(data, dict):
            return cls()
        return cls(
            resolution=float(data.get("resolution", 0.05)),
            origin_x=float(data.get("origin_x", 0.0)),
            origin_y=float(data.get("origin_y", 0.0)),
            width=int(data.get("width", 0)),
            height=int(data.get("height", 0)),
            data=data.get("data")
        )

from enum import Enum, auto

class SystemState(Enum):
    OFFLINE = auto()
    IDLE = auto()
    MAPPING = auto()
    NAVIGATING = auto()

class AppSystemState(QObject):
    """
    系统状态机 (State-Driven Reactive UI)
    集中管理各个服务的运行状态，基于严格的 Enum 状态机防止由于同时开启建图和导航等导致的状态错乱。
    当状态变更时，自动发射对应信号以更新前端 UI。
    """
    state_changed = Signal(SystemState)
    
    # 为了向后兼容，保留旧信号，但内部由状态机驱动
    mqtt_changed = Signal(bool)
    chassis_changed = Signal(bool)
    mapping_changed = Signal(bool)
    navigation_changed = Signal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_state = SystemState.OFFLINE
        
        # 保留旧变量适配旧的UI逻辑
        self._mqtt_running = False
        self._chassis_running = False

    @property
    def current_state(self) -> SystemState:
        return self._current_state
        
    def set_state(self, new_state: SystemState):
        if self._current_state != new_state:
            old_state = self._current_state
            self._current_state = new_state
            self.state_changed.emit(new_state)
            
            # 向后兼容信号派发
            if old_state == SystemState.MAPPING and new_state != SystemState.MAPPING:
                self.mapping_changed.emit(False)
            if new_state == SystemState.MAPPING:
                self.mapping_changed.emit(True)
                
            if old_state == SystemState.NAVIGATING and new_state != SystemState.NAVIGATING:
                self.navigation_changed.emit(False)
            if new_state == SystemState.NAVIGATING:
                self.navigation_changed.emit(True)

    # ---------- 向后兼容属性 ----------
    @property
    def mapping_running(self) -> bool:
        return self._current_state == SystemState.MAPPING

    @mapping_running.setter
    def mapping_running(self, val: bool):
        if val:
            self.set_state(SystemState.MAPPING)
        elif self._current_state == SystemState.MAPPING:
            self.set_state(SystemState.IDLE if self.chassis_running else SystemState.OFFLINE)

    @property
    def navigation_running(self) -> bool:
        return self._current_state == SystemState.NAVIGATING

    @navigation_running.setter
    def navigation_running(self, val: bool):
        if val:
            self.set_state(SystemState.NAVIGATING)
        elif self._current_state == SystemState.NAVIGATING:
            self.set_state(SystemState.IDLE if self.chassis_running else SystemState.OFFLINE)

    @property
    def mqtt_running(self) -> bool:
        return self._mqtt_running

    @mqtt_running.setter
    def mqtt_running(self, val: bool):
        if self._mqtt_running != val:
            self._mqtt_running = val
            self.mqtt_changed.emit(val)

    @property
    def chassis_running(self) -> bool:
        return self._chassis_running

    @chassis_running.setter
    def chassis_running(self, val: bool):
        if self._chassis_running != val:
            self._chassis_running = val
            self.chassis_changed.emit(val)
            if val and self._current_state == SystemState.OFFLINE:
                self.set_state(SystemState.IDLE)
            elif not val:
                self.set_state(SystemState.OFFLINE)


from collections import defaultdict
import time

class ErrorAggregator(QObject):
    """
    全局异常限流器 (Error Debouncer)
    针对高频触发的（比如每秒 10 次的 MQTT 解析报错）网络/解析异常进行聚合防抖，
    避免 UI 弹窗风暴（弹成千上万个错误引发线程卡死）。
    """
    # 信号：发射聚合后的错误描述文本
    error_flushed = Signal(str)

    def __init__(self, flush_interval: float = 2.0, parent=None):
        super().__init__(parent)
        self.flush_interval = flush_interval
        self._error_counts = defaultdict(int)
        self._last_flush_time = time.time()

    def report_error(self, error_key: str, error_detail: str = ""):
        """收集错误"""
        full_msg = f"{error_key}: {error_detail}" if error_detail else error_key
        self._error_counts[full_msg] += 1
        
        # 如果超出时间间隔，主动派发聚合日志
        if time.time() - self._last_flush_time > self.flush_interval:
            self.flush()

    def flush(self):
        """立即推送已聚合的错误并清空计数"""
        if not self._error_counts:
            return
            
        messages = []
        for msg, count in self._error_counts.items():
            if count > 1:
                messages.append(f"[{count}次] {msg}")
            else:
                messages.append(msg)
                
        self._error_counts.clear()
        self._last_flush_time = time.time()
        
        combined_msg = " \n".join(messages)
        self.error_flushed.emit(combined_msg)
