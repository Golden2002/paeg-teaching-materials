# -*- coding: utf-8 -*-
"""paeg_teaching_materials.tools — 真实功能节点（Tool 适配器 ⭐）。

网状联通架构（Oracle §3.110）：把 6 个 Generator + method + study_plan + research
包装为 Tool 节点，注册进 MaterialRegistry._tools，使它们：
1. 可独立调用（execute_tool MCP）
2. 可作前置环节（依赖边：research → 一切；outline → ppt；script → video）
3. 可组合编排（execute_pipeline 自动展开）

核心工具：
- ResearchTool：查资料（前置环节——所有生成的广播前置）
- PptTool / HandoutTool / ScriptTool / MindmapTool / VideoTool / ManimTool
- MethodTool（学习方法）/ StudyPlanTool（学习计划）
"""

from __future__ import annotations

from typing import Any, Dict, Type

from .core import Tool, MaterialContext, broadcast, directed, optional
from .registry import MaterialRegistry


class _GenericIn:
    """通用输入（topic/subject/learner_id）。"""
    model_json_schema = staticmethod(lambda: {
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "教学主题"},
            "subject": {"type": "string", "description": "学科"},
            "learner_id": {"type": "string", "description": "学习者 ID"},
        },
        "required": ["topic"],
    })


class _GenericOut:
    model_json_schema = staticmethod(lambda: {"type": "object"})


class GeneratorAdapter(Tool):
    """把 Generator 包装为 Tool（不改业务代码——Oracle P6 零破坏）。"""

    material_type: str = ""

    def __init__(self):
        if not self.material_type:
            raise ValueError("GeneratorAdapter 子类必须声明 material_type")

    @property
    def inputs_schema(self) -> Type:
        return _GenericIn

    @property
    def outputs_schema(self) -> Type:
        return _GenericOut

    async def __call__(self, ctx: MaterialContext, inputs: Any) -> Dict[str, Any]:
        topic = ctx.topic or (inputs.get("topic", "") if isinstance(inputs, dict) else "")
        subject = ctx.subject or "通用"
        learner_id = ctx.learner_id or "anon"
        # 注入前置查资料结果到 kw（若已有 resources）
        kw = {}
        if ctx.resources:
            kw["resources"] = ctx.resources
        # 注入前置大纲（若已有）
        if ctx.outline is not None:
            kw["outline"] = ctx.outline
        result = MaterialRegistry.generate(
            self.material_type, topic, subject, learner_id, **kw)
        return result


class ResearchTool(Tool):
    """查资料（前置环节——所有生成的广播前置 ⭐）。"""

    name = "research"
    description = "查资料：检索知识库/网络/用户资料 4 路资源（所有物料生成的前置环节）"
    produces = "resources"
    requires = []

    @property
    def inputs_schema(self) -> Type:
        return _GenericIn

    @property
    def outputs_schema(self) -> Type:
        return _GenericOut

    async def __call__(self, ctx: MaterialContext, inputs: Any) -> Dict[str, Any]:
        rp = MaterialRegistry.resources
        try:
            block = rp.collect_research_block(
                ctx.topic or "", ctx.subject or "通用",
                learner_id=ctx.learner_id, include_web=True)
        except Exception:
            block = {"user_assets": "", "kb_hits": "", "facts": "", "web_hits": "",
                     "has_any": False, "block": ""}
        ctx.set_field("resources", [block])
        return {"ok": True, "has_any": block.get("has_any", False), "resources": [block]}


class PptTool(GeneratorAdapter):
    name = "ppt"
    description = "PPT 制作（前置：查资料 + 大纲）"
    produces = "ppt_artifact"
    requires = [broadcast("research", "resources"), directed("outline", "outline")]
    material_type = "ppt"


class OutlineTool(Tool):
    """大纲生成（前置环节：PPT 制作的前提 ⭐）。"""

    name = "outline"
    description = "大纲生成（PPT 制作的前置环节）"
    produces = "outline"
    requires = [broadcast("research", "resources")]

    @property
    def inputs_schema(self) -> Type:
        return _GenericIn

    @property
    def outputs_schema(self) -> Type:
        return _GenericOut

    async def __call__(self, ctx: MaterialContext, inputs: Any) -> Dict[str, Any]:
        # 复用 PPT 生成器产出大纲部分
        result = MaterialRegistry.generate(
            "ppt", ctx.topic or "", ctx.subject or "通用", ctx.learner_id or "anon")
        ctx.set_field("outline", {"title": ctx.topic, "content": result.get("output", "")})
        return ctx.outline


class HandoutTool(GeneratorAdapter):
    name = "handout"
    description = "讲义生成（前置：查资料）"
    produces = "handout_artifact"
    requires = [broadcast("research", "resources")]
    material_type = "handout"


class ScriptTool(GeneratorAdapter):
    name = "script"
    description = "讲稿生成（前置：查资料；是教学视频制作的前置环节）"
    produces = "lecture_script"
    requires = [broadcast("research", "resources")]
    material_type = "script"


class VideoTool(GeneratorAdapter):
    name = "video"
    description = "教学视频生成（前置：查资料 + 讲稿——讲稿是视频制作的前置环节）"
    produces = "video_artifact"
    requires = [broadcast("research", "resources"), directed("script", "lecture_script")]
    material_type = "video"


class MindmapTool(GeneratorAdapter):
    name = "mindmap"
    description = "思维导图生成（前置：查资料——可选边，无资料也可生成）"
    produces = "mindmap_artifact"
    requires = [optional("research", "resources")]
    material_type = "mindmap"


class ManimTool(GeneratorAdapter):
    name = "manim"
    description = "Manim 数学动画生成（前置：查资料）"
    produces = "manim_artifact"
    requires = [broadcast("research", "resources")]
    material_type = "manim"


class MethodTool(GeneratorAdapter):
    name = "method"
    description = "学习方法建议（前置：查资料）"
    produces = "method_advice"
    requires = [broadcast("research", "resources")]
    material_type = "method"


class StudyPlanTool(GeneratorAdapter):
    name = "study_plan"
    description = "学习计划生成（前置：查资料）"
    produces = "study_plan"
    requires = [broadcast("research", "resources")]
    material_type = "study_plan"


def register_mesh_tools() -> None:
    """注册全部网状功能节点（一等公民）。"""
    MaterialRegistry.register_tool(ResearchTool())
    MaterialRegistry.register_tool(OutlineTool())
    MaterialRegistry.register_tool(PptTool())
    MaterialRegistry.register_tool(HandoutTool())
    MaterialRegistry.register_tool(ScriptTool())
    MaterialRegistry.register_tool(VideoTool())
    MaterialRegistry.register_tool(MindmapTool())
    MaterialRegistry.register_tool(ManimTool())
    MaterialRegistry.register_tool(MethodTool())
    MaterialRegistry.register_tool(StudyPlanTool())
