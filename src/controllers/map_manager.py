# map_manager.py
# -*- coding: utf-8 -*-
"""
MapManager — 地图管理模块

负责地图的加载、缓存、原点更新和坐标变换。
从 MyMainWindow 中提取，减少 God Class 的职责。
"""

import os
import logging
import yaml
import numpy as np
import matplotlib.image as mpimg
from scipy.ndimage import rotate
from typing import Dict, Any, Optional, List, Tuple

from src.core.constants import PATHS_CONFIG


class MapManager:
    """
    封装与地图文件 I/O 和坐标变换相关的所有操作。

    属性:
        map_data:         当前加载的地图数据字典 {resolution, origin, image, extent}
        cached_map:       旋转后的地图缓存（numpy 数组）
        map_bounds:       [x_min, x_max, y_min, y_max]
        map_rotation:     地图显示旋转角度（度）
        transform_cache:  BoundedCache，坐标变换的 LRU 缓存
    """

    def __init__(self, map_bounds: List[float], map_rotation: float = 0.0,
                 transform_cache=None):
        """
        Args:
            map_bounds:      初始地图边界 [x_min, x_max, y_min, y_max]
            map_rotation:    地图旋转角度（度）
            transform_cache: 可选的外部 BoundedCache 实例；None 则新建空 dict
        """
        self.map_data: Optional[Dict[str, Any]] = None
        self.cached_map: Optional[np.ndarray] = None
        self.map_bounds: List[float] = list(map_bounds)
        self.map_rotation: float = map_rotation
        self.transform_cache = transform_cache if transform_cache is not None else {}

    # ------------------------------------------------------------------ #
    # 地图加载
    # ------------------------------------------------------------------ #

    def load(self, yaml_path: str) -> bool:
        """
        从 YAML + 图片文件加载地图数据。

        策略：
        - 从 YAML 读取 resolution / origin
        - 优先使用 PNG，如 PNG 不存在则尝试从 PGM 自动转换

        Returns:
            True 表示加载成功，False 表示失败（self.map_data 置 None）
        """
        try:
            yaml_dir = os.path.dirname(yaml_path)

            with open(yaml_path, 'r') as f:
                map_config = yaml.safe_load(f)

            resolution = map_config['resolution']
            origin = map_config['origin']

            image_name = map_config.get('image', '')
            base_name = os.path.splitext(image_name)[0]

            png_path = os.path.join(yaml_dir, f"{base_name}.png")
            pgm_path = os.path.join(yaml_dir, f"{base_name}.pgm")

            if os.path.exists(png_path):
                map_image_path = png_path
            elif os.path.exists(pgm_path):
                try:
                    from PIL import Image
                    img = Image.open(pgm_path)
                    img.save(png_path)
                    logging.info(f"[MapManager] 已自动转换 PGM → PNG: {png_path}")
                    map_image_path = png_path
                except Exception as e:
                    logging.warning(f"[MapManager] PGM 转 PNG 失败，尝试直接读取 PGM: {e}")
                    map_image_path = pgm_path
            else:
                map_image_path = os.path.join(yaml_dir, image_name)

            map_img = mpimg.imread(map_image_path)

            self.map_data = {
                "resolution": resolution,
                "origin": origin,
                "image": map_img,
                "extent": self.map_bounds,
            }
            self.cached_map = rotate(map_img, self.map_rotation, reshape=False)
            logging.info(f"[MapManager] 地图加载成功: {map_image_path}, 形状={map_img.shape}")
            return True

        except (FileNotFoundError, KeyError, TypeError) as e:
            logging.error(f"[MapManager] 地图数据加载失败: {e}")
            self.map_data = None
            self.cached_map = None
            return False

    def reload_display(self, map_png_path: str, map_yaml_path: str = None) -> bool:
        """
        从已有 PNG（和可选的 YAML）重新加载地图显示数据，
        典型用于「保存建图结果 → 同步前端」场景。

        Returns:
            True 表示加载成功
        """
        try:
            map_img = mpimg.imread(map_png_path)
            if map_img is None:
                logging.error(f"[MapManager] 无法加载地图: {map_png_path}")
                return False

            # 统一为 RGB u8
            if len(map_img.shape) == 2:
                map_img = np.stack([map_img] * 3, axis=-1)
            elif map_img.shape[2] == 4:
                map_img = map_img[:, :, :3]
            if map_img.dtype in (np.float32, np.float64):
                map_img = (map_img * 255).astype(np.uint8)

            resolution = 0.05
            origin = [0, 0, 0]

            if map_yaml_path and os.path.exists(map_yaml_path):
                with open(map_yaml_path, 'r') as f:
                    info = yaml.safe_load(f)
                    resolution = info.get('resolution', 0.05)
                    origin = info.get('origin', [0, 0, 0])
                    logging.info(f"[MapManager] 地图参数: resolution={resolution}, origin={origin}")

            height, width = map_img.shape[:2]
            x_min = origin[0]
            y_min = origin[1]
            x_max = x_min + width * resolution
            y_max = y_min + height * resolution

            self.map_bounds = [x_min, x_max, y_min, y_max]
            self.map_data = {
                "resolution": resolution,
                "origin": origin,
                "image": map_img,
                "extent": self.map_bounds,
            }
            self.cached_map = rotate(map_img, self.map_rotation, reshape=False)
            logging.info(f"[MapManager] 地图已重新加载: {map_png_path}, 大小={map_img.shape}")
            return True

        except Exception as e:
            logging.error(f"[MapManager] 重新加载地图失败: {e}")
            return False

    def update_origin(self, new_x: float, new_y: float) -> bool:
        """
        更新地图原点：修改内存数据 + 写回 YAML 文件 + 重新加载。

        Returns:
            True 表示更新成功
        """
        if not self.map_data:
            logging.warning("[MapManager] update_origin: map_data 尚未加载")
            return False
        try:
            old_origin = self.map_data["origin"]
            self.map_data["origin"] = [new_x, new_y, 0.0]

            yaml_path = PATHS_CONFIG['map_yaml']
            try:
                with open(yaml_path, 'r') as f:
                    existing = yaml.safe_load(f) or {}
            except Exception:
                existing = {}

            map_config = {
                'image': existing.get('image', os.path.basename(
                    PATHS_CONFIG.get('map_image', 'map.png'))),
                'resolution': existing.get('resolution', self.map_data.get('resolution', 0.05)),
                'origin': [new_x, new_y, 0.0],
                'negate': existing.get('negate', 0),
                'occupied_thresh': existing.get('occupied_thresh', 0.65),
                'free_thresh': existing.get('free_thresh', 0.196),
            }
            with open(yaml_path, 'w') as f:
                yaml.dump(map_config, f, default_flow_style=False, sort_keys=False)

            # 重新加载以同步所有组件
            self.load(yaml_path)
            logging.info(f"[MapManager] 地图原点已更新: {old_origin} → [{new_x}, {new_y}, 0.0]")
            return True

        except Exception as e:
            logging.error(f"[MapManager] 更新地图原点失败: {e}")
            return False

    # ------------------------------------------------------------------ #
    # 坐标变换工具
    # ------------------------------------------------------------------ #

    @staticmethod
    def rotate_coords(x: float, y: float, angle: float,
                      origin_x: float = 0.0, origin_y: float = 0.0) -> Tuple[float, float]:
        """绕指定原点旋转坐标（`angle` 为度，逆时针为正）。"""
        angle_rad = np.deg2rad(angle)
        xs = x - origin_x
        ys = y - origin_y
        new_x = xs * np.cos(angle_rad) - ys * np.sin(angle_rad) + origin_x
        new_y = xs * np.sin(angle_rad) + ys * np.cos(angle_rad) + origin_y
        return new_x, new_y

    @staticmethod
    def inverse_rotate_coords(x: float, y: float, angle: float,
                              origin_x: float = 0.0, origin_y: float = 0.0) -> Tuple[float, float]:
        """逆旋转：等价于以 -angle 调用 rotate_coords。"""
        return MapManager.rotate_coords(x, y, -angle, origin_x, origin_y)

    @staticmethod
    def calc_direction_angle(x1: float, y1: float, x2: float, y2: float) -> float:
        """计算从 (x1, y1) 到 (x2, y2) 的朝向角（度）。"""
        return np.degrees(np.arctan2(y2 - y1, x2 - x1))
