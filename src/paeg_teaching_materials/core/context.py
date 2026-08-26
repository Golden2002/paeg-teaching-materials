# -*- coding: utf-8 -*-
"""paeg_teaching_materials.core.context — 类型化 Blackboard（MaterialContext ⭐）。

网状联通架构（Oracle §3.110）：节点间通过共享的 MaterialContext 传递中间产物，
每个字段有显式 reducer 决定合并语义。

设计对标：LangGraph StateGraph（共享状态 + 字段级 reducer）。

Reducer 三大语义：
- append（累积）：resources（多次收集资料累加）
- replace（覆盖）：outline / script / ppt_outline（最后一次胜出）
- union（并集）：completed_stages / artifacts

用法：
    ctx = MaterialContext(topic="一元二次方程")
    ctx.set_field("resources", [r1, r2])     # append
    ctx.set_field("outline", outline)        # replace
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, ClassVar, Dict, List, Optional, Set


@dataclass
class MaterialContext:
    """物料生成共享上下文（类型化 Blackboard）。"""

    # ── 用户输入 ──
    topic: Optional[str] = None
    subject: str = "通用"
    grade: Optional[str] = None
    learner_id: str = "anon"

    # ── 中间产物槽（带 reducer）──
    resources: List[Any] = field(default_factory=list)          # 查资料（append）
    outline: Optional[Any] = None                                # 大纲（replace）
    lecture_script: Optional[Any] = None                         # 讲稿（replace）
    ppt_outline: Optional[Any] = None                            # PPT 大纲（replace）
    lecture_outline: Optional[Any] = None                        # 讲义大纲（replace）
    mindmap_outline: Optional[Any] = None                        # 思维导图大纲（replace）

    # ── 元数据 ──
    completed_stages: Set[str] = field(default_factory=set)     # 已完成阶段（union）
    artifacts: Dict[str, Any] = field(default_factory=dict)     # 产物映射（merge）
    tool_versions: Dict[str, str] = field(default_factory=dict) # 工具版本（merge）

    # ── Reducer 表（字段 → 合并语义）──
    _REDUCERS: ClassVar[Dict[str, Callable[[Any, Any], Any]]] = {
        "resources": lambda old, new: [*old, *(new or [])],           # append
        "completed_stages": lambda old, new: old | set(new or []),    # union
        "artifacts": lambda old, new: {**(old or {}), **(new or {})}, # merge
        "tool_versions": lambda old, new: {**(old or {}), **(new or {})},
        # 其余字段默认 replace（由 set_field 处理）
    }

    # ── 字段访问（带 reducer）──
    def set_field(self, name: str, value: Any) -> None:
        """写入字段，按 reducer 合并。"""
        if name in self._REDUCERS:
            old = getattr(self, name, None)
            setattr(self, name, self._REDUCERS[name](old, value))
        else:
            setattr(self, name, value)

    def get_field(self, name: str, default: Any = None) -> Any:
        return getattr(self, name, default)

    # ── 阶段标记 ──
    def mark_completed(self, stage: str) -> None:
        self.completed_stages.add(stage)

    def is_completed(self, stage: str) -> bool:
        return stage in self.completed_stages

    # ── 序列化 ──
    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "subject": self.subject,
            "grade": self.grade,
            "learner_id": self.learner_id,
            "completed_stages": sorted(self.completed_stages),
            "artifacts": {k: str(v) if isinstance(v, Path) else v
                          for k, v in self.artifacts.items()},
        }
