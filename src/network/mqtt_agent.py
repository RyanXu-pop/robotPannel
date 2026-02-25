# mqtt_agent.py
import paho.mqtt.client as mqtt
from PySide6.QtCore import QObject, Signal
import json
import logging
import base64
import zlib
from typing import Optional
import numpy as np
from src.core.constants import MQTT_CONFIG, MQTT_TOPICS_CONFIG, TOPICS_CONFIG
from src.core.models import RobotPose, MapMetadata, ErrorAggregator


class RosMsgAdapter:
    # Topic key → config key 映射表（取代原来的 if-elif 链）
    _TOPIC_TYPE_MAP = {
        'pose': 'amcl_pose_msg_type',
        'voltage': 'power_voltage_msg_type',
        'goal': 'pose_stamped_msg_type',
        'initial_pose': 'amcl_pose_msg_type',
        # status 使用 JSON，不需要 ROS 类型映射
    }

    @staticmethod
    def get_ros_type_by_topic(topic: str) -> Optional[str]:
        """通过 MQTT topic 反查对应的 ROS 消息类型"""
        for k, v in MQTT_TOPICS_CONFIG.items():
            if v == topic:
                if k == 'status':
                    return None  # status 话题是 JSON 格式
                ros_key = RosMsgAdapter._TOPIC_TYPE_MAP.get(k)
                if ros_key and ros_key in TOPICS_CONFIG:
                    return TOPICS_CONFIG[ros_key]
        return None

    @staticmethod
    def parse(topic: str, payload: str):
        ros_type = RosMsgAdapter.get_ros_type_by_topic(topic)
        try:
            if ros_type == "geometry_msgs/PoseWithCovarianceStamped":
                # 期望为JSON，直接返回dict
                return json.loads(payload)
            elif ros_type == "geometry_msgs/PoseStamped":
                return json.loads(payload)
            elif ros_type == "std_msgs/Float32" or ros_type == "std_msgs/UInt16":
                return float(payload)
            else:
                # 默认尝试json（包括 status 话题和其他未映射的话题）
                return json.loads(payload)
        except Exception:
            return payload

    @staticmethod
    def serialize(topic: str, data):
        ros_type = RosMsgAdapter.get_ros_type_by_topic(topic)
        if ros_type == "std_msgs/Float32":
            return str(float(data))
        else:
            return json.dumps(data)

class MqttAgent(QObject):
    pose_updated = Signal(RobotPose)      # AMCL 位姿（导航模式）
    odom_updated = Signal(RobotPose)      # Odom 位姿（建图模式）- 新增

    voltage_updated = Signal(float)  # 保留以兼容旧代码
    chassis_status_updated = Signal(bool)  # 底盘健康状态信号
    status_updated = Signal(dict)  # 完整状态信号：{"chassis_alive": bool, "voltage": float}
    connection_status = Signal(bool, str)
    goal_updated = Signal(dict)
    initialpose_updated = Signal(dict)
    # 建图相关信号
    map_updated = Signal(MapMetadata)  # 地图数据

    scan_updated = Signal(dict)  # 激光数据：{"angle_min", "angle_max", "ranges", ...}
    path_updated = Signal(list)  # 全局路径规划：[{"x": float, "y": float}, ...]
    
    # 新增：聚合后的 MQTT 错误信号
    mqtt_error_aggregated = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化错误聚合器，每 3 秒刷新一次
        self.error_aggregator = ErrorAggregator(flush_interval=3.0)
        self.error_aggregator.error_flushed.connect(self.mqtt_error_aggregated.emit)

        self.host = MQTT_CONFIG.get('host', 'localhost')
        self.port = MQTT_CONFIG.get('port', 1883)
        self.username = MQTT_CONFIG.get('username', None)
        self.password = MQTT_CONFIG.get('password', None)
        self.topics = MQTT_TOPICS_CONFIG
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.is_connected = False

    def connect_broker(self):
        """连接到 MQTT Broker 并启动消息循环。"""
        try:
            self.client.connect(self.host, self.port, 60)
            self.client.loop_start()
        except Exception as e:
            logging.error(f"[MQTT] 连接失败: {e}")
            self.connection_status.emit(False, f"MQTT 连接失败: {e}")


    def publish(self, topic_key: str, payload: dict) -> bool:
        """
        发布消息到指定 topic。
        
        Args:
            topic_key: topics 配置中的 key（如 'goal'），也可直接传入完整 topic 字符串。
            payload: 要发送的数据（会自动序列化为 JSON）。
        
        Returns:
            True 表示已发送，False 表示当前未连接。
        """
        if not self.is_connected:
            logging.warning(f"[MQTT] 未连接，无法发布到 '{topic_key}'")
            return False
        topic = self.topics.get(topic_key, topic_key)
        try:
            self.client.publish(topic, json.dumps(payload))
            logging.debug(f"[MQTT] 发布到 {topic}: {payload}")
            return True
        except Exception as e:
            logging.error(f"[MQTT] 发布失败 ({topic}): {e}")
            return False


    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self.is_connected = True
            self.connection_status.emit(True, "已连接到 MQTT 服务器")
            # 订阅所有配置的 topic
            for topic in self.topics.values():
                client.subscribe(topic)
                logging.info(f"[MQTT] 已订阅: {topic}")
        else:
            self.connection_status.emit(False, f"MQTT 连接失败，返回码: {reason_code}")

    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        self.is_connected = False
        self.connection_status.emit(False, f"MQTT 断开连接 (码: {reason_code})")
        logging.warning(f"[MQTT] 断开连接, 状态码: {reason_code}")

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode(errors='ignore')
        
        try:
            parsed = RosMsgAdapter.parse(topic, payload)
        except Exception as e:
            self.error_aggregator.report_error(f"消息解析失败 [{topic}]", str(e))
            return
            
        # 解析并分发信号
        if topic == self.topics.get('pose'):
            if isinstance(parsed, dict):
                self.pose_updated.emit(RobotPose.from_dict(parsed, default_source='amcl'))

        elif topic == self.topics.get('status'):
            # 新的状态消息：{"chassis_alive": bool, "voltage": float}
            if isinstance(parsed, dict):
                # 发送完整状态信号
                self.status_updated.emit(parsed)
                # 提取并发送底盘健康状态
                if 'chassis_alive' in parsed:
                    self.chassis_status_updated.emit(bool(parsed['chassis_alive']))
                # 提取并发送电压值（兼容性）
                if 'voltage' in parsed:
                    if parsed['voltage'] is not None:
                        try:
                            voltage = float(parsed['voltage'])
                            self.voltage_updated.emit(voltage)
                            # 高频打印降低级别或移除
                        except (ValueError, TypeError) as e:
                            self.error_aggregator.report_error(f"电压值格式错误", f"值: {parsed['voltage']}, {e}")
                    else:
                        logging.debug("[MQTT] 电压值为 None（可能未收到 /battery 消息）")
        elif topic == self.topics.get('voltage'):
            # 兼容旧版本（如果还有单独的 voltage topic）
            self.voltage_updated.emit(parsed)
        elif topic == self.topics.get('goal'):
            self.goal_updated.emit(parsed)
        elif topic == self.topics.get('initial_pose'):
            self.initialpose_updated.emit(parsed)
        elif topic == self.topics.get('map'):
            # 建图数据（压缩的 OccupancyGrid）
            logging.info(f"[MQTT] 收到 robot/map 消息，准备解析...")
            self._handle_map_message(parsed)
        elif topic == self.topics.get('scan'):
            # 激光数据
            if isinstance(parsed, dict):
                self.scan_updated.emit(parsed)
        elif topic == self.topics.get('odom'):
            # Odom 位姿（用于建图模式显示机器人位置）
            if isinstance(parsed, dict):
                self.odom_updated.emit(RobotPose.from_dict(parsed, default_source='odom'))
        elif topic == self.topics.get('path'):
            # Nav2 全局路径规划
            if isinstance(parsed, list):
                self.path_updated.emit(parsed)


    def _handle_map_message(self, data: dict):
        """处理并解压地图数据"""
        if not isinstance(data, dict):
            return
        
        try:
            width = data.get('width', 0)
            height = data.get('height', 0)
            resolution = data.get('resolution', 0.05)
            origin_x = data.get('origin_x', 0.0)
            origin_y = data.get('origin_y', 0.0)
            compressed = data.get('compressed', False)
            data_b64 = data.get('data', '')
            
            if not data_b64 or width == 0 or height == 0:
                return
            
            # 解码 Base64
            compressed_data = base64.b64decode(data_b64)
            
            # 解压
            if compressed:
                raw_data = zlib.decompress(compressed_data)
            else:
                raw_data = compressed_data
            
            # 转换为 numpy 数组（用于渲染）
            # 地图数据：255=未知, 0=空闲, 100=障碍
            map_array = np.frombuffer(raw_data, dtype=np.uint8).reshape((height, width))
            
            # 发送强类型信号
            map_data = MapMetadata(
                width=width,
                height=height,
                resolution=resolution,
                origin_x=origin_x,
                origin_y=origin_y,
                data=map_array
            )
            self.map_updated.emit(map_data)
            # logging.debug(f"[MQTT] 收到地图: {width}x{height}") # 避免海量刷屏

        except Exception as e:
            self.error_aggregator.report_error("解析地图数据失败", str(e))

    def close(self):
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception as e:
            logging.error(f"[MQTT] 关闭失败: {e}")
