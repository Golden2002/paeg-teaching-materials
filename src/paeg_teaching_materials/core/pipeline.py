# -*- coding: utf-8 -*-
"""paeg_teaching_materials.core.pipeline — 组合管线（__or__ 模式 ⭐）。

网状联通架构（Oracle §3.110）：多个 Tool 通过 | 组合成 Pipeline，
组合结果本身仍是 Tool（可继续 | 递归组合）——"独立/组合"同构。

对标：LangChain RunnableSequence（r1 | r2 → RunnableSequence(r1, r2)）。
"""

from __future__ import annotations

import abc
from typing import Any, List, Type

from .tool import Tool
from .context import MaterialContext


class Pipeline(Tool):
    """组合工具：多个 Tool 顺序执行，前序输出作为后序输入。"""

    def __init__(self, steps: List[Tool], name: str = ""):
        if not steps:
            raise ValueError("Pipeline 至少需要 1 个步骤")
        self.steps = steps
        self.name = name or "→".join(s.name for s in steps)
        self.description = f"管线：{' → '.join(s.name for s in steps)}"
        # 组合的 produces = 最后一步的 produces
        self.produces = steps[-1].produces
        # 组合的 requires = 所有步骤 requires 的并集（去重）
        seen = set()
        reqs = []
        for s in steps:
            for d in s.requires:
                key = (d.source, d.field, d.mode)
                if key not in seen:
                    seen.add(key)
                    reqs.append(d)
        self.requires = reqs

    # ── schema 推导 ──
    @property
    def inputs_schema(self) -> Type:
        return self.steps[0].inputs_schema

    @property
    def outputs_schema(self) -> Type:
        return self.steps[-1].outputs_schema

    # ── 执行 ──
    async def __call__(self, ctx: MaterialContext, inputs: Any) -> Any:
        current = inputs
        for step in self.steps:
            # 每步执行后标记完成（供 Resolver 跳过已满足依赖）
            ctx.mark_completed(step.name)
            current = await step(ctx, current)
            # 若步骤声明了 produces 且未写入（Tool 内部未 set_field），写入 ctx
            # 注意：Tool 内部通常已自行 set_field；此处只兜底未写的场景。
            # 判断依据：字段为空/未变 且 current 不是该字段本身
            if step.produces:
                existing = ctx.get_field(step.produces)
                if existing is None:
                    ctx.set_field(step.produces, current)
        return current

    # ── 组合继续 ──
    def __or__(self, other: Tool) -> "Pipeline":
        return Pipeline([*self.steps, other])

    def __rshift__(self, other: Tool) -> "Pipeline":
        return self.__or__(other)

    def __repr__(self) -> str:
        return f"<Pipeline {' → '.join(s.name for s in self.steps)}>"
