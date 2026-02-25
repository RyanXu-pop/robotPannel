# navigation_controller.py
# -*- coding: utf-8 -*-
"""
NavigationController — 导航指令模块

负责目标坐标/角度发送、初始位姿的设置/保存/恢复，
封装与 MqttAgent 的交互，消除 MyMainWindow 对 MQTT 细节的直接依赖。
"""

import json
import math
import logging
from typing import Optional, Tuple, List

from PySide6.QtCore import QObject, Signal

from src.core.constants import PATHS_CONFIG, MQTT_TOPICS_CONFIG
from src.core.utils import apply_affine_transform


class NavigationController(QObject):
    """
    导航控制器。

    依赖:
        mqtt_agent:  MqttAgent 实例（用于发布 MQTT 消息）
    """
    
    status_message = Signal(str)

    def __init__(self, mqtt_agent, parent=None):
        """
        Args:
            mqtt_agent:  MqttAgent 实例
        """
        super().__init__(parent)
        self._mqtt = mqtt_agent


    # ------------------------------------------------------------------ #
    # 目标点发送
    # ------------------------------------------------------------------ #

    def send_goal(self, x: float, y: float, affine_M_inv,
                  robot_x: float, robot_y: float) -> Tuple[float, float, float]:
        """
        将像素/世界坐标转换为 ROS 坐标并发布导航目标。

        Args:
            x, y:        目标点世界坐标（地图坐标系）
            affine_M_inv: 仿射逆变换矩阵（世界 → ROS）
            robot_x, robot_y: 机器人当前世界坐标（仅用于计算 yaw）

        Returns:
            (target_x, target_y, yaw_deg) 供调用者更新内部状态
        """
        dx = x - robot_x
        dy = y - robot_y
        yaw = math.degrees(math.atan2(dy, dx))

        x_ros, y_ros = apply_affine_transform(affine_M_inv, [(x, y)])[0]

        self._mqtt.publish('goal', {"x": x_ros, "y": y_ros, "yaw": yaw})
        self.status_message.emit("状态: 目标发送指令已发送")
        logging.debug(f"[NavCtrl] send_goal → x_ros={x_ros:.3f}, y_ros={y_ros:.3f}, yaw={yaw:.1f}°")

        return x, y, yaw

    def send_goal_angle(self, robot_x: float, robot_y: float,
                        target_x: float, target_y: float,
                        affine_M_inv) -> Tuple[float, float, float]:
        """
        仅更新朝向角，机器人停在原地。

        Returns:
            (robot_x, robot_y, yaw_deg) 供调用者更新内部状态
        """
        dx = target_x - robot_x
        dy = target_y - robot_y
        yaw = math.degrees(math.atan2(dy, dx))

        x_ros, y_ros = apply_affine_transform(affine_M_inv, [(robot_x, robot_y)])[0]

        self._mqtt.publish('goal', {"x": x_ros, "y": y_ros, "yaw": yaw})
        self.status_message.emit("状态: 目标角度指令已发送")
        logging.debug(f"[NavCtrl] send_goal_angle → x_ros={x_ros:.3f}, y_ros={y_ros:.3f}, yaw={yaw:.1f}°")

        return robot_x, robot_y, yaw

    def set_goal_pose(self, x: float, y: float, yaw: float, affine_M_inv) -> bool:
        """
        根据用户在 UI 上点击并拖拽的方向，发布精确的目标点和朝向角。
        x, y 是目标坐标，yaw 是朝向角（弧度）。
        """
        x_ros, y_ros = apply_affine_transform(affine_M_inv, [(x, y)])[0]
        # 直接发送弧度
        try:
            self._mqtt.publish('goal', {"x": float(x_ros), "y": float(y_ros), "yaw": float(yaw)})
            self.status_message.emit(f"状态: 导航目标 ({x:.2f}, {y:.2f}) 已发送")
            logging.debug(f"[NavCtrl] set_goal_pose → x={x_ros:.3f}, y={y_ros:.3f}, yaw={yaw:.2f} rad")
            return True
        except Exception as e:
            logging.error(f"[NavCtrl] 导航目标发布失败: {e}")
            return False

    # ------------------------------------------------------------------ #
    # 初始位姿
    # ------------------------------------------------------------------ #

    def publish_initial_pose(self, x: float, y: float, yaw: float) -> bool:
        """
        向 ROS 发布初始位姿（initial_pose topic）。

        Returns:
            True 表示发布成功
        """
        try:
            self._mqtt.publish('initial_pose', {"x": float(x), "y": float(y), "angle": float(yaw)})
            logging.debug(f"[NavCtrl] publish_initial_pose → x={x}, y={y}, yaw={yaw}")
            return True
        except Exception as e:
            logging.error(f"[NavCtrl] 初始位姿发布失败: {e}")
            return False

    def set_initial_pose(self, x: float, y: float, yaw: float, affine_M_inv) -> bool:
        """
        将世界坐标 (x, y, yaw) 变换为 ROS 坐标后发布。

        Returns:
            True 表示成功
        """
        x_ros, y_ros = apply_affine_transform(affine_M_inv, [(x, y)])[0]
        result = self.publish_initial_pose(x_ros, y_ros, yaw)
        if result:
            self.status_message.emit(f"状态: 初始位置 ({x:.2f}, {y:.2f}) 同步指令已发送至ROS")
        return result


    def save_initial_pose(self, x_str: str, y_str: str, yaw_str: str) -> bool:
        """
        将初始位姿字符串持久化到 JSON 文件。

        Args:
            x_str, y_str, yaw_str: 来自 UI 输入框的原始字符串
        """
        try:
            pose_data = {"x": x_str, "y": y_str, "yaw": yaw_str}
            with open(PATHS_CONFIG['initial_pose_json'], 'w') as f:
                json.dump(pose_data, f)
            self.status_message.emit("状态: 初始位置已保存")
            return True
        except Exception as e:
            self.status_message.emit(f"状态: 保存失败 - {e}")
            logging.error(f"[NavCtrl] 保存初始位置失败: {e}")
            return False

    def recall_initial_pose(self) -> Optional[dict]:
        """
        从 JSON 文件读取已保存的初始位姿。

        Returns:
            {"x": str, "y": str, "yaw": str} 或 None（文件不存在）
        """
        try:
            with open(PATHS_CONFIG['initial_pose_json'], 'r') as f:
                pose_data = json.load(f)
            self.status_message.emit("状态: 已恢复保存的初始位置")
            return pose_data
        except FileNotFoundError:
            self.status_message.emit("状态: 未找到已保存的初始位置文件")
            return None
        except Exception as e:
            logging.error(f"[NavCtrl] 读取初始位置失败: {e}")
            return None
