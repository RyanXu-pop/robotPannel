# Vibe Coding 标准工作流 (SOP)

> **核心理念：Plan First, Code Second.**
> 永远不要让 AI 一上来就生成代码，必须先输出架构设计与修改清单。

---

## 双 Agent 系统

| Agent | 角色 | 何时激活 |
|-------|------|---------|
| 架构师 Agent | 工程严谨、安全、可扩展性 | 所有任务（新功能/重构/修复/UI 升级） |
| 设计师 Agent | 极致品味、用户体验 | **仅**涉及 UI/视觉变更时 |

> 纯后端任务、纯 Bug 修复不需要设计师 Agent，直接从阶段二跳到阶段四。

---

## 工作流（按任务类型选择路径）

```mermaid
flowchart TD
    S1["阶段一：上下文锚定 (.cursorrules + .sprint + 模块文档)"]
    S2["阶段二：架构师蓝图 (实施蓝图 + 安全边界标注)"]
    S3["阶段三：设计师方案 (视觉方案 + 样式与动画)"]
    S4["阶段四：执行与提交 (模块化执行 + 原子 Commit)"]

    S1 --> S2
    S2 -->|涉及 UI 或视觉| S3
    S2 -->|纯后端 或 Bug 修复| S4
    S3 --> S4
```

---

## 文档索引

| 文件 | 用途 | 何时使用 |
|------|------|----------|
| [01_project_context_template.md](01_project_context_template.md) | 项目上下文填写模板 | 新项目初始化时填写 |
| [02_architect_prompt_template.md](02_architect_prompt_template.md) | 架构师 Agent Prompt 模板 | 向架构师提需求时复制使用 |
| [03_designer_prompt_template.md](03_designer_prompt_template.md) | 设计师 Agent Prompt 模板 | 架构师蓝图完成后，**仅 UI 任务** |
| [04_executor_guide.md](04_executor_guide.md) | 执行者操作手册 | 在 IDE 中逐步实施时参考 |
| [05_verify_and_commit.md](05_verify_and_commit.md) | 验证与提交规范 | 每完成一步后执行 |

---

## 快速上手

```mermaid
flowchart TD
    S1["1. 确认上下文 (.cursorrules + .sprint + docs/modules)"] --> S2
    S2["2. 架构师蓝图 (02：安全边界 + 分步计划)"] --> Q
    Q{"是否涉及 UI 或视觉"}
    Q -->|是| S3["3. 设计师方案 (03：视觉参数与样式代码)"]
    Q -->|否| S4["跳过设计师，直接执行"]
    S3 --> S4["4. 逐步执行 (04：每步 1~2 个文件)"]
    S4 --> S5["5. 验证与提交 (05：Diff 安全审查)"]
    S5 --> S6{"所有 Step 是否完成"}
    S6 -->|否，继续执行| S4
    S6 -->|是，进入集成测试| S7["集成测试并合并主分支"]
```

---

## 配套体系

| 位置 | 作用 | 稳定性 |
|------|------|--------|
| `.cursorrules` | 长期 AI 规则（架构/编码/禁止事项） | 跨 Sprint 稳定 |
| `.sprint` | 当前 Sprint 约束（修改范围/冻结区/专项 DoD） | 随 Sprint 更新 |
| `docs/modules/architecture/` | 架构 Agent 管辖（冻结后端、信号契约） | 架构变更时更新 |
| `docs/modules/taste/` | 设计 Agent 管辖（品味原则、设计系统、Apple 设计规范） | 设计语言变更时更新 |

> `workflow/` = **怎么做**（通用方法论）
> `docs/modules/` = **做什么**（项目知识）
> `.sprint` = **这轮做什么**（时效约束）
