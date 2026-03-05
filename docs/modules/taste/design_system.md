# 设计系统 — V3 Liquid Glass

> **管辖 Agent：** 设计师 Agent
> **用途：** 所有视觉参数的唯一真相源（Single Source of Truth）
> **版本：** V3 — 完全重写

---

## 色盘

### 基础色（保留语义，升级实现）

```python
COLORS = {
    # 背景层级
    "bg_void":       "#121214",                   # 窗口底色（地图背景）
    "bg_glass":      "rgba(25, 25, 28, 0.82)",    # 浮动面板
    "bg_card":       "rgba(44, 44, 48, 0.90)",    # 按钮/卡片
    "bg_hover":      "rgba(60, 60, 66, 0.95)",    # 悬停态

    # 文字
    "text_primary":  "#F5F5F7",                   # 主要文字
    "text_secondary":"#98989D",                   # 辅助文字
    "text_tertiary": "#636366",                   # 最弱文字

    # 语义色
    "accent":        "#0A84FF",                   # 主色调（Apple Blue）
    "accent_hover":  "#409CFF",                   # 主色调悬停
    "success":       "#30D158",                   # 在线/成功
    "warning":       "#FFD60A",                   # 警告
    "danger":        "#FF3B30",                   # 错误/急停

    # Glass 专用
    "glass_highlight":    "rgba(255,255,255,0.06)",  # 面板内光晕
    "glass_border_top":   "rgba(255,255,255,0.10)",  # 顶部高光边
    "glass_border_side":  "rgba(255,255,255,0.04)",  # 侧边微光
    "glass_separator":    "rgba(255,255,255,0.06)",  # 分割线
}
```

### V2 → V3 色值迁移

| V2 键名 | V3 键名 | 变化 |
|---------|---------|------|
| `background_main` #1e1e1e | `bg_void` #121214 | 更深，让面板更突出 |
| `background_panel` #252526 | `bg_glass` rgba | 不透明 → 半透明 |
| `background_card` #2d2d30 | `bg_card` rgba | 不透明 → 半透明 |
| `primary` #007acc | `accent` #0A84FF | 更接近 Apple Blue |
| `error` #f14c4c | `danger` #FF3B30 | 更接近 Apple Red |
| `success` #3fb950 | `success` #30D158 | 更接近 Apple Green |

---

## 圆角

| 元素 | 外圆角 | 内圆角 | 备注 |
|------|--------|--------|------|
| 浮动面板 | 16px | 12px | 同心 Squircle |
| 按钮 | 10px | — | |
| 输入框 | 8px | — | |
| 状态栏 | 12px | — | 胶囊形 |
| 小徽章 | 6px | — | |
| E-Stop | 14px | — | 大触控区 |

---

## 阴影

```python
SHADOWS = {
    "panel":        {"offset": (0, 8), "blur": 16, "color": "rgba(0,0,0,0.50)"},
    "button":       {"offset": (0, 2), "blur":  8, "color": "rgba(0,0,0,0.30)"},
    "button_hover": {"offset": (0, 4), "blur": 12, "color": "rgba(0,0,0,0.40)"},
    "status_bar":   {"offset": (0, 2), "blur":  8, "color": "rgba(0,0,0,0.25)"},
    "estop":        {"offset": (0, 4), "blur": 16, "color": "rgba(255,59,48,0.35)"},
}
```

> `blurRadius` 上限 20px（`.cursorrules` 硬约束）

---

## 动画

```python
ANIMATIONS = {
    "standard":    {"duration": 200, "curve": "InOutQuad"},      # 交互反馈
    "panel_fade":  {"duration": 250, "curve": "OutCubic"},       # 面板淡入
    "drawer":      {"duration": 300, "curve": "OutCubic"},       # 滑入滑出
    "hover":       {"duration": 150, "curve": "OutQuad"},        # 悬停光效
    "mode_switch": {"duration": 250, "curve": "InOutCubic"},     # 模式切换
    "pulse":       {"duration": 1500, "curve": "InOutSine"},     # 呼吸脉冲
}
```

> 动画实现必须用 `QPropertyAnimation`，禁止 Python 逐帧驱动

---

## 字号体系

| 级别 | 大小 | 字重 | 行高 | 用途 |
|------|------|------|------|------|
| H1 | 18px | 600 (Semibold) | 1.3 | 面板标题 |
| H2 | 15px | 600 (Semibold) | 1.3 | 分区标题 |
| Body | 13px | 400 (Regular) | 1.4 | 正文、标签值 |
| Mono | 13px | 400 (Regular) | 1.2 | 数值（等宽字体） |
| Caption | 11px | 400 (Regular) | 1.3 | 辅助文字 |

**字体族**：`'SF Pro Display', 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif`
**等宽字体**：`'SF Mono', 'Cascadia Code', 'Consolas', monospace`

---

## 间距（8pt 网格）

| Token | 值 | 用途 |
|-------|---|------|
| `space_xs` | 4px | 紧凑内间距 |
| `space_sm` | 8px | 元素间 |
| `space_md` | 12px | 组内间距 |
| `space_lg` | 16px | 组间间距 |
| `space_xl` | 24px | 面板内边距 |

---

## 组件规格

### 状态栏（Zone A）

| 属性 | 值 |
|------|---|
| 高度 | 36px |
| 背景 | `bg_glass` |
| 圆角 | 底部 12px（顶部贴窗口边缘则 0） |
| 内边距 | 0 16px |
| 字号 | Caption 11px (标签) + Body 13px (数值) |

### 控制面板（Zone B）

| 属性 | 值 |
|------|---|
| 宽度 | 260px |
| 背景 | `bg_glass` |
| 圆角 | 16px |
| 阴影 | `SHADOWS["panel"]` |
| 内边距 | 20px |
| 按钮间距 | 8px |
| 与窗口边缘间距 | 16px |

### E-Stop 按钮

| 属性 | 值 |
|------|---|
| 尺寸 | ≥ 48×48px |
| 背景 | `danger` #FF3B30, opacity 1.0 |
| 圆角 | 14px |
| 阴影 | `SHADOWS["estop"]` 红色外发光 |
| 字号 | H2 15px Semibold |
| 安全间距 | 周围 16px |
| 动画 | 无延迟（立即响应） |

### 浮动按钮（Zone D）

| 属性 | 值 |
|------|---|
| 尺寸 | 40×40px |
| 背景 | `bg_card` |
| 圆角 | 20px（圆形） |
| 阴影 | `SHADOWS["button"]` |

---

## 地图渲染（MapView + Layers）

| 图层 | 颜色 | 备注 |
|------|------|------|
| 背景 | `bg_void` #121214 | |
| 网格 | `rgba(60,60,66,0.25)` | 比 V2 更柔和 |
| 路径 | `#00E5FF` 赛博青 | 线宽 0.05 |
| 点云 | `rgba(255,100,80,0.70)` | 柔和红橙 |
| 机器人 | `accent` #0A84FF | 呼吸脉冲保留 |
| 箭头 | `#FF9500` | 交互拖拽预览 |

---

## theme.py 接口约束

- `apply_theme(app)` 函数签名不可变
- `COLORS` 字典必须存在且包含上述所有键
- 新增 `SHADOWS`、`ANIMATIONS` 字典作为公开预设
- 新增 `apply_glass_shadow(widget, preset_key)` 辅助函数

---

*本文档是 V3 UI 的参数真相源。所有 rgba、px、ms 值以此为准。*
