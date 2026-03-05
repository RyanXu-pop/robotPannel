# 00 — Agent 驱动快速上手

> **你唯一需要做的事：告诉 Agent 你要什么。**
> 规则、约束、验证全部由 Agent 自己读文件执行。

---

## 每日三句话

### 1️⃣ 提需求 → 出蓝图

```
读 @.cursorrules @.sprint @docs/modules/architecture/system_overview.md

我要 [一句话描述需求]。

先按 @workflow/02_architect_prompt_template.md 输出架构师蓝图，不要写代码。
```

> 如果涉及 UI/视觉，蓝图通过后再追加：
> ```
> 按 @workflow/03_designer_prompt_template.md 输出设计师方案。
> 参考 @docs/modules/taste/design_system.md
> ```

### 2️⃣ 审蓝图 → 逐步执行

审完蓝图点头后：

```
执行蓝图 Step {N}。严格遵守 @.sprint 的白名单和冻结区。
```

> 一次一个 Step，每个 Step 只改 1~2 个文件。

### 3️⃣ 验证 → 提交

每个 Step 完成后：

```
按 @.sprint 的验证命令做安全检查，确认冻结区零修改。
通过后用 Conventional Commits 格式提交。
```

---

## Sprint 操作

### 新建 Sprint

```
读 @.cursorrules @.sprint
新 Sprint 目标：[xxx]
帮我更新 .sprint 文件的目标、白名单、黑名单和 DoD。
```

### 切换 Sprint

```
上个 Sprint 已完成。读 @.sprint，新 Sprint 目标是 [xxx]。
更新 .sprint，保留长期红线，清空旧的白名单/黑名单。
```

---

## @引用速查

| 你要做什么 | @引用这些文件 |
|-----------|--------------|
| 提任何需求 | `@.cursorrules` `@.sprint` |
| 架构/后端 | + `@docs/modules/architecture/system_overview.md` |
| UI/视觉 | + `@docs/modules/taste/design_system.md` `@docs/modules/taste/design_principles.md` |
| 确认信号接口 | + `@docs/modules/architecture/ui_signals.md` |
| 确认冻结 API | + `@docs/modules/architecture/frozen_backend.md` |

---

## 异常处理

| 情况 | 你说 |
|------|------|
| Agent 改了冻结区 | "撤回，你修改了冻结区。重新执行，只改白名单内的文件。" |
| 蓝图的某步不可行 | "Step N 技术上不可行，原因是 [xxx]。修改蓝图。" |
| Agent 幻觉（编造 API） | 清空上下文，新对话重新开始，显式 @引用目标文件 |
| 想回滚 | "回滚最近一次提交：`git revert HEAD`" |

---

*你是 Tech Lead，Agent 是执行者。你审核它的蓝图，然后说"执行"。*
