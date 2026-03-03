"""Sprint 编辑器 - 表单化编辑 .sprint 文件"""
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QListWidget, QPushButton, QScrollArea, QFrame, QMessageBox,
    QAbstractItemView, QInputDialog,
)
from PySide6.QtCore import Qt
from tools.workflow_manager.theme import COLORS
from tools.workflow_manager.parsers import parse_sprint, write_sprint
from tools.workflow_manager.models import SprintConfig


class _ListEditor(QWidget):
    """可增删的列表编辑器"""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QHBoxLayout()
        lbl = QLabel(title)
        lbl.setObjectName("SectionTitle")
        header.addWidget(lbl)
        header.addStretch()

        add_btn = QPushButton("+")
        add_btn.setFixedSize(28, 28)
        add_btn.clicked.connect(self._add_item)
        header.addWidget(add_btn)

        del_btn = QPushButton("-")
        del_btn.setFixedSize(28, 28)
        del_btn.clicked.connect(self._del_item)
        header.addWidget(del_btn)

        layout.addLayout(header)

        self._list = QListWidget()
        self._list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        layout.addWidget(self._list)

    def set_items(self, items: list[str]):
        self._list.clear()
        for item in items:
            self._list.addItem(item)

    def get_items(self) -> list[str]:
        return [self._list.item(i).text() for i in range(self._list.count())]

    def _add_item(self):
        text, ok = QInputDialog.getText(self, "New item", "Content:")
        if ok and text.strip():
            self._list.addItem(text.strip())

    def _del_item(self):
        row = self._list.currentRow()
        if row >= 0:
            self._list.takeItem(row)


class SprintEditor(QWidget):
    """Sprint 表单编辑器"""

    def __init__(self, sprint_path: str, parent=None):
        super().__init__(parent)
        self._path = sprint_path

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Sprint Editor")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        # Meta fields
        meta = QHBoxLayout()
        meta.setSpacing(12)

        name_col = QVBoxLayout()
        name_col.addWidget(QLabel("Sprint Name"))
        self._name = QLineEdit()
        name_col.addWidget(self._name)
        meta.addLayout(name_col)

        date_col = QVBoxLayout()
        date_col.addWidget(QLabel("Start Date"))
        self._date = QLineEdit()
        date_col.addWidget(self._date)
        meta.addLayout(date_col)

        end_col = QVBoxLayout()
        end_col.addWidget(QLabel("End Condition"))
        self._end = QLineEdit()
        end_col.addWidget(self._end)
        meta.addLayout(end_col)

        layout.addLayout(meta)

        # Goal
        goal_label = QLabel("Sprint Goal")
        goal_label.setObjectName("SectionTitle")
        layout.addWidget(goal_label)
        self._goal = QTextEdit()
        self._goal.setMaximumHeight(80)
        layout.addWidget(self._goal)

        # Lists in 2-column grid
        lists_row = QHBoxLayout()
        lists_row.setSpacing(16)

        self._whitelist = _ListEditor("Whitelist (allowed files)")
        lists_row.addWidget(self._whitelist)

        self._blacklist = _ListEditor("Blacklist (frozen)")
        lists_row.addWidget(self._blacklist)

        layout.addLayout(lists_row)

        lists_row2 = QHBoxLayout()
        lists_row2.setSpacing(16)

        self._redlines = _ListEditor("Red Lines")
        lists_row2.addWidget(self._redlines)

        self._dod = _ListEditor("DoD Items")
        lists_row2.addWidget(self._dod)

        layout.addLayout(lists_row2)

        self._verify = _ListEditor("Verify Commands")
        layout.addWidget(self._verify)

        # Save button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        save_btn = QPushButton("Save .sprint")
        save_btn.setProperty("class", "PrimaryAction")
        save_btn.setStyleSheet(
            "background-color: " + COLORS["primary"] + "; color: white;"
            " border: none; padding: 10px 32px; border-radius: 6px; font-size: 14px; font-weight: 600;"
        )
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

        layout.addStretch()
        scroll.setWidget(container)

        self._load()

    def _load(self):
        if not os.path.exists(self._path):
            return
        config = parse_sprint(self._path)
        self._name.setText(config.name)
        self._date.setText(config.start_date)
        self._end.setText(config.end_condition)
        self._goal.setPlainText(config.goal)
        self._whitelist.set_items(config.whitelist)
        self._blacklist.set_items(config.blacklist)
        self._redlines.set_items(config.redlines)
        self._dod.set_items(config.dod_items)
        self._verify.set_items([n + ": " + c for n, c in config.verify_commands])

    def _save(self):
        config = SprintConfig(
            name=self._name.text(),
            start_date=self._date.text(),
            end_condition=self._end.text(),
            goal=self._goal.toPlainText(),
            whitelist=self._whitelist.get_items(),
            blacklist=self._blacklist.get_items(),
            redlines=self._redlines.get_items(),
            dod_items=self._dod.get_items(),
            verify_commands=[],
        )
        for line in self._verify.get_items():
            if ": " in line:
                parts = line.split(": ", 1)
                config.verify_commands.append((parts[0], parts[1]))
            else:
                config.verify_commands.append((line, ""))

        write_sprint(config, self._path)
        QMessageBox.information(self, "Saved", ".sprint file saved successfully.")
