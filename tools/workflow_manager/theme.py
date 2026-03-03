"""Workflow Manager 暗色主题 - 复用主项目色盘"""

COLORS = {
    "background_main": "#1e1e1e",
    "background_panel": "#252526",
    "background_card": "#2d2d30",
    "background_hover": "#37373d",
    "text_primary": "#d4d4d4",
    "text_secondary": "#858585",
    "text_bright": "#ffffff",
    "primary": "#007acc",
    "primary_hover": "#0098ff",
    "success": "#3fb950",
    "warning": "#d29922",
    "error": "#f14c4c",
    "border": "#3c3c3c",
    "border_focus": "#007acc",
    "tag_architect": "#2d6a4f",
    "tag_designer": "#6a2d5f",
}

SIDEBAR_WIDTH = 200


def _qss():
    c = COLORS
    parts = [
        "QWidget { background-color: " + c["background_main"] + "; color: " + c["text_primary"] + ";",
        "  font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif; font-size: 13px; }",
        "#Sidebar { background-color: " + c["background_panel"] + "; border-right: 1px solid " + c["border"] + "; }",
        "#Sidebar QPushButton { text-align: left; padding: 10px 16px; border: none;",
        "  border-radius: 6px; margin: 2px 8px; color: " + c["text_secondary"] + "; font-size: 13px; }",
        "#Sidebar QPushButton:hover { background-color: " + c["background_hover"] + "; color: " + c["text_primary"] + "; }",
        "#Sidebar QPushButton:checked { background-color: " + c["primary"] + "; color: " + c["text_bright"] + "; }",
        ".Card { background-color: " + c["background_card"] + "; border: 1px solid " + c["border"] + "; border-radius: 8px; padding: 12px; }",
        ".Card:hover { border-color: " + c["primary"] + "; }",
        "QPushButton { background-color: " + c["background_card"] + "; color: " + c["text_primary"] + "; border: 1px solid " + c["border"] + ";",
        "  border-radius: 4px; padding: 6px 16px; }",
        "QPushButton:hover { background-color: " + c["background_hover"] + "; }",
        "QPushButton.PrimaryAction { background-color: " + c["primary"] + "; color: white; border: none; }",
        "QPushButton.PrimaryAction:hover { background-color: " + c["primary_hover"] + "; }",
        "QLineEdit, QTextEdit, QDateEdit { background-color: " + c["background_main"] + "; border: 1px solid " + c["border"] + ";",
        "  border-radius: 4px; padding: 5px; color: " + c["text_primary"] + "; }",
        "QLineEdit:focus, QTextEdit:focus { border-color: " + c["border_focus"] + "; }",
        "QListWidget, QTreeWidget { background-color: " + c["background_main"] + "; border: 1px solid " + c["border"] + "; border-radius: 4px; outline: none; }",
        "QListWidget::item, QTreeWidget::item { padding: 4px 8px; border-radius: 4px; }",
        "QListWidget::item:hover, QTreeWidget::item:hover { background-color: " + c["background_hover"] + "; }",
        "QListWidget::item:selected, QTreeWidget::item:selected { background-color: " + c["primary"] + "; color: " + c["text_bright"] + "; }",
        "QScrollBar:vertical { background: transparent; width: 8px; }",
        "QScrollBar::handle:vertical { background: " + c["border"] + "; min-height: 20px; border-radius: 4px; }",
        "QScrollBar::handle:vertical:hover { background: " + c["text_secondary"] + "; }",
        "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }",
        "QScrollBar:horizontal { background: transparent; height: 8px; }",
        "QScrollBar::handle:horizontal { background: " + c["border"] + "; min-width: 20px; border-radius: 4px; }",
        "QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }",
        "QTextBrowser { background-color: " + c["background_main"] + "; border: none; padding: 16px; }",
        "QLabel#SectionTitle { font-size: 16px; font-weight: 600; color: " + c["text_primary"] + "; padding: 4px 0; }",
        "QLabel#PageTitle { font-size: 20px; font-weight: 700; color: " + c["text_bright"] + "; padding: 8px 0; }",
    ]
    return "\n".join(parts)


def _md_css():
    c = COLORS
    parts = [
        "body { background-color: " + c["background_main"] + "; color: " + c["text_primary"] + ";",
        "  font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif; font-size: 14px; line-height: 1.6; padding: 0 8px; }",
        "h1, h2, h3 { color: " + c["text_bright"] + "; }",
        "h1 { font-size: 22px; border-bottom: 1px solid " + c["border"] + "; padding-bottom: 8px; }",
        "h2 { font-size: 18px; margin-top: 24px; }",
        "h3 { font-size: 15px; margin-top: 16px; }",
        "a { color: " + c["primary"] + "; text-decoration: none; }",
        "a:hover { color: " + c["primary_hover"] + "; }",
        "code { background-color: " + c["background_card"] + "; padding: 2px 6px; border-radius: 3px;",
        "  font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 13px; }",
        "pre { background-color: " + c["background_panel"] + "; border: 1px solid " + c["border"] + "; border-radius: 6px;",
        "  padding: 12px; overflow-x: auto; font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 13px; line-height: 1.4; }",
        "pre code { background: none; padding: 0; }",
        "table { border-collapse: collapse; width: 100%; margin: 12px 0; }",
        "th, td { border: 1px solid " + c["border"] + "; padding: 8px 12px; text-align: left; }",
        "th { background-color: " + c["background_panel"] + "; color: " + c["text_bright"] + "; font-weight: 600; }",
        "tr:hover { background-color: " + c["background_card"] + "; }",
        "blockquote { border-left: 3px solid " + c["primary"] + "; margin: 12px 0; padding: 4px 16px;",
        "  color: " + c["text_secondary"] + "; background-color: " + c["background_panel"] + "; border-radius: 0 4px 4px 0; }",
        "hr { border: none; border-top: 1px solid " + c["border"] + "; margin: 16px 0; }",
    ]
    return "\n".join(parts)


GLOBAL_QSS = _qss()
MARKDOWN_CSS = _md_css()


def apply_theme(app) -> None:
    """注入全局主题"""
    app.setStyleSheet(GLOBAL_QSS)
