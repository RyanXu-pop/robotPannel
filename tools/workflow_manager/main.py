#!/usr/bin/env python
"""Workflow Manager - 工作流可视化管理工具"""
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PySide6.QtWidgets import QApplication
from tools.workflow_manager.theme import apply_theme
from tools.workflow_manager.widgets.main_window import MainWindow
from tools.workflow_manager.widgets.dashboard import DashboardView
from tools.workflow_manager.widgets.doc_viewer import DocViewer
from tools.workflow_manager.widgets.sprint_editor import SprintEditor
from tools.workflow_manager.widgets.task_board import TaskBoard
from tools.workflow_manager.models import TaskStore


def main():
    app = QApplication(sys.argv)
    apply_theme(app)

    window = MainWindow()

    sprint_path = os.path.join(project_root, ".sprint")
    tasks_path = os.path.join(project_root, ".tasks.json")

    dashboard = DashboardView(project_root)
    doc_viewer = DocViewer(project_root)
    sprint_editor = SprintEditor(sprint_path)
    task_store = TaskStore(tasks_path)
    task_board = TaskBoard(task_store)

    window.set_page("dashboard", dashboard)
    window.set_page("docs", doc_viewer)
    window.set_page("sprint", sprint_editor)
    window.set_page("tasks", task_board)

    dashboard.file_clicked.connect(lambda path: (
        window._nav_buttons["docs"].setChecked(True),
        window.set_page("docs", doc_viewer),
        window._stack.setCurrentWidget(window._pages["docs"]),
        doc_viewer.open_file(path),
    ))

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
