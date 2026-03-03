"""Dashboard - 分类卡片展示所有工作流文件"""
import os
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QGridLayout,
)
from PySide6.QtCore import Signal, Qt
from tools.workflow_manager.theme import COLORS
from tools.workflow_manager.models import FileEntry

FILE_REGISTRY = [
    FileEntry(".cursorrules", ".cursorrules", "AI 长期规则（架构/编码/禁令）", "shared", "rules"),
    FileEntry(".sprint", ".sprint", "当前 Sprint 约束（白名单/黑名单/DoD）", "shared", "rules"),
    FileEntry("workflow/README.md", "README.md", "工作流入口索引", "shared", "workflow"),
    FileEntry("workflow/01_project_context_template.md", "01 项目上下文模板", "新项目初始化时填写", "shared", "workflow"),
    FileEntry("workflow/02_architect_prompt_template.md", "02 架构师 Prompt", "向架构师提需求时使用", "architect", "workflow"),
    FileEntry("workflow/03_designer_prompt_template.md", "03 设计师 Prompt", "仅 UI 任务时使用", "designer", "workflow"),
    FileEntry("workflow/04_executor_guide.md", "04 执行者指南", "在 IDE 中逐步实施时参考", "shared", "workflow"),
    FileEntry("workflow/05_verify_and_commit.md", "05 验证与提交", "每完成一步后执行", "shared", "workflow"),
    FileEntry("docs/modules/architecture/system_overview.md", "系统全景", "部署拓扑 + MVVM 数据流", "architect", "architecture"),
    FileEntry("docs/modules/architecture/frozen_backend.md", "冻结后端 API", "UI Sprint 期间不可修改的接口", "architect", "architecture"),
    FileEntry("docs/modules/architecture/ui_signals.md", "UI Signal 契约", "UI 与 Controller 的信号接口", "architect", "architecture"),
    FileEntry("docs/modules/architecture/verify_commands.md", "验证命令速查", "静态检查/测试/Diff 审查命令", "architect", "architecture"),
    FileEntry("docs/modules/taste/design_principles.md", "品味原则", "Apple HIG 三原则 + 设计哲学", "designer", "taste"),
    FileEntry("docs/modules/taste/design_system.md", "设计系统", "Liquid Glass 视觉参数（唯一真相源）", "designer", "taste"),
    FileEntry("docs/modules/taste/apple_design_spec.md", "Apple 设计规范 2026", "Ive/Jobs 哲学 + 组件/布局/交互完整规范", "designer", "taste"),
]

CATEGORY_LABELS = {
    "rules": "AI 规则",
    "workflow": "通用工作流",
    "architecture": "架构知识库",
    "taste": "设计知识库",
}

AGENT_COLORS = {
    "architect": COLORS["tag_architect"],
    "designer": COLORS["tag_designer"],
    "shared": COLORS["border"],
}

AGENT_LABELS = {
    "architect": "架构师",
    "designer": "设计师",
    "shared": "共享",
}


class FileCard(QFrame):
    """单个文件卡片"""
    clicked = Signal(str)

    def __init__(self, entry: FileEntry, project_root: str, parent=None):
        super().__init__(parent)
        self._entry = entry
        self._abs_path = os.path.join(project_root, entry.path)
        self.setProperty("class", "Card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(90)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        top = QHBoxLayout()
        name_label = QLabel(entry.name)
        name_label.setStyleSheet("font-weight: 600; font-size: 13px; color: " + COLORS["text_bright"] + ";")
        top.addWidget(name_label)
        top.addStretch()

        agent_tag = QLabel(AGENT_LABELS.get(entry.agent, entry.agent))
        bg = AGENT_COLORS.get(entry.agent, COLORS["border"])
        agent_tag.setStyleSheet(
            "background-color: " + bg + "; color: " + COLORS["text_bright"] + ";"
            " padding: 2px 8px; border-radius: 3px; font-size: 11px;"
        )
        top.addWidget(agent_tag)
        layout.addLayout(top)

        desc = QLabel(entry.description)
        desc.setStyleSheet("color: " + COLORS["text_secondary"] + "; font-size: 12px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        mtime_str = ""
        if os.path.exists(self._abs_path):
            ts = os.path.getmtime(self._abs_path)
            mtime_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
        time_label = QLabel(mtime_str)
        time_label.setStyleSheet("color: " + COLORS["text_secondary"] + "; font-size: 11px;")
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(time_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._abs_path)
        super().mousePressEvent(event)


class DashboardView(QWidget):
    """仪表盘视图"""
    file_clicked = Signal(str)

    def __init__(self, project_root: str, parent=None):
        super().__init__(parent)
        self._root = project_root

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        title = QLabel("Dashboard")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        for cat_key, cat_label in CATEGORY_LABELS.items():
            entries = [e for e in FILE_REGISTRY if e.category == cat_key]
            if not entries:
                continue

            section_label = QLabel(cat_label)
            section_label.setObjectName("SectionTitle")
            layout.addWidget(section_label)

            grid = QGridLayout()
            grid.setSpacing(12)
            for i, entry in enumerate(entries):
                card = FileCard(entry, self._root)
                card.clicked.connect(self.file_clicked.emit)
                row, col = divmod(i, 3)
                grid.addWidget(card, row, col)
            layout.addLayout(grid)

        layout.addStretch()
        scroll.setWidget(container)
