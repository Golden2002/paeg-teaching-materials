# -*- coding: utf-8 -*-
"""paeg_teaching_materials.core.tool — 功能节点抽象（Tool[Input, Output] ⭐）。

网状联通架构（Oracle §3.110 ⭐）：每个功能是一等公民节点——
既可独立调用（MCP 工具），也可作为其他功能的前置环节（DAG 编排）。

设计对标：LangChain Runnable 的 `__or__` 组合（组合结果仍是 Tool）。

用法：
    class MyTool(Tool[MyIn, MyOut]):
        name = "my_tool"
        description = "..."
        produces = "my_out"          # 写入 MaterialContext 的字段
        requires = [Dependency("research", "resources", mode="broadcast")]

        def inputs_schema(self): return MyIn
        def outputs_schema(self): return MyOut

        async def __call__(self, ctx, inputs): ...
"""

from __future__ import annotations

import abc
from typing import Any, ClassVar, Generic, List, Optional, Type, TypeVar

from .edges import Dependency
from .context import MaterialContext

TIn = TypeVar("TIn")
TOut = TypeVar("TOut")


class Tool(Generic[TIn, TOut], abc.ABC):
    """功能节点：类型化输入/输出 + 依赖声明 + 独立/组合双模式。"""

    name: ClassVar[str] = ""
    description: ClassVar[str] = ""
    produces: ClassVar[Optional[str]] = None      # 写入 MaterialContext 的字段
    requires: ClassVar[List[Dependency]] = []      # 前置依赖边

    # ── schema（子类实现）──
    @property
    @abc.abstractmethod
    def inputs_schema(self) -> Type[TIn]:
        """输入类型（Pydantic 模型 → JSON Schema）。"""
        ...

    @property
    @abc.abstractmethod
    def outputs_schema(self) -> Type[TOut]:
        """输出类型（Pydantic 模型 → JSON Schema）。"""
        ...

    # ── 执行（子类实现核心逻辑）──
    @abc.abstractmethod
    async def __call__(self, ctx: MaterialContext, inputs: TIn) -> TOut:
        """执行工具。ctx 为共享 Blackboard（读前置产物），inputs 为本次输入。"""
        ...

    # ── 组合（LangChain Runnable __or__ 模式）──
    def __or__(self, other: "Tool") -> "Tool":
        """r1 | r2 → Pipeline（组合结果仍是 Tool，可继续 | 递归组合）。"""
        from .pipeline import Pipeline
        return Pipeline([self, other])

    def __rshift__(self, other: "Tool") -> "Tool":
        """r1 >> r2 同义于 |（更贴近"前置"语义）。"""
        return self.__or__(other)

    # ── MCP 双暴露 ──
    def to_mcp_schema(self) -> dict:
        """自动生成 MCP 工具描述（inputSchema 从 Pydantic 推导）。"""
        try:
            in_schema = self.inputs_schema.model_json_schema()
        except Exception:
            in_schema = {"type": "object", "properties": {}, "required": []}
        return {
            "name": f"tool_{self.name}",
            "description": self.description,
            "inputSchema": {"type": "object", "properties": in_schema.get("properties", {}),
                            "required": in_schema.get("required", [])},
            "produces": self.produces,
            "requires": [{"source": d.source, "field": d.field, "mode": d.mode}
                         for d in self.requires],
        }

    # ── 辅助 ──
    @property
    def dependencies(self) -> List[Dependency]:
        return list(self.requires)

    def __repr__(self) -> str:
        return f"<Tool {self.name} requires={[d.source for d in self.requires]}>"
