"""
conftest.py — 共享测试 fixture

提供 QApplication 实例等跨测试共享资源，避免每个测试文件重复初始化。
"""
import sys
import os
import pytest

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture(scope="session")
def qapp():
    """Session-scoped QApplication fixture：整个测试会话只创建一次。"""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    yield app
