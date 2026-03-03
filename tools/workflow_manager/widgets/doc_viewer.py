"""文档查看器 - 文件树 + Markdown 渲染"""
import os
import markdown
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QTextBrowser, QSplitter, QLabel,
)
from PySide6.QtCore import Qt
from tools.workflow_manager.theme import COLORS, MARKDOWN_CSS


class DocViewer(QWidget):
    """文档查看器：左侧文件树，右侧 Markdown 渲染"""

    SCAN_DIRS = ["workflow", "docs"]

    def __init__(self, project_root: str, parent=None):
        super().__init__(parent)
        self._root = project_root
        self._md = markdown.Markdown(extensions=["tables", "fenced_code"])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QLabel("Docs")
        header.setObjectName("PageTitle")
        header.setContentsMargins(24, 16, 24, 8)
        layout.addWidget(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setMinimumWidth(220)
        self._tree.setMaximumWidth(320)
        splitter.addWidget(self._tree)

        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(True)
        splitter.addWidget(self._browser)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        self._build_tree()
        self._tree.itemClicked.connect(self._on_item_clicked)

        self._also_scan_root_files = [".cursorrules", ".sprint"]
        for fname in self._also_scan_root_files:
            fpath = os.path.join(self._root, fname)
            if os.path.isfile(fpath):
                item = QTreeWidgetItem(self._tree, [fname])
                item.setData(0, Qt.ItemDataRole.UserRole, fpath)

    def _build_tree(self):
        for dirname in self.SCAN_DIRS:
            dirpath = os.path.join(self._root, dirname)
            if not os.path.isdir(dirpath):
                continue
            root_item = QTreeWidgetItem(self._tree, [dirname + "/"])
            root_item.setExpanded(True)
            self._add_dir(root_item, dirpath)

    def _add_dir(self, parent_item: QTreeWidgetItem, dirpath: str):
        try:
            entries = sorted(os.listdir(dirpath))
        except OSError:
            return
        dirs_first = sorted(entries, key=lambda e: (not os.path.isdir(os.path.join(dirpath, e)), e))
        for name in dirs_first:
            full = os.path.join(dirpath, name)
            if os.path.isdir(full):
                child = QTreeWidgetItem(parent_item, [name + "/"])
                child.setExpanded(True)
                self._add_dir(child, full)
            elif name.endswith((".md", ".txt", ".yaml", ".yml")):
                child = QTreeWidgetItem(parent_item, [name])
                child.setData(0, Qt.ItemDataRole.UserRole, full)

    def _on_item_clicked(self, item: QTreeWidgetItem, _col: int):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path and os.path.isfile(path):
            self.open_file(path)

    def open_file(self, path: str):
        """渲染并显示指定文件"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        except OSError:
            self._browser.setHtml("<p>Cannot read file.</p>")
            return

        if path.endswith(".md"):
            self._md.reset()
            html_body = self._md.convert(text)
            html = "<html><head><style>" + MARKDOWN_CSS + "</style></head><body>" + html_body + "</body></html>"
        else:
            escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            html = "<html><head><style>" + MARKDOWN_CSS + "</style></head><body><pre>" + escaped + "</pre></body></html>"

        self._browser.setHtml(html)

        # highlight corresponding tree item
        self._select_tree_item(path)

    def _select_tree_item(self, path: str):
        iterator = self._tree.itemAt(0, 0)

        def walk(item):
            if item is None:
                return
            if item.data(0, Qt.ItemDataRole.UserRole) == path:
                self._tree.setCurrentItem(item)
                return
            for i in range(item.childCount()):
                walk(item.child(i))

        for i in range(self._tree.topLevelItemCount()):
            walk(self._tree.topLevelItem(i))
