"""数据模型定义"""
from dataclasses import dataclass, field
from datetime import date
from typing import Optional
import json
import os


@dataclass
class SprintConfig:
    """Sprint 配置的结构化表示"""
    name: str = ""
    start_date: str = ""
    end_condition: str = ""
    goal: str = ""
    whitelist: list[str] = field(default_factory=list)
    blacklist: list[str] = field(default_factory=list)
    redlines: list[str] = field(default_factory=list)
    dod_items: list[str] = field(default_factory=list)
    verify_commands: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class FileEntry:
    """仪表盘中的文件条目"""
    path: str
    name: str
    description: str
    agent: str  # "architect" | "designer" | "shared"
    category: str  # "rules" | "workflow" | "architecture" | "taste"


@dataclass
class TaskItem:
    """看板任务卡片"""
    id: str
    title: str
    description: str = ""
    priority: str = "medium"  # "high" | "medium" | "low"
    status: str = "todo"  # "todo" | "in_progress" | "done"
    created_at: str = ""
    linked_file: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at,
            "linked_file": self.linked_file,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TaskItem":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class TaskStore:
    """任务持久化存储"""

    def __init__(self, path: str):
        self._path = path
        self._tasks: list[TaskItem] = []
        self.load()

    def load(self):
        if os.path.exists(self._path):
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._tasks = [TaskItem.from_dict(d) for d in data]
            except (json.JSONDecodeError, KeyError):
                self._tasks = []
        else:
            self._tasks = []

    def save(self):
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump([t.to_dict() for t in self._tasks], f, ensure_ascii=False, indent=2)

    @property
    def tasks(self) -> list[TaskItem]:
        return self._tasks

    def add(self, task: TaskItem):
        self._tasks.append(task)
        self.save()

    def remove(self, task_id: str):
        self._tasks = [t for t in self._tasks if t.id != task_id]
        self.save()

    def update(self, task: TaskItem):
        for i, t in enumerate(self._tasks):
            if t.id == task.id:
                self._tasks[i] = task
                break
        self.save()

    def get_by_status(self, status: str) -> list[TaskItem]:
        return [t for t in self._tasks if t.status == status]
