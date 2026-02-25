import sys
import os
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.controllers.service_controller import ServiceController
from src.core.models import AppSystemState


@pytest.fixture
def mock_ssh():
    ssh = MagicMock()
    ssh.start_mqtt_bridge_async = AsyncMock(return_value=(True, "ok"))
    ssh.stop_mqtt_bridge_async = AsyncMock()
    ssh.start_chassis_async = AsyncMock(return_value=(True, "ok"))
    ssh.stop_chassis_async = AsyncMock()
    ssh.start_gmapping_async = AsyncMock(return_value=(True, "ok"))
    ssh.stop_gmapping_async = AsyncMock()
    ssh.start_navigation_async = AsyncMock(return_value=(True, "ok"))
    ssh.stop_navigation_async = AsyncMock()
    return ssh


@pytest.fixture
def app_state():
    return AppSystemState()


@pytest.fixture
def service_ctrl(app_state, mock_ssh):
    workflow = MagicMock()
    return ServiceController(
        app_state=app_state,
        async_ssh=mock_ssh,
        workflow_ctrl=workflow,
    )


def test_can_start_mapping_navigation_conflict(service_ctrl, app_state):
    """建图与导航互斥：导航运行时不能启动建图"""
    app_state.navigation_running = True
    can, reason = service_ctrl.can_start_mapping()
    assert can is False
    assert "导航" in reason


def test_can_start_mapping_chassis_required(service_ctrl, app_state):
    """建图需要底盘运行"""
    app_state.chassis_running = False
    app_state.navigation_running = False
    can, reason = service_ctrl.can_start_mapping()
    assert can is False
    assert "底盘" in reason


def test_can_start_mapping_mqtt_check(service_ctrl, app_state):
    """建图检查 MQTT 状态"""
    app_state.chassis_running = True
    app_state.navigation_running = False
    app_state.mqtt_running = False
    can, reason = service_ctrl.can_start_mapping()
    assert can is False
    assert reason == "MQTT_NOT_RUNNING"


def test_can_start_mapping_all_ok(service_ctrl, app_state):
    """所有前置条件满足时可以启动建图"""
    app_state.chassis_running = True
    app_state.navigation_running = False
    app_state.mqtt_running = True
    can, reason = service_ctrl.can_start_mapping()
    assert can is True
    assert reason == ""


def test_can_start_navigation_mapping_conflict(service_ctrl, app_state):
    """导航与建图互斥：建图运行时不能启动导航"""
    app_state.mapping_running = True
    can, reason = service_ctrl.can_start_navigation()
    assert can is False
    assert "建图" in reason


def test_can_start_navigation_chassis_required(service_ctrl, app_state):
    """导航需要底盘运行"""
    app_state.mapping_running = False
    app_state.chassis_running = False
    can, reason = service_ctrl.can_start_navigation()
    assert can is False
    assert "底盘" in reason


def test_can_start_navigation_all_ok(service_ctrl, app_state):
    """所有前置条件满足时可以启动导航"""
    app_state.mapping_running = False
    app_state.chassis_running = True
    can, reason = service_ctrl.can_start_navigation()
    assert can is True
    assert reason == ""
