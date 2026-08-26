# -*- coding: utf-8 -*-
"""网状联通核心测试（Oracle §3.110 ⭐）：Tool/Context/Edges/Pipeline/Resolver/Registry。"""
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import pytest

from paeg_teaching_materials.core import (
    Tool, MaterialContext, Dependency, broadcast, directed, optional,
    Pipeline, Resolver,
)
from paeg_teaching_materials import MaterialRegistry


# ─────────────────────────────────────
# 1. MaterialContext（类型化 Blackboard + reducer）
# ─────────────────────────────────────
class TestMaterialContext:
    def test_topic_init(self):
        ctx = MaterialContext(topic="一元二次方程", subject="数学")
        assert ctx.topic == "一元二次方程"
        assert ctx.subject == "数学"

    def test_resources_append(self):
        """resources 字段 append 累积。"""
        ctx = MaterialContext()
        ctx.set_field("resources", ["资料1"])
        ctx.set_field("resources", ["资料2", "资料3"])
        assert ctx.resources == ["资料1", "资料2", "资料3"]

    def test_outline_replace(self):
        """outline 字段 replace 覆盖。"""
        ctx = MaterialContext()
        ctx.set_field("outline", {"v": 1})
        ctx.set_field("outline", {"v": 2})
        assert ctx.outline == {"v": 2}

    def test_completed_stages_union(self):
        ctx = MaterialContext()
        ctx.mark_completed("research")
        ctx.mark_completed("outline")
        ctx.mark_completed("research")
        assert ctx.completed_stages == {"research", "outline"}
        assert ctx.is_completed("research")

    def test_artifacts_merge(self):
        ctx = MaterialContext()
        ctx.set_field("artifacts", {"ppt": "a.pptx"})
        ctx.set_field("artifacts", {"script": "b.md"})
        assert ctx.artifacts == {"ppt": "a.pptx", "script": "b.md"}


# ─────────────────────────────────────
# 2. Tool + 组合（__or__ / __rshift__）
# ─────────────────────────────────────
class _SimpleIn:
    model_json_schema = staticmethod(lambda: {"type": "object"})


class _SimpleOut:
    pass


class ResearchTool(Tool):
    name = "research"
    description = "查资料（前置环节）"
    produces = "resources"
    requires = []

    def inputs_schema(self):
        return _SimpleIn

    def outputs_schema(self):
        return _SimpleOut

    async def __call__(self, ctx, inputs):
        ctx.set_field("resources", [f"资料:{ctx.topic or inputs.get('topic', '')}"])
        return {"ok": True, "resources": ctx.resources}


class OutlineTool(Tool):
    name = "outline"
    description = "大纲（前置环节）"
    produces = "outline"
    requires = [broadcast("research", "resources")]

    def inputs_schema(self):
        return _SimpleIn

    def outputs_schema(self):
        return _SimpleOut

    async def __call__(self, ctx, inputs):
        # 消费前置产物
        assert ctx.resources, "前置查资料必须已执行"
        ctx.set_field("outline", {"title": ctx.topic or inputs.get("topic", ""), "resources": len(ctx.resources)})
        return ctx.outline


class PPTTool(Tool):
    name = "ppt"
    description = "PPT 制作（消费大纲）"
    produces = "ppt_artifact"
    requires = [directed("outline", "outline")]

    def inputs_schema(self):
        return _SimpleIn

    def outputs_schema(self):
        return _SimpleOut

    async def __call__(self, ctx, inputs):
        assert ctx.outline, "前置大纲必须已执行"
        return {"ok": True, "ppt": f"{ctx.outline['title']}.pptx"}


class TestToolComposition:
    def test_or_creates_pipeline(self):
        p = ResearchTool() | OutlineTool()
        assert isinstance(p, Pipeline)
        assert len(p.steps) == 2

    def test_rshift_same(self):
        p = ResearchTool() >> OutlineTool()
        assert isinstance(p, Pipeline)
        assert len(p.steps) == 2

    def test_pipeline_chain_3(self):
        p = ResearchTool() | OutlineTool() | PPTTool()
        assert len(p.steps) == 3

    def test_pipeline_executes_with_context(self):
        """组合执行：前置产物自动传递。"""
        import asyncio
        p = ResearchTool() | OutlineTool() | PPTTool()
        ctx = MaterialContext(topic="导数")
        result = asyncio.run(p(ctx, {"topic": "导数"}))
        assert result["ppt"] == "导数.pptx"
        assert "research" in ctx.completed_stages
        assert "outline" in ctx.completed_stages
        assert ctx.resources == ["资料:导数"]
        assert ctx.outline["resources"] == 1


# ─────────────────────────────────────
# 3. Resolver（依赖解析 + 循环检测）
# ─────────────────────────────────────
class TestResolver:
    def test_build_plan_topological(self):
        """反向追溯：target=ppt 展开 research→outline→ppt。"""
        tools = {
            "research": ResearchTool(),
            "outline": OutlineTool(),
            "ppt": PPTTool(),
        }
        r = Resolver(tools)
        plan = r.build_plan("ppt")
        names = [s.tool.name for s in plan.steps]
        assert names == ["research", "outline", "ppt"]  # 拓扑序：前置在前

    def test_dependency_graph(self):
        tools = {"research": ResearchTool(), "outline": OutlineTool(), "ppt": PPTTool()}
        r = Resolver(tools)
        g = r.dependency_graph()
        assert g["ppt"]["requires"][0]["source"] == "outline"
        assert g["outline"]["requires"][0]["source"] == "research"

    def test_unknown_target(self):
        r = Resolver({"research": ResearchTool()})
        with pytest.raises(ValueError):
            r.build_plan("unknown")


# ─────────────────────────────────────
# 4. Registry Tool 槽（P2）
# ─────────────────────────────────────
class TestRegistryTools:
    def test_register_tool(self):
        MaterialRegistry.register_tool(ResearchTool())
        MaterialRegistry.register_tool(OutlineTool())
        MaterialRegistry.register_tool(PPTTool())
        assert "research" in MaterialRegistry.available_tools()
        assert "outline" in MaterialRegistry.available_tools()
        assert "ppt" in MaterialRegistry.available_tools()

    def test_execute_tool_single(self):
        """独立调用单个 Tool（双暴露模式 1）。"""
        import asyncio
        ctx = MaterialContext(topic="向量")
        result = asyncio.run(MaterialRegistry.execute_tool("research", ctx, {"topic": "向量"}))
        assert result["ok"] is True
        assert ctx.resources == ["资料:向量"]

    def test_execute_plan_auto(self):
        """网状编排：target=ppt 自动展开依赖（双暴露模式 2）。"""
        ctx = MaterialContext(topic="极限")
        result = MaterialRegistry.execute_plan("ppt", ctx, {"topic": "极限"})
        assert result["ppt"] == "极限.pptx"
        assert "research" in ctx.completed_stages
        assert "outline" in ctx.completed_stages


# ─────────────────────────────────────
# 5. MCP 双暴露（P5）
# ─────────────────────────────────────
class TestMcpMeshTools:
    pytest.importorskip("fastmcp")

    def test_execute_tool_mcp(self):
        """MCP 独立调用单个节点。"""
        import asyncio
        from paeg_teaching_materials.mcp_server import build_server
        mcp = build_server()
        r = asyncio.run(mcp.call_tool("execute_tool", {"tool_name": "research", "topic": "向量"}))
        assert r.is_error is False
        assert '"ok": true' in r.content[0].text

    def test_execute_pipeline_mcp(self):
        """MCP 网状编排自动展开依赖。"""
        import asyncio
        from paeg_teaching_materials.mcp_server import build_server
        mcp = build_server()
        r = asyncio.run(mcp.call_tool("execute_pipeline", {"target": "ppt", "topic": "导数"}))
        assert r.is_error is False
        assert "research" in r.content[0].text  # 自动执行前置查资料

    def test_list_dependencies_mcp(self):
        """MCP 依赖图自省。"""
        import asyncio
        from paeg_teaching_materials.mcp_server import build_server
        mcp = build_server()
        r = asyncio.run(mcp.call_tool("list_dependencies", {}))
        assert r.is_error is False
        assert '"graph"' in r.content[0].text

    def test_mcp_tools_count_increased(self):
        """MCP 工具数增至 15（12 + execute_tool/execute_pipeline/list_dependencies）。"""
        import asyncio
        from paeg_teaching_materials.mcp_server import build_server
        mcp = build_server()
        tools = asyncio.run(mcp.list_tools())
        names = {t.name for t in tools}
        assert "execute_tool" in names
        assert "execute_pipeline" in names
        assert "list_dependencies" in names
        assert len(names) >= 15
