"""解析 .sprint 文件为结构化数据，支持回写"""
import re
from tools.workflow_manager.models import SprintConfig


def parse_sprint(path: str) -> SprintConfig:
    """读取 .sprint 文件并解析为 SprintConfig"""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    config = SprintConfig()

    # Sprint 名称
    m = re.search(r"# Sprint[：:]\s*(.+)", text)
    if m:
        config.name = m.group(1).strip()

    # 生效日期
    m = re.search(r"# 生效日期[：:]\s*(.+)", text)
    if m:
        config.start_date = m.group(1).strip()

    # 到期条件
    m = re.search(r"# 到期条件[：:]\s*(.+)", text)
    if m:
        config.end_condition = m.group(1).strip()

    # Sprint 目标 (between 目标 header and next section)
    goal_match = re.search(
        r"# =+ Sprint 目标 =+\n(.*?)(?=\n# =+)",
        text, re.DOTALL
    )
    if goal_match:
        lines = [l.lstrip("# ").strip() for l in goal_match.group(1).strip().splitlines() if l.strip() and not l.strip().startswith("# ==")]
        config.goal = "\n".join(lines)

    # 白名单
    wl_match = re.search(
        r"# =+ 修改范围（白名单） =+\n(.*?)(?=\n# =+)",
        text, re.DOTALL
    )
    if wl_match:
        for line in wl_match.group(1).splitlines():
            line = line.strip().lstrip("#").strip()
            if line and not line.startswith("==") and not line.startswith("只有"):
                config.whitelist.append(line)

    # 黑名单
    bl_match = re.search(
        r"# =+ 冻结区（黑名单） =+\n(.*?)(?=\n# =+)",
        text, re.DOTALL
    )
    if bl_match:
        for line in bl_match.group(1).splitlines():
            line = line.strip().lstrip("#").strip()
            if line and not line.startswith("==") and not line.startswith("以下") and not line.startswith("详细"):
                config.blacklist.append(line)

    # 红线
    rl_match = re.search(
        r"# =+ Sprint 红线.*?=+\n(.*?)(?=\n# =+)",
        text, re.DOTALL
    )
    if rl_match:
        for line in rl_match.group(1).splitlines():
            line = line.strip().lstrip("#").strip()
            if line.startswith("✗"):
                config.redlines.append(line.lstrip("✗").strip())

    # DoD
    dod_match = re.search(
        r"# =+ Sprint DoD.*?=+\n(.*?)(?=\n# =+)",
        text, re.DOTALL
    )
    if dod_match:
        for line in dod_match.group(1).splitlines():
            line = line.strip().lstrip("#").strip()
            if line.startswith("□"):
                config.dod_items.append(line.lstrip("□").strip())

    # 验证命令
    vc_match = re.search(
        r"# =+ Sprint 验证命令 =+\n(.*?)$",
        text, re.DOTALL
    )
    if vc_match:
        for line in vc_match.group(1).splitlines():
            line = line.strip().lstrip("#").strip()
            if "：" in line or ":" in line:
                sep = "：" if "：" in line else ":"
                parts = line.split(sep, 1)
                if len(parts) == 2:
                    config.verify_commands.append((parts[0].strip(), parts[1].strip()))

    return config


def write_sprint(config: SprintConfig, path: str) -> None:
    """将 SprintConfig 回写为 .sprint 文件"""
    lines = []
    lines.append("# ============================================================")
    lines.append("# .sprint — 当前 Sprint 约束（时效性文件，随 Sprint 切换而更新）")
    lines.append("# ============================================================")
    lines.append("# Sprint：" + config.name)
    lines.append("# 生效日期：" + config.start_date)
    lines.append("# 到期条件：" + config.end_condition)
    lines.append("")

    lines.append("# ==================== Sprint 目标 ====================")
    for gl in config.goal.splitlines():
        lines.append("# " + gl)
    lines.append("")

    lines.append("# ==================== 修改范围（白名单） ====================")
    lines.append("# 以下文件/范围允许修改：")
    lines.append("#")
    for item in config.whitelist:
        lines.append("#   " + item)
    lines.append("")

    lines.append("# ==================== 冻结区（黑名单） ====================")
    lines.append("# 以下区域本 Sprint 不可修改，详细 API 见 docs/modules/architecture/frozen_backend.md")
    lines.append("#")
    for item in config.blacklist:
        lines.append("#   " + item)
    lines.append("")

    lines.append("# ==================== Sprint 红线（违反即 REJECT） ====================")
    lines.append("#")
    for item in config.redlines:
        lines.append("# ✗ " + item)
    lines.append("#")
    lines.append("# 详细 Signal 契约 → docs/modules/architecture/ui_signals.md")
    lines.append("")

    lines.append("# ==================== Sprint DoD（附加检查项） ====================")
    lines.append("# 以下为本 Sprint 的额外验收标准，叠加在 .cursorrules 的通用 DoD 之上：")
    lines.append("#")
    for item in config.dod_items:
        lines.append("# □ " + item)
    lines.append("")

    lines.append("# ==================== Sprint 验证命令 ====================")
    for name, cmd in config.verify_commands:
        lines.append("# " + name + "：  " + cmd)

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
