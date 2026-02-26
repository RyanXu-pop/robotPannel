# 设计系统 — 2026 Liquid Glass

> **管辖 Agent：** 设计师 Agent
> **用途：** 所有视觉参数的唯一真相源（Single Source of Truth）

---

## 当前 vs 目标 `[目标列为 PLANNED]`

| 维度 | 当前（VSCode Dark） | 目标（2026 Liquid Glass） |
|------|-------------------|--------------------------|
| 背景 | 不透明纯色 `#1e1e1e` | 半透明毛玻璃 `rgba(30,30,30,0.75)` |
| 面板 | 纯色卡片 `#252526` | 半透明浮层 + 物理阴影 |
| 圆角 | 4~8px 统一 | 同心 Squircle（外16/内12） |
| 阴影 | 无 | 多层物理阴影 |
| 边框 | 1px solid 灰色 | 边缘高光（白色低透明度） |
| 动画 | 无 | QPropertyAnimation 缓动 |
| 整体感觉 | 扁平工具感 | 毛玻璃悬浮感 |

---

## 当前色盘归档（theme.py） `[CURRENT — 已实现]`

```python
COLORS = {
    "background_main": "#1e1e1e",
    "background_panel": "#252526",
    "background_card": "#2d2d30",
    "text_primary": "#d4d4d4",
    "text_secondary": "#858585",
    "primary": "#007acc",
    "primary_hover": "#0098ff",
    "primary_disabled": "#003d66",
    "success": "#3fb950",
    "warning": "#d29922",
    "error": "#f14c4c",
    "border": "#3c3c3c",
    "border_focus": "#007acc",
}
```

升级方向：保留语义色值，将不透明纯色背景替换为 Liquid Glass 半透明背景，新增边缘高光和物理阴影层。新增键名统一使用 `glass_` 前缀。

---

## Liquid Glass 视觉参数

### 透明度

| 层级 | rgba 值 | 用途 |
|------|--------|------|
| 面板背景 | `rgba(30, 30, 30, 0.75)` ~ `rgba(45, 45, 48, 0.85)` | 浮动面板、抽屉容器 |
| 悬浮卡片 | `rgba(50, 50, 54, 0.90)` | 按钮组、信息卡片 |
| 毛玻璃光晕 | `rgba(255, 255, 255, 0.03)` ~ `rgba(255, 255, 255, 0.06)` | 面板顶部叠层光效 |

### 圆角（同心 Squircle 规则）

| 元素 | 外圆角 | 内圆角（外 - padding） |
|------|--------|---------------------|
| 面板容器 | 16px | 12px |
| 按钮 | 10px | — |
| 输入框 | 8px | — |
| 小徽章/Tag | 6px | — |

### 阴影

| 状态 | box-shadow 值 |
|------|---------------|
| 悬浮面板 | `0 8px 32px rgba(0,0,0,0.45)` |
| 按钮静态 | `0 2px 8px rgba(0,0,0,0.3)` |
| 按钮悬停 | `0 4px 16px rgba(0,0,0,0.4)` |

> `blurRadius` 上限见 `.cursorrules` 禁止事项

### 边缘高光

| 位置 | 值 |
|------|---|
| 顶部 | `1px solid rgba(255,255,255,0.08)` |
| 左/右 | `1px solid rgba(255,255,255,0.04)` |

### 动画曲线

| 场景 | 时长 | 缓动函数 |
|------|------|----------|
| 标准交互反馈 | 0.2s | ease-in-out |
| 抽屉展开/收起 | 0.3s | cubic-bezier(0.4, 0.0, 0.2, 1) |
| 悬停光效 | 0.15s | ease-out |
| 面板淡入 | 0.25s | ease-out |

> 动画实现约束见 `.cursorrules` 禁止事项

### 字号层次

| 级别 | 大小 | 字重 | 用途 |
|------|------|------|------|
| H1 | 18px | 600 | 面板标题 |
| H2 | 15px | 600 | 分区标题 |
| Body | 13px | 400 | 正文、标签值 |
| Caption | 11px | 400 | 辅助文字、时间戳 |

---

## UI 组件视觉职责 `[PLANNED]`

| 组件 | 当前状态 | Liquid Glass 目标 |
|------|----------|-------------------|
| ControlPanel | 不透明纯色面板 | 半透明毛玻璃 + 物理阴影悬浮 |
| TelemetryPanel | 不透明纯色面板 | 半透明背景 + 数据高亮卡片 |
| TeleopPanel | 简单键位布局 | 毛玻璃底板 + 按键微物理反馈 |
| PoseRecordPanel | 表格式布局 | 毛玻璃 + 行悬浮高亮 |
| UnifiedDrawer | 基础展开/收起 | cubic-bezier 缓动 + 阴影加深动画 |
| MapView | 纯色背景 | 零边框 + 背景透出窗口边缘 |
| theme.py | VSCode Dark 色盘 | Liquid Glass 色盘 + 阴影/动画预设 |

---

## theme.py 升级规划 `[PLANNED — 尚未实现]`

> 以下代码是**设计目标**，当前 `theme.py` 中还不存在这些内容。
> 实现时以此为蓝图，完成后将本段标记改为 `[IMPLEMENTED]`。

升级后的 `theme.py` 应新增：

```python
# 新增 Liquid Glass 色值（glass_ 前缀）
"glass_panel_bg": "rgba(30, 30, 30, 0.78)",
"glass_card_bg": "rgba(50, 50, 54, 0.90)",
"glass_highlight": "rgba(255, 255, 255, 0.06)",
"glass_border_top": "rgba(255, 255, 255, 0.08)",
"glass_border_side": "rgba(255, 255, 255, 0.04)",

# 新增预设常量
GLASS_SHADOWS = {
    "panel": {"offset": (0, 8), "blur": 16, "color": "rgba(0,0,0,0.45)"},
    "button": {"offset": (0, 2), "blur": 8, "color": "rgba(0,0,0,0.3)"},
    "button_hover": {"offset": (0, 4), "blur": 12, "color": "rgba(0,0,0,0.4)"},
}

GLASS_ANIMATIONS = {
    "standard": {"duration": 200, "curve": QEasingCurve.InOutQuad},
    "drawer": {"duration": 300, "curve": QEasingCurve.OutCubic},
    "hover": {"duration": 150, "curve": QEasingCurve.OutQuad},
    "fade_in": {"duration": 250, "curve": QEasingCurve.OutQuad},
}
```

接口约束：`apply_theme(app)` 签名不可变。

---

*本文档是设计师 Agent 输出视觉方案时的参数基准。所有 rgba、px、ms 值以此为准。*
