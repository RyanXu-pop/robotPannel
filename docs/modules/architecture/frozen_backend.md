# 冻结后端 API 清单

> **管辖 Agent：** 架构师 Agent
> **文档状态：** [FROZEN] — 以下所有接口在 UI Sprint 期间不可修改

---

## MqttAgent `[FROZEN]`

**文件：** `src/network/mqtt_agent.py`

### Signal 清单

| Signal | 参数类型 | 用途 |
|--------|---------|------|
| `pose_updated` | `RobotPose` | AMCL 定位位姿更新 |
| `odom_updated` | `RobotPose` | 里程计位姿更新 |
| `voltage_updated` | `float` | 电池电压更新 |
| `chassis_status_updated` | `bool` | 底盘存活状态 |
| `status_updated` | `dict` | 综合状态消息 |
| `connection_status` | `bool, str` | MQTT 连接状态 + 描述 |
| `goal_updated` | `dict` | 导航目标回传 |
| `initialpose_updated` | `dict` | 初始位姿回传 |
| `map_updated` | `MapMetadata` | 地图数据更新 |
| `scan_updated` | `dict` | 激光扫描数据 |
| `path_updated` | `list` | 全局路径规划 |
| `mqtt_error_aggregated` | `str` | 聚合错误消息 |

### 公开方法

| 方法签名 | 用途 |
|---------|------|
| `connect_broker(self)` | 连接 MQTT Broker |
| `update_connection(self, host: str, port: int)` | 更新连接参数 |
| `publish(self, topic_key: str, payload: dict) -> bool` | 发布消息 |
| `close(self)` | 关闭连接 |

### 辅助类：RosMsgAdapter `[FROZEN]`

| 方法签名 | 用途 |
|---------|------|
| `get_ros_type_by_topic(topic: str) -> Optional[str]` | Topic → ROS 类型映射 |
| `parse(topic: str, payload: str)` | 消息反序列化 |
| `serialize(topic: str, data)` | 消息序列化 |

---

## AsyncSSHManager `[FROZEN]`

**文件：** `src/network/async_ssh_manager.py`

| 方法签名 | 用途 |
|---------|------|
| `start_chassis_async(self) -> Tuple[bool, str]` | 启动底盘 |
| `stop_chassis_async(self)` | 停止底盘 |
| `start_gmapping_async(self) -> Tuple[bool, str]` | 启动 SLAM 建图 |
| `stop_gmapping_async(self)` | 停止建图 |
| `start_navigation_async(self) -> Tuple[bool, str]` | 启动导航 |
| `stop_navigation_async(self)` | 停止导航 |
| `save_map_async(self, map_name: str = "my_map") -> Tuple[bool, str]` | 保存地图 |
| `download_map_async(self, map_name: str, local_dir: str) -> Tuple[bool, str]` | 下载地图 |
| `upload_map_async(self, local_pgm_path: str, local_yaml_path: str) -> Tuple[bool, str]` | 上传地图 |
| `start_mqtt_bridge_async(self) -> Tuple[bool, str]` | 启动 MQTT Bridge |
| `stop_mqtt_bridge_async(self)` | 停止 MQTT Bridge |
| `close_async(self, stop_services: bool = True)` | 关闭所有连接 |

---

## Controllers `[FROZEN]`

### NavigationController

**文件：** `src/controllers/navigation_controller.py`

**Signal：** `status_message = Signal(str)`

| 方法签名 | 用途 |
|---------|------|
| `send_goal(self, x, y, affine_M_inv, robot_x, robot_y) -> Tuple[float, float, float]` | 下发导航目标 |
| `send_goal_angle(self, robot_x, robot_y, target_x, target_y, affine_M_inv) -> Tuple[float, float, float]` | 下发带角度目标 |
| `set_goal_pose(self, x, y, yaw, affine_M_inv) -> bool` | 设置目标位姿 |
| `publish_initial_pose(self, x, y, yaw) -> bool` | 发布初始位姿 |
| `set_initial_pose(self, x, y, yaw, affine_M_inv) -> bool` | 设置初始位姿 |
| `save_initial_pose(self, x_str, y_str, yaw_str) -> bool` | 保存初始位姿到文件 |
| `recall_initial_pose(self) -> Optional[dict]` | 从文件恢复初始位姿 |

### TeleopController

**文件：** `src/controllers/teleop_controller.py`

| 方法签名 | 用途 |
|---------|------|
| `handle_key_press(self, event) -> bool` | 处理键盘按下 |
| `handle_key_release(self, event) -> bool` | 处理键盘释放 |

### WorkflowController

**文件：** `src/controllers/workflow_controller.py`

**Signal：**
- `status_message = Signal(str)`
- `map_synced = Signal(str, str)`
- `workflow_finished = Signal(str, bool, str)`

| 方法签名 | 用途 |
|---------|------|
| `save_and_sync_map_async(self, map_name, local_maps_dir)` | 保存并同步地图 |
| `start_service_async(self, service_name)` | 启动服务 |
| `stop_service_async(self, service_name)` | 停止服务 |
| `execute_mapping_workflow(self)` | 建图工作流 |
| `execute_stop_mapping_workflow(self)` | 停止建图工作流 |
| `execute_navigation_workflow(self)` | 导航工作流 |
| `execute_stop_navigation_workflow(self)` | 停止导航工作流 |
| `execute_chassis_workflow(self)` | 底盘启动工作流 |
| `execute_mqtt_workflow(self)` | MQTT Bridge 启动工作流 |
| `execute_save_map_workflow(self)` | 保存地图工作流 |

### ServiceController

**文件：** `src/controllers/service_controller.py`

**Signal：**
- `status_message = Signal(str)`
- `show_info = Signal(str, str)`
- `show_error = Signal(str, str)`
- `show_warning = Signal(str, str)`
- `button_enable = Signal(str, bool)`
- `map_saved = Signal(str)`

| 方法签名 | 用途 |
|---------|------|
| `toggle_mqtt_async(self)` | 切换 MQTT 状态 |
| `toggle_chassis_async(self)` | 切换底盘状态 |
| `can_start_mapping(self) -> tuple[bool, str]` | 检查建图前置条件 |
| `toggle_mapping_async(self)` | 切换建图状态 |
| `can_start_navigation(self) -> tuple[bool, str]` | 检查导航前置条件 |
| `toggle_navigation_async(self)` | 切换导航状态 |
| `save_map_async(self, map_name, maps_dir, data_map_path)` | 保存地图 |
| `download_map_async(self, map_name, local_dir)` | 下载地图 |
| `upload_map_async(self, pgm_path, yaml_path)` | 上传地图 |

### MapManager

**文件：** `src/controllers/map_manager.py`

| 方法签名 | 用途 |
|---------|------|
| `load(self, yaml_path: str) -> bool` | 加载地图文件 |
| `reload_display(self, map_png_path, map_yaml_path=None) -> bool` | 刷新地图显示 |
| `update_origin(self, new_x, new_y) -> bool` | 更新地图原点 |
| `rotate_coords(x, y, angle, ...) [static]` | 坐标旋转 |
| `inverse_rotate_coords(x, y, angle, ...) [static]` | 坐标逆旋转 |
| `calc_direction_angle(x1, y1, x2, y2) [static]` | 计算方向角 |

### PoseRecorder

**文件：** `src/controllers/pose_recorder.py`

**Signal：** `status_message = Signal(str)`

| 方法签名 | 用途 |
|---------|------|
| `start(self) -> None` | 开始记录 |
| `stop(self) -> bool` | 停止并导出 |
| `append(self, x, y, z, angle) -> None` | 追加位姿点 |
| `format_current(self, last_data, affine_M) -> Optional[str]` | 格式化当前位姿 |

---

## RobotStateHub (Store) `[FROZEN]`

**文件：** `src/ui_v2/robot_state_hub.py`

### Signal 清单

| Signal | 参数类型 | 用途 |
|--------|---------|------|
| `voltage_changed` | `float, float` | 电压 + 百分比 |
| `chassis_alive_changed` | `bool` | 底盘存活状态 |
| `robot_pose_changed` | `RobotPose` | 机器人位姿 |
| `laser_scan_changed` | `dict` | 激光扫描数据 |
| `global_path_changed` | `list` | 全局路径 |
| `map_data_changed` | `MapMetadata` | 地图数据 |
| `mapping_state_changed` | `bool` | 建图状态 |
| `navigation_state_changed` | `bool` | 导航状态 |
| `workflow_message` | `str` | 工作流消息广播 |

### 公开方法

| 方法签名 | 用途 |
|---------|------|
| `update_voltage(self, voltage: float)` | 更新电压 |
| `update_chassis_status(self, is_alive: bool)` | 更新底盘状态 |
| `update_robot_pose(self, pose: RobotPose)` | 更新位姿 |
| `update_scan(self, scan_data: dict)` | 更新激光数据 |
| `update_path(self, path: list)` | 更新路径 |
| `update_map(self, map_meta: MapMetadata)` | 更新地图 |
| `set_mapping_running(self, running: bool)` | 设置建图状态 |
| `set_navigation_running(self, running: bool)` | 设置导航状态 |
| `broadcast_message(self, msg: str)` | 广播消息 |

### 属性

| 属性 | 类型 | 用途 |
|------|------|------|
| `mapping_running` | `bool` | 建图是否运行中 |
| `navigation_running` | `bool` | 导航是否运行中 |
| `current_pose` | `Optional[RobotPose]` | 当前位姿 |

---

## Models `[FROZEN]`

**文件：** `src/core/models.py`

### RobotPose (dataclass)

| 字段 | 类型 | 默认值 |
|------|------|--------|
| `x` | `float` | `0.0` |
| `y` | `float` | `0.0` |
| `z` | `float` | `0.0` |
| `yaw` | `float` | `0.0` |
| `angle` | `float` | `0.0` |
| `source` | `str` | `""` |

类方法：`from_dict(cls, data: dict, default_source: str = "") -> RobotPose`

### MapMetadata (dataclass)

| 字段 | 类型 | 默认值 |
|------|------|--------|
| `resolution` | `float` | `0.05` |
| `origin_x` | `float` | `0.0` |
| `origin_y` | `float` | `0.0` |
| `width` | `int` | `0` |
| `height` | `int` | `0` |
| `data` | `Optional[Any]` | `None` |

类方法：`from_dict(cls, data: dict) -> MapMetadata`

### SystemState (Enum)

`OFFLINE` | `IDLE` | `MAPPING` | `NAVIGATING`

### AppSystemState `[FROZEN]`

**Signal：** `state_changed`, `mqtt_changed`, `chassis_changed`, `mapping_changed`, `navigation_changed`

| 方法/属性 | 用途 |
|---------|------|
| `set_state(self, new_state: SystemState)` | 切换系统状态 |
| `current_state` (property) | 当前状态 |
| `mapping_running` (property) | 建图运行中 |
| `navigation_running` (property) | 导航运行中 |
| `mqtt_running` (property) | MQTT 运行中 |
| `chassis_running` (property) | 底盘运行中 |

### ErrorAggregator `[FROZEN]`

**Signal：** `error_flushed = Signal(str)`

| 方法签名 | 用途 |
|---------|------|
| `report_error(self, error_key: str, error_detail: str = "")` | 上报错误 |
| `flush(self)` | 刷出聚合错误 |

---

*标注 `[FROZEN]` 的接口在 UI Sprint 期间不可修改。如需变更，须先更新本文档并经架构评审。*
