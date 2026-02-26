# UI Signal 契约清单

> **管辖 Agent：** 架构师 Agent
> **文档状态：** [FROZEN] — 这些 Signal 是 UI 与 Controller 的接口契约，视觉重构时不可碰

---

## ControlPanel

**文件：** `src/ui_v2/panels/control_panel.py`
**类名：** `ControlPanel(QWidget)`

| Signal | 参数 | 触发场景 |
|--------|------|---------|
| `sig_start_mapping` | — | 点击开始建图 |
| `sig_stop_mapping` | — | 点击停止建图 |
| `sig_save_map` | — | 点击保存地图 |
| `sig_start_navigation` | — | 点击开始导航 |
| `sig_stop_navigation` | — | 点击停止导航 |
| `sig_set_initial_pose` | — | 点击设置初始位姿（地图交互模式） |
| `sig_set_goal_pose` | — | 点击设置目标点（地图交互模式） |
| `sig_manual_initial_pose` | `float, float, float` | 手动输入初始位姿 |
| `sig_manual_goal` | `float, float, float` | 手动输入目标点 |
| `sig_start_chassis` | — | 点击启动底盘 |
| `sig_start_mqtt_node` | — | 点击启动 MQTT Bridge |
| `sig_download_map` | — | 点击下载地图 |
| `sig_upload_map` | — | 点击上传地图 |
| `sig_save_initial_pose` | — | 点击保存初始位姿 |
| `sig_recall_initial_pose` | — | 点击恢复初始位姿 |

**共 15 个 Signal**

---

## PoseRecordPanel

**文件：** `src/ui_v2/panels/pose_panel.py`
**类名：** `PoseRecordPanel(QWidget)`

| Signal | 参数 | 触发场景 |
|--------|------|---------|
| `height_changed` | `int` | 面板高度变化 |
| `sig_start_trace` | — | 点击开始轨迹记录 |
| `sig_stop_trace` | — | 点击停止轨迹记录 |
| `sig_record_point` | — | 点击记录当前点 |
| `sig_go_to_selected` | `float, float, float` | 点击前往选中位姿 |

**共 5 个 Signal**

---

## TeleopPanel

**文件：** `src/ui_v2/panels/teleop_panel.py`
**类名：** `TeleopPanel(QWidget)`

| Signal | 参数 | 触发场景 |
|--------|------|---------|
| `height_changed` | `int` | 面板高度变化 |

**共 1 个 Signal**

---

## UnifiedDrawer

**文件：** `src/ui_v2/panels/unified_drawer.py`
**类名：** `UnifiedDrawer(QWidget)`

| Signal | 参数 | 触发场景 |
|--------|------|---------|
| `height_changed` | `int` | 抽屉高度变化 |

**共 1 个 Signal**

---

## TelemetryPanel

**文件：** `src/ui_v2/panels/telemetry_panel.py`
**类名：** `TelemetryPanel(QWidget)`

无自定义 Signal（仅订阅 RobotStateHub 的 Signal 用于显示）。

---

## MapGraphicsView

**文件：** `src/ui_v2/map/map_view.py`
**类名：** `MapGraphicsView(QGraphicsView)`

| Signal | 参数 | 触发场景 |
|--------|------|---------|
| `interaction_triggered` | `float, float, float, str` | 地图交互（点击/拖拽设定目标或初始位姿） |

**共 1 个 Signal**

---

## Map Layers

**文件：** `src/ui_v2/map/layers.py`

以下图层类均无自定义 Signal：

| 类名 | 父类 | 用途 |
|------|------|------|
| `GridLayer` | `QGraphicsObject` | 背景网格 |
| `OccupancyMapLayer` | `QGraphicsPixmapItem` | 占据栅格地图 |
| `PathLayer` | `QGraphicsObject` | 导航路径渲染 |
| `LidarLayer` | `QGraphicsObject` | 激光点云渲染 |
| `RobotItem` | `QGraphicsObject` | 机器人图标 |
| `ArrowItem` | `QGraphicsObject` | 方向箭头 |

---

## UI-Only Sprint 规则

视觉重构时，对以上所有 Signal：

1. **不可删除** — 任何 `sig_xxx` 或 `height_changed` 定义
2. **不可修改签名** — 参数类型和数量不可变
3. **不可修改 connect()** — Signal 与 Controller/Store 的连接逻辑不可碰
4. **可以修改** — 发射 Signal 的 UI 控件的视觉属性（样式、布局、动画）

---

*本清单从代码库自动归档。如需新增 Signal，须先更新本文档。*
