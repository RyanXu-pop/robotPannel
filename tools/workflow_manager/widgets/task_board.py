"""Task Board - 三列看板式任务追踪"""
import uuid
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QInputDialog, QMenu, QMessageBox,
)
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QDrag
from tools.workflow_manager.theme import COLORS
from tools.workflow_manager.models import TaskStore, TaskItem

COLUMNS = [
    ("todo", "To Do"),
    ("in_progress", "In Progress"),
    ("done", "Done"),
]

PRIORITY_COLORS = {
    "high": COLORS["error"],
    "medium": COLORS["warning"],
    "low": COLORS["success"],
}


class TaskCard(QFrame):
    """可拖拽的任务卡片"""

    def __init__(self, task: TaskItem, store: TaskStore, board: "TaskBoard", parent=None):
        super().__init__(parent)
        self._task = task
        self._store = store
        self._board = board
        self.setProperty("class", "Card")
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)
        self.setFixedHeight(80)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        top = QHBoxLayout()
        title = QLabel(task.title)
        title.setStyleSheet("font-weight: 600; font-size: 13px; color: " + COLORS["text_bright"] + ";")
        title.setWordWrap(True)
        top.addWidget(title, 1)

        pri_color = PRIORITY_COLORS.get(task.priority, COLORS["border"])
        pri_dot = QLabel()
        pri_dot.setFixedSize(10, 10)
        pri_dot.setStyleSheet("background-color: " + pri_color + "; border-radius: 5px;")
        top.addWidget(pri_dot)
        layout.addLayout(top)

        if task.description:
            desc = QLabel(task.description)
            desc.setStyleSheet("color: " + COLORS["text_secondary"] + "; font-size: 11px;")
            desc.setWordWrap(True)
            desc.setMaximumHeight(30)
            layout.addWidget(desc)

        time_label = QLabel(task.created_at)
        time_label.setStyleSheet("color: " + COLORS["text_secondary"] + "; font-size: 10px;")
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(time_label)

    def mouseMoveEvent(self, event):
        if event.buttons() != Qt.MouseButton.LeftButton:
            return
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(self._task.id)
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.MoveAction)

    def _context_menu(self, pos):
        menu = QMenu(self)
        edit_action = menu.addAction("Edit")
        delete_action = menu.addAction("Delete")
        menu.addSeparator()
        for status_key, status_label in COLUMNS:
            if status_key != self._task.status:
                move_action = menu.addAction("Move to " + status_label)
                move_action.setData(status_key)

        action = menu.exec(self.mapToGlobal(pos))
        if action is None:
            return
        if action == edit_action:
            self._edit()
        elif action == delete_action:
            self._delete()
        elif action.data():
            self._task.status = action.data()
            self._store.update(self._task)
            self._board.refresh()

    def _edit(self):
        text, ok = QInputDialog.getText(self, "Edit title", "Title:", text=self._task.title)
        if ok and text.strip():
            self._task.title = text.strip()
            self._store.update(self._task)
            self._board.refresh()

    def _delete(self):
        reply = QMessageBox.question(self, "Delete", "Delete this task?")
        if reply == QMessageBox.StandardButton.Yes:
            self._store.remove(self._task.id)
            self._board.refresh()


class ColumnWidget(QFrame):
    """看板列 - 可接受拖拽"""

    def __init__(self, status: str, label: str, store: TaskStore, board: "TaskBoard", parent=None):
        super().__init__(parent)
        self._status = status
        self._store = store
        self._board = board
        self.setAcceptDrops(True)
        self.setMinimumWidth(260)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel(label)
        title.setObjectName("SectionTitle")
        header.addWidget(title)

        count = len(store.get_by_status(status))
        count_label = QLabel(str(count))
        count_label.setStyleSheet(
            "background-color: " + COLORS["background_hover"] + "; color: " + COLORS["text_secondary"] + ";"
            " padding: 2px 8px; border-radius: 10px; font-size: 11px;"
        )
        header.addWidget(count_label)
        header.addStretch()

        if status == "todo":
            add_btn = QPushButton("+")
            add_btn.setFixedSize(28, 28)
            add_btn.clicked.connect(self._add_task)
            header.addWidget(add_btn)

        layout.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        inner = QWidget()
        self._inner_layout = QVBoxLayout(inner)
        self._inner_layout.setContentsMargins(0, 0, 0, 0)
        self._inner_layout.setSpacing(8)
        self._inner_layout.addStretch()
        scroll.setWidget(inner)
        layout.addWidget(scroll)

        self._populate()

    def _populate(self):
        while self._inner_layout.count() > 1:
            item = self._inner_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for task in self._store.get_by_status(self._status):
            card = TaskCard(task, self._store, self._board)
            self._inner_layout.insertWidget(self._inner_layout.count() - 1, card)

    def _add_task(self):
        text, ok = QInputDialog.getText(self, "New Task", "Title:")
        if ok and text.strip():
            task = TaskItem(
                id=uuid.uuid4().hex[:8],
                title=text.strip(),
                status="todo",
                created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
            )
            self._store.add(task)
            self._board.refresh()

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        task_id = event.mimeData().text()
        for task in self._store.tasks:
            if task.id == task_id:
                task.status = self._status
                self._store.update(task)
                break
        self._board.refresh()
        event.acceptProposedAction()


class TaskBoard(QWidget):
    """三列看板主视图"""

    def __init__(self, store: TaskStore, parent=None):
        super().__init__(parent)
        self._store = store

        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(24, 24, 24, 24)
        self._outer.setSpacing(16)

        title = QLabel("Tasks")
        title.setObjectName("PageTitle")
        self._outer.addWidget(title)

        self._columns_widget = QWidget()
        self._columns_layout = QHBoxLayout(self._columns_widget)
        self._columns_layout.setSpacing(16)
        self._columns_layout.setContentsMargins(0, 0, 0, 0)
        self._outer.addWidget(self._columns_widget, 1)

        self._build_columns()

    def _build_columns(self):
        while self._columns_layout.count():
            item = self._columns_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for status, label in COLUMNS:
            col = ColumnWidget(status, label, self._store, self)
            self._columns_layout.addWidget(col)

    def refresh(self):
        self._build_columns()
