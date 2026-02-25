# utils.py
import numpy as np
import logging
from typing import Optional, List, Tuple
from collections import OrderedDict

def convert_to_float(item: str) -> Optional[float]:
    """将字符串转换为浮点数"""
    try:
        return float(item)
    except (ValueError, TypeError):
        logging.warning(f"无法将 '{item}' 转换为浮点数")
        return None

def compute_affine_transform(src_points: List[Tuple[float, float]], 
                          dst_points: List[Tuple[float, float]]) -> np.ndarray:
    """计算仿射变换矩阵"""
    if len(src_points) < 3 or len(dst_points) < 3:
        raise ValueError("至少需要3组点对来计算仿射变换")
    A = []
    B = []
    for (x, y), (u, v) in zip(src_points, dst_points):
        A.append([x, y, 1, 0, 0, 0])
        A.append([0, 0, 0, x, y, 1])
        B.extend([u, v])
    A = np.array(A, dtype=np.float64)
    B = np.array(B, dtype=np.float64)
    try:
        params = np.linalg.lstsq(A, B, rcond=None)[0]
    except np.linalg.LinAlgError:
        raise ValueError("无法计算仿射变换矩阵，点可能共线或配置不当")
    return np.array([
        [params[0], params[1], params[2]],
        [params[3], params[4], params[5]],
        [0, 0, 1]
    ], dtype=np.float64)

def compute_inverse_affine_transform(M: np.ndarray) -> np.ndarray:
    """计算逆仿射变换矩阵"""
    try:
        return np.linalg.inv(M)
    except np.linalg.LinAlgError:
        raise ValueError("矩阵不可逆，无法计算逆变换")

def apply_affine_transform(M: np.ndarray, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """应用仿射变换到点集"""
    points_hom = np.array([(x, y, 1) for x, y in points], dtype=np.float64).T
    transformed = M @ points_hom
    return [(x, y) for x, y, _ in transformed.T]


class BoundedCache(OrderedDict):
    """dict子类，限制最大条目数，防止长期运行内存无限增长。"""
    def __init__(self, maxsize: int = 500):
        super().__init__()
        self._maxsize = maxsize
        self._keys_order: List[Tuple] = []

    def __setitem__(self, key, value):
        if key not in self:
            if len(self) >= self._maxsize:
                oldest = self._keys_order.pop(0)
                super().__delitem__(oldest)
            self._keys_order.append(key)
        super().__setitem__(key, value)

