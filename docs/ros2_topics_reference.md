# Yahboom ROS 2 Humble 机器人话题参考

## 底盘启动后的话题 (yahboomcar_bringup)

| 话题名称 | 消息类型 | 说明 | 数据字段 |
|---------|---------|------|---------|
| `/battery` | `std_msgs/msg/UInt16` | 电池电压 | `data`: 电压值 (mV)，如 12000 = 12V |
| `/odom` | `nav_msgs/msg/Odometry` | 融合后的里程计 | `pose.pose.position.{x,y,z}`, `pose.pose.orientation.{x,y,z,w}`, `twist.twist.linear.{x,y,z}`, `twist.twist.angular.{x,y,z}` |
| `/odom_raw` | `nav_msgs/msg/Odometry` | 原始里程计数据 | 同上 |
| `/imu` | `sensor_msgs/msg/Imu` | IMU 传感器数据 | `orientation.{x,y,z,w}`, `angular_velocity.{x,y,z}`, `linear_acceleration.{x,y,z}` |
| `/imu/data` | `sensor_msgs/msg/Imu` | IMU 数据（处理后） | 同上 |
| `/scan` | `sensor_msgs/msg/LaserScan` | 激光雷达扫描 | `ranges[]`, `angle_min`, `angle_max`, `angle_increment`, `range_min`, `range_max` |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | 速度控制指令（订阅） | `linear.{x,y,z}`, `angular.{x,y,z}` |
| `/tf` | `tf2_msgs/msg/TFMessage` | 坐标变换 | `transforms[]` (frame 关系) |
| `/tf_static` | `tf2_msgs/msg/TFMessage` | 静态坐标变换 | 同上 |
| `/robot_description` | `std_msgs/msg/String` | URDF 机器人描述 | `data`: XML 字符串 |
| `/joint_states` | `sensor_msgs/msg/JointState` | 关节状态 | `name[]`, `position[]`, `velocity[]`, `effort[]` |
| `/diagnostics` | `diagnostic_msgs/msg/DiagnosticArray` | 诊断信息 | `status[]` |
| `/JoyState` | `sensor_msgs/msg/Joy` | 遥控器/手柄状态 | `axes[]`, `buttons[]` |
| `/joy` | `sensor_msgs/msg/Joy` | 手柄原始数据 | 同上 |
| `/beep` | `std_msgs/msg/UInt16` | 蜂鸣器控制 | `data`: 蜂鸣时长 (ms) |
| `/servo_s1` | `std_msgs/msg/UInt16` | 舵机1控制 | `data`: 角度 |
| `/servo_s2` | `std_msgs/msg/UInt16` | 舵机2控制 | `data`: 角度 |

## 建图模式话题 (Gmapping)

| 话题名称 | 消息类型 | 说明 | 数据字段 |
|---------|---------|------|---------|
| `/map` | `nav_msgs/msg/OccupancyGrid` | 2D 栅格地图 | `info.resolution`, `info.width`, `info.height`, `info.origin.position.{x,y,z}`, `data[]` (0=空闲, 100=障碍, -1=未知) |
| `/map_metadata` | `nav_msgs/msg/MapMetaData` | 地图元数据 | `resolution`, `width`, `height`, `origin` |

## 导航模式话题 (Navigation2)

| 话题名称 | 消息类型 | 说明 | 数据字段 |
|---------|---------|------|---------|
| `/amcl_pose` | `geometry_msgs/msg/PoseWithCovarianceStamped` | AMCL 定位位姿 | `pose.pose.position.{x,y,z}`, `pose.pose.orientation.{x,y,z,w}`, `pose.covariance[]` |
| `/initialpose` | `geometry_msgs/msg/PoseWithCovarianceStamped` | 初始位姿设置 | 同上 |
| `/goal_pose` | `geometry_msgs/msg/PoseStamped` | 导航目标点 | `pose.position.{x,y,z}`, `pose.orientation.{x,y,z,w}` |
| `/map` | `nav_msgs/msg/OccupancyGrid` | 导航使用的地图 | 同建图模式 |
| `/local_costmap/costmap` | `nav_msgs/msg/OccupancyGrid` | 局部代价地图 | 同上 |
| `/global_costmap/costmap` | `nav_msgs/msg/OccupancyGrid` | 全局代价地图 | 同上 |
| `/plan` | `nav_msgs/msg/Path` | 规划路径 | `poses[]` |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | 导航控制输出 | `linear.{x,y,z}`, `angular.{x,y,z}` |

---

## 消息类型详细结构

### std_msgs/msg/UInt16
```python
{
    "data": 12000  # uint16 值
}
```

### geometry_msgs/msg/Twist
```python
{
    "linear": {"x": 0.0, "y": 0.0, "z": 0.0},
    "angular": {"x": 0.0, "y": 0.0, "z": 0.0}
}
```

### nav_msgs/msg/Odometry
```python
{
    "header": {"stamp": {...}, "frame_id": "odom"},
    "child_frame_id": "base_link",
    "pose": {
        "pose": {
            "position": {"x": 0.0, "y": 0.0, "z": 0.0},
            "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
        },
        "covariance": [...]  # 36 元素数组
    },
    "twist": {
        "twist": {
            "linear": {"x": 0.0, "y": 0.0, "z": 0.0},
            "angular": {"x": 0.0, "y": 0.0, "z": 0.0}
        },
        "covariance": [...]
    }
}
```

### sensor_msgs/msg/Imu
```python
{
    "header": {...},
    "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
    "orientation_covariance": [...],  # 9 元素
    "angular_velocity": {"x": 0.0, "y": 0.0, "z": 0.0},
    "angular_velocity_covariance": [...],
    "linear_acceleration": {"x": 0.0, "y": 0.0, "z": 9.8}
}
```

### sensor_msgs/msg/LaserScan
```python
{
    "header": {...},
    "angle_min": -3.14,
    "angle_max": 3.14,
    "angle_increment": 0.01,
    "time_increment": 0.0,
    "scan_time": 0.1,
    "range_min": 0.1,
    "range_max": 12.0,
    "ranges": [...],  # 距离数组
    "intensities": [...]  # 强度数组（可选）
}
```

### nav_msgs/msg/OccupancyGrid
```python
{
    "header": {...},
    "info": {
        "map_load_time": {...},
        "resolution": 0.05,  # 米/像素
        "width": 384,
        "height": 384,
        "origin": {
            "position": {"x": -10.0, "y": -10.0, "z": 0.0},
            "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
        }
    },
    "data": [...]  # int8 数组: 0=空闲, 100=障碍, -1=未知
}
```

### geometry_msgs/msg/PoseWithCovarianceStamped (AMCL 位姿)
```python
{
    "header": {...},
    "pose": {
        "pose": {
            "position": {"x": 0.0, "y": 0.0, "z": 0.0},
            "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
        },
        "covariance": [...]  # 36 元素协方差矩阵
    }
}
```

### geometry_msgs/msg/PoseStamped (目标点)
```python
{
    "header": {"frame_id": "map"},
    "pose": {
        "position": {"x": 1.0, "y": 2.0, "z": 0.0},
        "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
    }
}
```

---

## 四元数与欧拉角转换

机器人朝向使用四元数 (x, y, z, w) 表示，转换为 yaw（偏航角）：

```python
import math

def quaternion_to_yaw(x, y, z, w):
    """四元数转 yaw 角（弧度）"""
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    return math.atan2(siny_cosp, cosy_cosp)

def yaw_to_quaternion(yaw):
    """yaw 角（弧度）转四元数"""
    return {
        "x": 0.0,
        "y": 0.0,
        "z": math.sin(yaw / 2.0),
        "w": math.cos(yaw / 2.0)
    }
```

---

## MQTT 桥接当前配置

当前 `mqtt_bridge_ros2.py` 桥接的话题：

| ROS 2 话题 | MQTT 话题 | 方向 | 说明 |
|-----------|----------|------|------|
| `/battery` | `robot/status` | ROS→MQTT | 电池电压 |
| `/odom_raw` | `robot/odom` | ROS→MQTT | 里程计位置 |
| `/amcl_pose` | `robot/pose` | ROS→MQTT | AMCL 定位位姿 |
| `/map` | `robot/map` | ROS→MQTT | 地图数据（压缩） |
| `/scan` | `robot/scan` | ROS→MQTT | 激光雷达（压缩） |
| `robot/cmd_vel` | `/cmd_vel` | MQTT→ROS | 速度控制 |
| `robot/goal` | `/goal_pose` | MQTT→ROS | 导航目标 |
| `robot/initial_pose` | `/initialpose` | MQTT→ROS | 初始位姿 |
