import sys
import os
import pytest
from unittest.mock import MagicMock
import numpy as np

# Need to adjust import path since tests is a subdirectory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.controllers.navigation_controller import NavigationController

@pytest.fixture
def mock_mqtt():
    return MagicMock()

@pytest.fixture
def nav_ctrl(mock_mqtt):
    return NavigationController(mqtt_agent=mock_mqtt)

def test_send_goal(nav_ctrl, mock_mqtt):
    # Setup affine_M_inv as identity matrix for simplicity
    affine_M_inv = np.eye(3)
    
    # Send goal to (10, 10), current robot is at (0, 0)
    # The dx, dy is (10, 10), so yaw should be 45 degrees
    rx, ry, yaw = nav_ctrl.send_goal(10.0, 10.0, affine_M_inv, robot_x=0.0, robot_y=0.0)
    
    assert rx == 10.0
    assert ry == 10.0
    assert yaw == pytest.approx(45.0)
    
    # Check that mqtt agent was called with the correct topic and payload
    mock_mqtt.publish.assert_called_once()
    args, kwargs = mock_mqtt.publish.call_args
    assert args[0] == 'goal'
    assert args[1]['x'] == 10.0
    assert args[1]['y'] == 10.0
    assert args[1]['yaw'] == pytest.approx(45.0)

def test_publish_initial_pose(nav_ctrl, mock_mqtt):
    result = nav_ctrl.publish_initial_pose(1.5, -2.5, 90.0)
    
    assert result is True
    # Initial pose topic is 'initial_pose'
    mock_mqtt.publish.assert_called_once()
    args, kwargs = mock_mqtt.publish.call_args
    assert args[0] == 'initial_pose'
    assert args[1]['x'] == 1.5
    assert args[1]['y'] == -2.5
    assert args[1]['angle'] == 90.0

def test_set_initial_pose(nav_ctrl, mock_mqtt):
    affine_M_inv = np.eye(3)
    # With identity, x, y remain the same
    result = nav_ctrl.set_initial_pose(5.0, 5.0, 180.0, affine_M_inv)
    
    assert result is True
    mock_mqtt.publish.assert_called_once()
    args, kwargs = mock_mqtt.publish.call_args
    assert args[0] == 'initial_pose'
    assert args[1]['x'] == 5.0
    assert args[1]['y'] == 5.0
    assert args[1]['angle'] == 180.0
