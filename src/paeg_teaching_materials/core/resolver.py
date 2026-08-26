# -*- coding: utf-8 -*-
"""paeg_teaching_materials.core.resolver — 依赖解析器（拓扑排序 + ExecutionPlan ⭐）。

网状联通架构（Oracle §3.110）：给定目标工具，反向追溯 requires 展开 DAG，
拓扑排序生成执行计划；检测循环依赖并报错。

对标：Airflow TaskFlow 自动依赖推断 + Dagster GraphDefinition 声明式图。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from .tool import Tool


@dataclass
class ExecutionStep:
    """执行计划中的一步。"""
    tool: Tool
    satisfied: List[str] = field(default_factory=list)   # 已满足的依赖


@dataclass
class ExecutionPlan:
    """有序执行计划。"""
    steps: List[ExecutionStep] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)     # 已满足被跳过的（optional）

    def __repr__(self) -> str:
        return f"<ExecutionPlan {' → '.join(s.tool.name for s in self.steps)}>"


class Resolver:
    """从 Tool 注册表解析依赖图。"""

    def __init__(self, tools: Dict[str, Tool]):
        self._tools = tools

    def build_plan(self, target: str, ctx=None,
                   skip_optional_missing: bool = True) -> ExecutionPlan:
        """反向追溯 target 的 requires，拓扑排序生成执行计划。

        Args:
            target: 目标工具名。
            ctx: MaterialContext（可选，检测已满足字段跳过步骤）。
            skip_optional_missing: optional 边缺失时跳过（默认 True）。
        """
        if target not in self._tools:
            raise ValueError(f"未知工具: {target}（可用: {sorted(self._tools.keys())}）")

        # 1. 反向收集依赖子图（DFS）
        needed: List[Tool] = []
        visited: Set[str] = set()
        visiting: Set[str] = set()

        def _collect(name: str) -> None:
            if name in visited:
                return
            if name in visiting:
                raise ValueError(f"检测到循环依赖: {name}（{sorted(visiting)} 环）")
            visiting.add(name)
            tool = self._tools[name]
            for dep in tool.requires:
                src = dep.source
                # optional 缺失且跳过 → 不展开
                if dep.mode == "optional" and src not in self._tools and skip_optional_missing:
                    continue
                if src not in self._tools:
                    continue
                _collect(src)
            visiting.remove(name)
            visited.add(name)
            needed.append(tool)

        _collect(target)

        # 2. 拓扑排序（依赖在前）——needed 已是后序，反转即拓扑序
        # 但需处理同层（无相互依赖的可并行，此处保守串行）
        plan = ExecutionPlan()
        for tool in needed:
            # 检查已满足字段（ctx 已有该 produces 的有效值 → 跳过）
            if ctx is not None and tool.produces:
                existing = ctx.get_field(tool.produces)
                # 空容器视为未满足（resources=[] / artifacts={} 仍需执行）
                _has_value = existing is not None
                if _has_value and isinstance(existing, (list, dict, set)):
                    _has_value = len(existing) > 0
                if _has_value:
                    plan.skipped.append(tool.name)
                    continue
            satisfied = [d.source for d in tool.requires
                         if d.source in self._tools]
            plan.steps.append(ExecutionStep(tool=tool, satisfied=satisfied))
        return plan

    def dependency_graph(self) -> Dict[str, Dict]:
        """全网依赖图（供 list_dependencies MCP 工具）。"""
        graph = {}
        for name, tool in self._tools.items():
            graph[name] = {
                "produces": tool.produces,
                "requires": [{"source": d.source, "field": d.field, "mode": d.mode}
                             for d in tool.requires],
            }
        return graph
