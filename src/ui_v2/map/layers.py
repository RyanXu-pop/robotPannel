import math
import numpy as np
from typing import Optional, List, Dict
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPathItem, QGraphicsObject, QGraphicsPixmapItem
from PySide6.QtCore import QRectF, QPointF, Qt, Property, QPropertyAnimation
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPixmap, QImage, QTransform

from src.core.models import MapMetadata

class GridLayer(QGraphicsObject):
    """全局栅格背景层"""
    def __init__(self, size: float = 1.0, color: str = "#333333"):
        super().__init__()
        self.grid_size = size
        self.color = QColor(color)
        self.setZValue(-10)  # 最底层

    def boundingRect(self) -> QRectF:
        # 提供一个极大的边界以覆盖默认视野
        return QRectF(-100, -100, 200, 200)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setPen(QPen(self.color, 0.05))
        rect = option.exposedRect
        x_start = math.floor(rect.left() / self.grid_size) * self.grid_size
        y_start = math.floor(rect.top() / self.grid_size) * self.grid_size
        
        # 绘制垂线
        x = x_start
        while x < rect.right():
            painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
            x += self.grid_size
            
        # 绘制水平线
        y = y_start
        while y < rect.bottom():
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            y += self.grid_size


class OccupancyMapLayer(QGraphicsPixmapItem):
    """占据栅格地图层 (处理 nav_msgs/OccupancyGrid 或加载的静态图)"""
    def __init__(self):
        super().__init__()
        self.setZValue(0)
        self._resolution = 0.05
        self._origin_x = 0.0
        self._origin_y = 0.0

    def set_map_data(self, map_meta: MapMetadata):
        """将 MapMetadata 或本地图像刷新上来"""
        if map_meta.data is None:
            return
            
        self._resolution = map_meta.resolution
        self._origin_x = map_meta.origin_x
        self._origin_y = map_meta.origin_y
        
        w, h = map_meta.width, map_meta.height
        data = np.asarray(map_meta.data)
        
        # 判断是来自 Mqtt 的一维 OccupancyGrid，还是来自本地加载的三维彩色图像
        if data.ndim == 1:
            data = data.reshape((h, w))
            img_data = np.full((h, w, 4), [128, 128, 128, 255], dtype=np.uint8)
            img_data[data == 0] = [255, 255, 255, 255]
            img_data[data == 100] = [0, 0, 0, 255]
            # ROS 地图倒置处理
            img_data = np.flipud(img_data)
        else:
            # 本地图片 (h, w, c)，通常来自 mpimg.imread (0.0~1.0 float 或 0-255 int)
            if data.dtype == np.float32 or data.dtype == np.float64:
                img_data = (data * 255).astype(np.uint8)
            else:
                img_data = data.astype(np.uint8)
                
            # 兼容 2D 灰度图 (h, w)
            if img_data.ndim == 2:
                img_data = np.stack((img_data,)*3, axis=-1)
                
            # 确保是 RGBA
            if img_data.shape[2] == 3:
                alpha = np.full((h, w, 1), 255, dtype=np.uint8)
                img_data = np.concatenate((img_data, alpha), axis=2)
            # 本地图像是直接对应坐标的，通过 map.yaml 配置加载，也必须统一翻转规则
            img_data = np.flipud(img_data)

        # 确保在使用前是一个 C-contiguous 的阵列，否则 QImage 构造函数会抛出 BufferError
        img_data = np.ascontiguousarray(img_data)

        
        qimage = QImage(img_data.data, w, h, w * 4, QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimage)
        self.setPixmap(pixmap)
        
        # 应用缩放和偏移将像素坐标转为世界坐标 (米)
        transform = QTransform().scale(self._resolution, self._resolution)
        self.setTransform(transform)
        # origin_y 在图片左下角，翻转后要减去实际高度
        self.setPos(self._origin_x, self._origin_y)


class PathLayer(QGraphicsObject):
    """全局路径渲染层"""
    def __init__(self, color: str = "#00ff00", width: float = 0.05):
        super().__init__()
        self.path_points: List[dict] = []
        self.pen = QPen(QColor(color), width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        self.setZValue(1)

    def set_path(self, path: List[dict]):
        self.path_points = path
        self.update()

    def boundingRect(self) -> QRectF:
        if not self.path_points:
            return QRectF(0, 0, 0, 0)
        min_x = min(p["x"] for p in self.path_points)
        max_x = max(p["x"] for p in self.path_points)
        min_y = min(p["y"] for p in self.path_points)
        max_y = max(p["y"] for p in self.path_points)
        # 添加一些边距
        margin = 0.5
        return QRectF(min_x - margin, -(max_y + margin), max_x - min_x + 2*margin, max_y - min_y + 2*margin)

    def paint(self, painter: QPainter, option, widget=None):
        if len(self.path_points) < 2:
            return
        painter.setPen(self.pen)
        # 由于视角的 Y 向上，我们需要将传递的世界 Y 坐标的反转（由 MapView 最终矩阵管理，此处原样画）
        # 这里为了配合 QGraphicsScene 默认的 Y 向下，可以统一在 MapGraphicsView 内部做 scale(1, -1)
        for i in range(len(self.path_points) - 1):
            p1 = QPointF(self.path_points[i]["x"], self.path_points[i]["y"])
            p2 = QPointF(self.path_points[i+1]["x"], self.path_points[i+1]["y"])
            painter.drawLine(p1, p2)


class LidarLayer(QGraphicsObject):
    """雷达点云渲染层"""
    def __init__(self):
        super().__init__()
        self.points: List[QPointF] = []
        self.pen = QPen(QColor(255, 0, 0, 200), 0.05)
        self.setZValue(2)
        # Lidar 数据相对于机器人，所以需要绑定到机器人的 transform 上
        # 这里简化处理：直接绘制相对于机器人的坐标，然后在 View 中让 LidarLayer 跟随 RobotItem

    def set_scan(self, scan_data: dict, robot_x: float, robot_y: float, robot_yaw: float):
        """传入 scan 数据及机器人当前世界坐标以计算绝对点云"""
        self.points.clear()
        if not scan_data:
            self.update()
            return

        angle_min = scan_data.get("angle_min", 0.0)
        angle_increment = scan_data.get("angle_increment", 0.0)
        ranges = scan_data.get("ranges", [])
        
        for i, r in enumerate(ranges):
            # 忽略 NaN 和极远值
            if r is None or math.isnan(r) or r <= 0.05 or r > 20.0:
                continue
            
            # 当前射线的绝对角度 = 机器人朝向角 + 雷达局部角度
            angle = robot_yaw + angle_min + i * angle_increment
            
            # 极坐标转直角坐标 (世界坐标系)
            px = robot_x + r * math.cos(angle)
            py = robot_y + r * math.sin(angle)
            self.points.append(QPointF(px, py))
            
        import logging
        if len(self.points) > 0 and getattr(self, '_log_counter', 0) % 20 == 0:
            logging.info(f"[诊断 UI] 成功重绘雷达点云，包含 {len(self.points)} 个有效点")
        self._log_counter = getattr(self, '_log_counter', 0) + 1
            
        self.update()

    def boundingRect(self) -> QRectF:
        if not self.points:
            return QRectF()
        xs = [p.x() for p in self.points]
        ys = [p.y() for p in self.points]
        return QRectF(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))

    def paint(self, painter: QPainter, option, widget=None):
        painter.setPen(self.pen)
        painter.drawPoints(self.points)


class RobotItem(QGraphicsObject):
    """小车模型层, 带有 Apple Maps 风格的呼吸脉冲定位特效"""
    def __init__(self, size: float = 0.5):
        super().__init__()
        self.size = size
        self.setZValue(10)
        
        # 机器人基准尺寸属性
        self.radius = size / 2
        
        # 脉冲动画属性初始化
        self._pulse_radius = self.radius * 1.5
        
        # 创建无限循环的呼吸动画
        self.anim = QPropertyAnimation(self, b"pulseRadius")
        self.anim.setDuration(2000) # 2秒一个呼吸周期
        self.anim.setStartValue(self.radius * 1.2)
        self.anim.setEndValue(self.radius * 4.0)
        self.anim.setLoopCount(-1) # 无限循环
        self.anim.start()

    @Property(float)
    def pulseRadius(self) -> float:
        return self._pulse_radius
        
    @pulseRadius.setter
    def pulseRadius(self, val: float):
        self._pulse_radius = val
        self.update() # 触发重绘

    def boundingRect(self) -> QRectF:
        # 包围盒必须能够容纳最大的脉冲光圈，否则会被裁剪
        max_pulse = self.radius * 4.5
        return QRectF(-max_pulse, -max_pulse, max_pulse * 2, max_pulse * 2)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. 动态脉冲光环 (Pulsating Aura)
        # 根据当前半径计算渐变透明度（圆越大越透明）
        progress = (self._pulse_radius - (self.radius * 1.2)) / (self.radius * 4.0 - self.radius * 1.2)
        progress = max(0.0, min(1.0, progress))
        alpha = int(120 * (1.0 - progress)) # 初始透明度最大 120
        
        painter.setBrush(QColor(0, 122, 204, alpha))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(0, 0), self._pulse_radius, self._pulse_radius)
        
        # 2. 固有的外圈高亮投影 (更小、更真实的底盘发光)
        painter.setBrush(QColor(0, 122, 204, 60))
        painter.drawEllipse(QPointF(0, 0), self.radius * 1.2, self.radius * 1.2)

        # 2. 绘制醒目的方向小车体 (一个尖端朝右正X方向的流线型三角形)
        # 车尾扁平，车头尖锐
        painter.setBrush(QBrush(QColor("#007acc"))) # 深蓝色车身
        painter.setPen(QPen(Qt.white, 0.03, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        
        from PySide6.QtGui import QPolygonF
        poly = QPolygonF([
            QPointF(self.radius * 1.5, 0),                # 车头尖端 (指向X正半轴)
            QPointF(-self.radius * 0.8, -self.radius),    # 左后方
            QPointF(-self.radius * 0.4, 0),               # 尾部内凹
            QPointF(-self.radius * 0.8, self.radius)      # 右后方
        ])
        painter.drawPolygon(poly)
        
        # 3. 车顶的激光雷达模拟盖子（小圆）
        painter.setBrush(QBrush(QColor("#111111")))
        painter.setPen(QPen(QColor("#333333"), 0.01))
        painter.drawEllipse(QPointF(0, 0), self.radius * 0.4, self.radius * 0.4)


class ArrowItem(QGraphicsObject):
    """用于表示交互拖拽的带箭头的线段层"""
    def __init__(self, color: str = "#FF9600"):
        super().__init__()
        self.p1 = QPointF(0, 0)
        self.p2 = QPointF(0, 0)
        self._color = QColor(color)
        self.setZValue(20)

    def setLine(self, x1, y1, x2, y2):
        self.p1 = QPointF(x1, y1)
        self.p2 = QPointF(x2, y2)
        self.update()

    def boundingRect(self) -> QRectF:
        x_min = min(self.p1.x(), self.p2.x())
        x_max = max(self.p1.x(), self.p2.x())
        y_min = min(self.p1.y(), self.p2.y())
        y_max = max(self.p1.y(), self.p2.y())
        margin = 0.5
        return QRectF(x_min - margin, y_min - margin, x_max - x_min + 2*margin, y_max - y_min + 2*margin)

    def paint(self, painter: QPainter, option, widget=None):
        # 如果长度为 0 则不绘制
        dx = self.p2.x() - self.p1.x()
        dy = self.p2.y() - self.p1.y()
        length = math.hypot(dx, dy)
        if length < 0.05:
            return

        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制主线
        main_pen = QPen(self._color, 0.05, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(main_pen)
        painter.drawLine(self.p1, self.p2)
        
        # 绘制箭头 (填充的多边形)
        angle = math.atan2(dy, dx)
        arrow_size = 0.3
        
        # 箭头两个背角点
        arrow_p1 = self.p2 - QPointF(math.cos(angle + math.pi/6) * arrow_size,
                                     math.sin(angle + math.pi/6) * arrow_size)
        arrow_p2 = self.p2 - QPointF(math.cos(angle - math.pi/6) * arrow_size,
                                     math.sin(angle - math.pi/6) * arrow_size)
                                     
        from PySide6.QtGui import QPolygonF
        polygon = QPolygonF([self.p2, arrow_p1, arrow_p2])
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self._color))
        painter.drawPolygon(polygon)

