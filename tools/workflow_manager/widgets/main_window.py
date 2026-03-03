"""主窗口 - 侧边栏导航 + QStackedWidget 内容区"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QStackedWidget, QLabel, QButtonGroup,
)
from PySide6.QtCore import Qt
from tools.workflow_manager.theme import SIDEBAR_WIDTH


class MainWindow(QMainWindow):
    """Workflow Manager 主窗口"""

    NAV_ITEMS = [
        ("dashboard", "Dashboard"),
        ("docs", "Docs"),
        ("sprint", "Sprint"),
        ("tasks", "Tasks"),
    ]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Workflow Manager")
        self.setMinimumSize(1000, 650)
        self.resize(1200, 750)

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # --- 侧边栏 ---
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(SIDEBAR_WIDTH)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 16, 0, 16)
        sidebar_layout.setSpacing(2)

        title = QLabel("Workflow\nManager")
        title.setObjectName("PageTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(title)
        sidebar_layout.addSpacing(16)

        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)
        self._nav_buttons: dict[str, QPushButton] = {}

        for key, label in self.NAV_ITEMS:
            btn = QPushButton(label)
            btn.setCheckable(True)
            self._nav_group.addButton(btn)
            self._nav_buttons[key] = btn
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()
        root_layout.addWidget(sidebar)

        # --- 内容区 ---
        self._stack = QStackedWidget()
        root_layout.addWidget(self._stack)

        self._pages: dict[str, QWidget] = {}
        for key, label in self.NAV_ITEMS:
            page = QWidget()
            page_layout = QVBoxLayout(page)
            page_layout.setContentsMargins(24, 24, 24, 24)
            placeholder = QLabel(label)
            placeholder.setObjectName("PageTitle")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            page_layout.addWidget(placeholder)
            page_layout.addStretch()
            self._pages[key] = page
            self._stack.addWidget(page)

        self._nav_group.buttonClicked.connect(self._on_nav)
        self._nav_buttons["dashboard"].setChecked(True)
        self._stack.setCurrentWidget(self._pages["dashboard"])

    def set_page(self, key: str, widget: QWidget):
        """替换某个导航页的内容"""
        old = self._pages.get(key)
        if old:
            idx = self._stack.indexOf(old)
            self._stack.removeWidget(old)
            old.deleteLater()
        nav_keys = [k for k, _ in self.NAV_ITEMS]
        insert_idx = nav_keys.index(key) if key in nav_keys else self._stack.count()
        self._stack.insertWidget(insert_idx, widget)
        self._pages[key] = widget
        if self._nav_buttons.get(key) and self._nav_buttons[key].isChecked():
            self._stack.setCurrentWidget(widget)

    def _on_nav(self, btn: QPushButton):
        for key, b in self._nav_buttons.items():
            if b is btn:
                page = self._pages.get(key)
                if page:
                    self._stack.setCurrentWidget(page)
                break
