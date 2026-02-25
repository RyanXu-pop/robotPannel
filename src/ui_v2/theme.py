"""
现代暗色风格主题定义
用于集中管理 UI V2 的色盘、字体和 QSS 样式表
"""

# 定义核心色彩变量 (Modern Dark Theme Palette)
COLORS = {
    "background_main": "#1e1e1e",      # 主背景色 (VSCode Dark)
    "background_panel": "#252526",     # 侧边栏/浮动面板背景
    "background_card": "#2d2d30",      # 卡片/高亮控件背景
    "text_primary": "#d4d4d4",         # 主要文字
    "text_secondary": "#858585",       # 次要/提示文字
    "primary": "#007acc",              # 主色调 (赛博蓝)
    "primary_hover": "#0098ff",        # 主色调悬停
    "primary_disabled": "#003d66",     # 主色调禁用
    "success": "#3fb950",              # 成功/在线绿
    "warning": "#d29922",              # 警告黄
    "error": "#f14c4c",                # 错误/离线红
    "border": "#3c3c3c",               # 默认边框
    "border_focus": "#007acc",         # 激活态边框
}

# 全局通用 CSS 注入表
GLOBAL_STYLESHEET = f"""
/* 全局基础设置 */
QWidget {{
    background-color: {COLORS['background_main']};
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'Microsoft YaHei', 'PingFang SC', sans-serif;
    font-size: 13px;
}}

/* 带有卡片效果的背景 */
.CardWidget, .PanelWidget {{
    background-color: {COLORS['background_panel']};
    border-radius: 8px;
    border: 1px solid {COLORS['border']};
}}

/* 按钮通用设置 */
QPushButton {{
    background-color: {COLORS['background_card']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 6px 16px;
}}
QPushButton:hover {{
    background-color: {COLORS['border']};
}}
QPushButton:pressed {{
    background-color: {COLORS['background_panel']};
}}
QPushButton:disabled {{
    color: {COLORS['text_secondary']};
    border-color: {COLORS['background_card']};
}}

/* 品牌动作按钮 (Action Button) */
QPushButton.PrimaryAction {{
    background-color: {COLORS['primary']};
    color: white;
    border: none;
}}
QPushButton.PrimaryAction:hover {{
    background-color: {COLORS['primary_hover']};
}}
QPushButton.PrimaryAction:disabled {{
    background-color: {COLORS['primary_disabled']};
    color: {COLORS['text_secondary']};
}}

/* 危险/高危动作按钮 */
QPushButton.DangerAction {{
    background-color: {COLORS['error']};
    color: white;
    border: none;
}}

/* 滚动条美化 */
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 0px 0px 0px 0px;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['border']};
    min-height: 20px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLORS['text_secondary']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* 图形视图 (地图主视野) */
QGraphicsView {{
    background-color: {COLORS['background_main']};
    border: none;
}}

/* 单行输入框 */
QLineEdit {{
    background-color: {COLORS['background_main']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 5px;
    color: {COLORS['text_primary']};
}}
QLineEdit:focus {{
    border: 1px solid {COLORS['border_focus']};
}}
"""

def apply_theme(app) -> None:
    """给 QApplication 注入全局主题配置"""
    app.setStyleSheet(GLOBAL_STYLESHEET)
