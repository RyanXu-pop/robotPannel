# macOS 应用设计规范 (2026 版)

> **管辖 Agent：** 设计师 Agent
> **来源：** Grok Design Report — Jony Ive & Steve Jobs 设计哲学深度萃取
> **适用范围：** 桌面应用（如机器人控制面板），优先 macOS 原生感；跨平台时 fallback 到类似风格

---

## 文档概述

本规范旨在为 macOS 桌面应用开发提供全面、专业的设计指导，适用于电脑端软件（如控制面板、工具应用或创意软件）。它深受 Jony Ive 和 Steve Jobs 的设计理念影响：

- **极致简约**（Minimalism）
- **以用户为中心**（Human-Centric）
- **优雅与功能融合**（Elegance in Functionality）
- **惊喜的细节**（Delightful Details）

Jobs 强调"设计不仅仅是外观和感觉，而是如何工作"；Ive 则推崇"真实材质感"如 Liquid Glass 的光学深度和"退隐界面" Deference，让内容主导。

这份规范不只是规则列表，而是哲学框架：每个组件和细节都应服务于用户直觉，减少认知负担，创造"呼吸感"强的空间。适用于 PySide6/Qt 或 SwiftUI 等框架实现。假设目标是 2026 macOS Tahoe 26 系统，兼容 Dark/Light 模式和 VisionOS 影响的"空间计算"元素。

**文档结构：**

| 章节 | 内容 |
|------|------|
| 1. 设计原则 | 核心哲学 |
| 2. 视觉基础 | 颜色、排版、图标、材质 |
| 3. 组件规范 | 常见 UI 元素 |
| 4. 布局与交互 | 整体结构、动画、反馈 |
| 5. 最佳实践 | 常见场景、测试指南 |

---

## 1. 设计原则（The Philosophy: Ive & Jobs' Legacy）

所有设计决策必须贯彻以下原则，确保应用像"活的艺术品"一样优雅。

### 1.1 Deference（退隐与顺应）

- **理念：** 界面应退隐，让内容（e.g., 机器人地图）成为主角。Jobs 说："设计是灵魂的体现"——界面不是装饰，而是服务内容。
- **规范：**
  - 避免喧闹元素：无多余边框、线条；用留白和材质层级区分空间
  - 内容主导：90% 屏幕留给核心视图（e.g., 全屏 SLAM 地图），控件悬浮出现，只在交互时浮现
  - 示例：在机器人面板中，状态栏（电压/连接）应像 Dynamic Island 一样"呼吸"收缩，不抢地图风头

### 1.2 Clarity（清晰与可读性）

- **理念：** Ive 强调"清晰是优雅的基础"——用户一眼懂，无需说明书。Jobs 追求"简单到完美"。
- **规范：**
  - 高对比：文本/图标在任何模式下对比度 >4.5:1（WCAG AA 标准）
  - 层级分明：用字重（SF Pro Semibold vs Regular）构建信息优先级，而非颜色滥用
  - 避免歧义：每个组件有单一目的；e.g., 按钮文本简短（<5 字），图标用 SF Symbols 极简线框

### 1.3 Depth（深度与空间感）

- **理念：** Jobs/Ive 视 macOS 为"物理世界延伸"——用 Z 轴创造真实感，避免平面。
- **规范：**
  - Liquid Glass 材质：高透半透明（Translucency 70-90%），模拟玻璃折射底层内容；边缘微高光（1px solid rgba(255,255,255,0.25)）
  - 物理投影：阴影柔和大范围（blur radius 10-20px, opacity 0.1-0.3），区分前景/背景
  - 示例：悬浮面板像浮在地图上，Z 轴高于底层 2-4 层

### 1.4 Consistency（一致性与熟悉感）

- **理念：** Jobs 说"伟大设计是熟悉却惊喜"——统一风格，让用户无学习曲线。
- **规范：**
  - 系统级一致：全局用 SF Pro 字体，匹配 macOS 系统设置（Light/Dark 自动适配）
  - 跨组件统一：所有按钮圆角 12px，间距基于 8pt 栅格系统

### 1.5 Micro-Interactions（微交互与反馈）

- **理念：** Ive 追求"触感真实"——每个动作像物理响应，带来惊喜。
- **规范：**
  - 所有交互有 0.2-0.3s ease-in-out 动画（模拟阻尼/弹簧）
  - 反馈即时：hover 微光变，click 轻微缩放（scale 0.98）

### 1.6 Simplicity（极简主义）

- **理念：** Jobs 名言"简单比复杂更难"——去除一切非必需。
- **规范：**
  - 去线化：无分割线，用留白/阴影分隔
  - 信息密度控制：高密度数据用 Sparkline / 颜色，而非文本堆积

---

## 2. 视觉基础（Visual Foundations）

基础元素确保整体和谐，贯彻 Ive 的"材质真实感"。

### 2.1 颜色系统（Color System）

- **理念：** 颜色服务功能，非装饰。Jobs 偏好低饱和，Ive 强调动态适应。
- **规范：**

| 类别 | 值 | 说明 |
|------|---|------|
| 系统色 | 优先用系统语义色 | System Blue for accents, System Gray for backgrounds |
| 主色调 Light | `#F2F2F7` / `rgba(242,242,247,0.8)` | 低饱和背景 |
| 主色调 Dark | `#1C1C1E` / `rgba(28,28,30,0.8)` | 低饱和背景 |
| 强调色 | Apple Blue `#007AFF` | for actions |
| 成功色 | Green `#34C759` | for success |
| 警告/急停色 | Red `#FF3B30` | for alerts / E-Stop |
| Liquid Glass 效果 | `blur(20px)` + vibrancy | 系统级半透明 |
| 高光 | gradient from `rgba(255,255,255,0.4)` to transparent | 边缘光效 |

- **适配：** 自动支持 Light/Dark/Auto 模式；对比度始终 >7:1 for text
- **示例：** E-Stop 按钮：饱和红 (#FF3B30, opacity 1.0)，边缘外发光 (glow 2px)

### 2.2 排版（Typography）

- **理念：** Ive 视字体为"界面呼吸"——清晰、层级感强。Jobs 要求"完美像素"。
- **规范：**

| 级别 | 字体 | 字重 | 大小 | 用途 |
|------|------|------|------|------|
| Title | SF Pro (System Font) | Semibold | 28pt | headline |
| Body | SF Pro (System Font) | Regular | 17pt | main text |
| Caption | SF Pro (System Font) | Medium | 13pt | labels |

- **Hierarchy:** 用字重分级（Bold > Medium > Regular），字号差 4-8pt
- **间距：** 行高 1.2-1.4x 字号；段落间 8-16pt
- **对齐：** 左对齐为主；数字/状态居中
- **Liquid Glass 适配：** 在高透背景上用微阴影 `text-shadow: 0 1px 1px rgba(0,0,0,0.1)` 提升可读
- **Fallback 字体族：** Helvetica Neue

### 2.3 图标与图形（Icons & Graphics）

- **理念：** Jobs 说"图标是诗"——极简线框，传达本质。
- **规范：**

| 属性 | 值 |
|------|---|
| 风格 | SF Symbols (线宽 1-2pt, filled/outline) |
| 大小 | 24x24pt (standard)；hover 微缩放 1.1x |
| 颜色 | 单色匹配强调色；状态图标用渐变 (e.g., battery green to red) |
| 自定义图形 | 机器人位姿箭头用平滑曲线 (Bezier)，边缘 antialias |
| 动画 | 呼吸脉冲 (opacity 0.8-1.0, duration 1s infinite) for status icons |

### 2.4 材质与效果（Materials & Effects）

- **理念：** Ive 的 Liquid Glass：像真实玻璃，动态反射光线/底层内容。
- **规范：**

| 效果 | 值 |
|------|---|
| Translucency | 背景 `rgba(255,255,255,0.15-0.3)` + `backdrop-filter: blur(20px)` |
| 高光/折射 | 边缘 `linear-gradient (top: rgba(255,255,255,0.4), bottom: transparent)` |
| 阴影 | `drop-shadow (0 4px 12px rgba(0,0,0,0.15))`；动态随 Z 轴变 |
| 圆角 | Squircle (连续平滑)；大组件 24px，小 12px；确保同心 (nested 容器圆角一致) |

---

## 3. 组件规范（UI Components）

每个组件贯彻极简：单一目的、微反馈、空间感。

### 3.1 窗口与视图（Windows & Views）

- **理念：** Jobs 视窗口为"画布"——无边框，内容满屏。
- **规范：**

| 属性 | 值 |
|------|---|
| 主窗口 | FramelessWindowHint；背景全屏地图，控件悬浮 |
| 尺寸 | 最小 800x600；自适应屏幕，留白 24pt margins |
| 标题栏 | 隐形或胶囊形 (Dynamic Pill)，只显示模式/状态 |

- **示例：** 机器人地图视图占 100%；面板从边缘滑出 (QPropertyAnimation duration 300ms)

### 3.2 按钮（Buttons）

- **理念：** Ive 强调"触感"——像玻璃按键，受力反馈。
- **规范：**

| 属性 | 值 |
|------|---|
| 样式 | 圆角 12px；背景 Liquid Glass (translucent)；文本 SF Pro Medium 17pt |
| Normal 状态 | opacity 0.9 |
| Hover 状态 | scale 1.05 + glow |
| Pressed 状态 | scale 0.98 + darken 10% |
| 变体 | Primary (Blue filled)；Secondary (transparent border)；Destructive (Red for E-Stop) |
| 尺寸 | 最小 44x44pt (touch-friendly)；padding 12pt |

- **示例：** E-Stop：常驻左下，红色高饱和，hover 脉冲动画

### 3.3 面板与卡片（Panels & Cards）

- **理念：** Jobs 追求"无缝"——面板像从空间浮现。
- **规范：**

| 属性 | 值 |
|------|---|
| 样式 | Liquid Glass 材质；圆角 24px；阴影 blur 20px |
| 布局 | QVBoxLayout + 16pt spacing；留白 24pt padding |
| 交互 | 默认隐藏，拖拽/点击呼出 (slide-in 动画 0.3s) |

- **示例：** Telemetry 面板：悬浮右上，显示电压环形进度 + 状态灯；高密度数据用 Sparkline

### 3.4 地图与视图（Maps & Views）

- **理念：** Ive 的空间计算——地图如真实世界，控件悬浮其上。
- **规范：**

| 属性 | 值 |
|------|---|
| 渲染 | QGraphicsView 全屏；背景暗调 (Dark Mode 默认) |
| 层级 | 底层地图；中层路径/激光 (微光粒子)；上层机器人箭头 (呼吸动画) |
| 交互 | 捏合缩放 (pinch gesture)；拖拽位姿箭头 (snap to grid) |

- **示例：** SLAM 地图占 90% 屏；激光点云用渐变颜色 (绿近红远)

### 3.5 指示器与状态（Indicators & Status）

- **理念：** Jobs 强调"即时反馈"——状态如生命迹象。
- **规范：**

| 元素 | 实现方式 |
|------|---------|
| 进度 | 环形 (QProgressBar styled as circle)；颜色渐变 |
| 状态灯 | 圆形图标，呼吸动画 (opacity cycle) for alive |
| 警报 | 红色脉冲 + haptic (系统振动) |

- **示例：** 连接状态：绿灯呼吸；断开：红灯常亮 + 面板浮现

---

## 4. 布局与交互（Layout & Interactions）

| 维度 | 规范 |
|------|------|
| 栅格系统 | 8pt 基础网格；所有间距/尺寸倍数 |
| 留白 | 宽敞 padding (24-48pt) 创造"呼吸感" |
| 动画 | 所有过渡 0.2-0.5s ease-in-out；模拟物理 (QSpringAnimation for bounce) |
| 手势 | 支持 trackpad：两指滚动地图、三指滑动面板 |
| 无界感 | 去线化；用阴影/模糊分隔空间 |

---

## 5. 最佳实践（Best Practices）

| 维度 | 实践 |
|------|------|
| 测试 | 视觉回归测试 (screenshot compare)；用户测试焦点组（5人，测直觉性） |
| 常见场景 | 机器人控制：地图全屏，面板悬浮；紧急时 E-Stop 放大浮现 |
| 可访问性 | VoiceOver 支持；动态字体大小 |
| 迭代 | 每版本 A/B 测试 2-3 设计变体，选用户反馈最佳 |

---

## 与现有文档的关系

| 文档 | 关系 |
|------|------|
| [design_principles.md](design_principles.md) | 本文提供更细粒度的原则阐释，与其互补 |
| [design_system.md](design_system.md) | 本文的参数值应与 design_system 保持一致；冲突时以 design_system 为准（因其直接对应 theme.py） |

---

*本规范非静态——随 macOS 更新迭代。贯彻 Ive/Jobs：设计是"如何让用户惊喜"。如需实现示例代码，参考 Apple Developer 资源。*
