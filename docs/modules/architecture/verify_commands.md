# 项目验证命令速查

> **管辖 Agent：** 架构师 Agent
> **用途：** 项目级验证命令集中管理，workflow/05 中的通用模板引用此文件

---

## 静态检查

```bash
# 单文件语法检查
python -m py_compile src/目标文件.py

# 批量语法检查（全项目）
python -m compileall src/ -q

# 类型检查（可选，逐步引入）
# mypy src/目标文件.py --ignore-missing-imports
```

---

## 启动验证

```bash
# 快速启动，观察控制台是否有 ERROR
python main.py

# 仿真模式（不依赖真实机器人）
# 启动后点击 "🟢 仿真" 按钮，观察 mock 数据流是否正常
```

---

## 单元测试

```bash
# 运行特定模块测试
pytest tests/test_目标模块.py -v

# 全量测试
pytest tests/ -v

# 带覆盖率
pytest tests/ -v --cov=src
```

---

## Diff 安全审查

```bash
# 查看本次修改了哪些文件
git diff --name-only

# 确认冻结区未被修改（应无输出）
git diff --name-only -- src/network/ src/controllers/ src/core/ src/ui_v2/robot_state_hub.py

# 搜索是否误改了信号/接口
git diff | rg "\.connect\(|objectName|Signal\("
```

---

## Scope 对照表

Conventional Commits 的 scope 与模块对应：

| Scope | 对应模块 |
|-------|---------|
| `mqtt` | src/network/mqtt_agent.py |
| `ssh` | src/network/async_ssh_manager.py |
| `nav` | src/controllers/navigation_controller.py |
| `teleop` | src/controllers/teleop_controller.py |
| `workflow` | src/controllers/workflow_controller.py |
| `map` | src/controllers/map_manager.py + src/ui_v2/map/ |
| `pose` | src/controllers/pose_recorder.py |
| `store` | src/ui_v2/robot_state_hub.py |
| `models` | src/core/models.py |
| `ui` | src/ui_v2/panels/ |
| `theme` | src/ui_v2/theme.py |
| `drawer` | src/ui_v2/panels/unified_drawer.py |
| `config` | config/ + src/core/constants.py |
| `bridge` | ros/mqtt_bridge_ros2.py |
