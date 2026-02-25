import pytest
import math
import numpy as np
from src.core.models import RobotPose, MapMetadata

def test_robot_pose_from_dict_standard():
    data = {"x": 1.0, "y": 2.0, "z": 0.5, "yaw": math.pi / 2, "source": "amcl"}
    pose = RobotPose.from_dict(data)
    
    assert pose.x == 1.0
    assert pose.y == 2.0
    assert pose.z == 0.5
    assert pose.yaw == pytest.approx(math.pi / 2)
    assert pose.angle == pytest.approx(90.0)
    assert pose.source == "amcl"

def test_robot_pose_from_dict_missing_values():
    data = {"x": 5.0}
    pose = RobotPose.from_dict(data, default_source="odom")
    
    assert pose.x == 5.0
    assert pose.y == 0.0
    assert pose.yaw == 0.0
    assert pose.angle == 0.0
    assert pose.source == "odom"

def test_robot_pose_with_angle_instead_of_yaw():
    # Only providing angle in degrees
    data = {"angle": 180.0}
    pose = RobotPose.from_dict(data)
    
    assert pose.angle == 180.0
    assert pose.yaw == pytest.approx(math.pi)

def test_robot_pose_with_large_yaw_infers_angle():
    # sometimes yaw is mistakenly provided as degrees
    data = {"yaw": 180.0}
    pose = RobotPose.from_dict(data)
    
    assert pose.angle == 180.0
    assert pose.yaw == pytest.approx(math.pi)

def test_robot_pose_invalid_input():
    # If a non-dict is passed, it should return a default pose safely
    pose = RobotPose.from_dict(None)
    assert pose.x == 0.0
    assert pose.y == 0.0
    assert pose.yaw == 0.0

def test_map_metadata_from_dict():
    data = {
        "resolution": 0.02,
        "origin_x": -10.0,
        "width": 100,
        "height": 200,
        "data": np.zeros((200, 100))
    }
    meta = MapMetadata.from_dict(data)
    
    assert meta.resolution == 0.02
    assert meta.origin_x == -10.0
    assert meta.origin_y == 0.0
    assert meta.width == 100
    assert meta.height == 200
    assert isinstance(meta.data, np.ndarray)
