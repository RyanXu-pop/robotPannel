import pytest
import math
import numpy as np

# Need to adjust import path since tests is a subdirectory
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.controllers.map_manager import MapManager

def test_rotate_coords():
    # Rotate (1, 0) by 90 degrees around origin (0, 0)
    x, y = MapManager.rotate_coords(1.0, 0.0, 90.0, origin_x=0.0, origin_y=0.0)
    assert x == pytest.approx(0.0, abs=1e-5)
    assert y == pytest.approx(1.0, abs=1e-5)

def test_rotate_coords_with_origin():
    # Rotate (2, 1) by 90 degrees around origin (1, 1)
    # Relative point: (1, 0). Rotated relative point: (0, 1). Absolute: (1, 2)
    x, y = MapManager.rotate_coords(2.0, 1.0, 90.0, origin_x=1.0, origin_y=1.0)
    assert x == pytest.approx(1.0, abs=1e-5)
    assert y == pytest.approx(2.0, abs=1e-5)

def test_inverse_rotate_coords():
    # Inverse rotate (0, 1) by angle 90 -> should go back to (1, 0)
    x, y = MapManager.inverse_rotate_coords(0.0, 1.0, 90.0, origin_x=0.0, origin_y=0.0)
    assert x == pytest.approx(1.0, abs=1e-5)
    assert y == pytest.approx(0.0, abs=1e-5)

def test_calc_direction_angle():
    # Pointing straight up (0, 0) -> (0, 1) should be 90 degrees
    angle = MapManager.calc_direction_angle(0.0, 0.0, 0.0, 1.0)
    assert angle == pytest.approx(90.0)
    
    # Pointing straight left (0, 0) -> (-1, 0) should be 180 degrees
    angle = MapManager.calc_direction_angle(0.0, 0.0, -1.0, 0.0)
    assert angle == pytest.approx(180.0)
    
    # Pointing bottom-right (0, 0) -> (1, -1) should be -45 degrees
    angle = MapManager.calc_direction_angle(0.0, 0.0, 1.0, -1.0)
    assert angle == pytest.approx(-45.0)
