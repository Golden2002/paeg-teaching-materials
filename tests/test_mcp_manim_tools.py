# -*- coding: utf-8 -*-
"""R8 MCP 5 工具测试（§3.111 ⭐：render_manim/plan_scenes/audit_visual/tts_narrate/mux_video_assets）。"""
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import pytest

pytest.importorskip("fastmcp")


@pytest.fixture(scope="module")
def mcp():
    from paeg_teaching_materials.mcp_server import build_server
    return build_server()


class TestR8Tools:
    def test_5_tools_registered(self, mcp):
        import asyncio
        tools = asyncio.run(mcp.list_tools())
        names = {t.name for t in tools}
        assert "render_manim" in names
        assert "plan_scenes" in names
        assert "audit_visual" in names
        assert "tts_narrate" in names
        assert "mux_video_assets" in names

    def test_audit_visual(self, mcp):
        """audit_visual：MVQS + lint（无渲染）。"""
        import asyncio
        code = "class Demo(Scene):\n    def construct(self):\n        c = Circle().move_to(LEFT)\n        s = Square().next_to(c, RIGHT)\n        self.play(Create(c), Create(s))"
        r = asyncio.run(mcp.call_tool("audit_visual", {"code": code}))
        assert r.is_error is False
        txt = r.content[0].text
        assert "mvqs" in txt
        assert "lint_issues" in txt

    def test_audit_visual_by_topic(self, mcp):
        """audit_visual：topic 触发生成后审计。"""
        import asyncio
        from paeg_teaching_materials import MaterialRegistry

        def mock_llm(system, user, max_tokens=2000, temperature=0.7):
            return "class Demo(Scene):\n    def construct(self):\n        c = Circle().move_to(LEFT)\n        self.play(Create(c))"

        MaterialRegistry.inject(llm=mock_llm)
        r = asyncio.run(mcp.call_tool("audit_visual", {"topic": "导数"}))
        assert r.is_error is False
        assert "mvqs" in r.content[0].text

    def test_plan_scenes(self, mcp):
        """plan_scenes：分镜规划（含叙事质量）。"""
        import asyncio
        from paeg_teaching_materials import MaterialRegistry

        def mock_llm(system, user, max_tokens=2000, temperature=0.7):
            return "class Demo(Scene):\n    def construct(self):\n        self.play(FadeIn(Circle()))"

        MaterialRegistry.inject(llm=mock_llm)
        r = asyncio.run(mcp.call_tool("plan_scenes", {"topic": "基变换"}))
        assert r.is_error is False
        assert "script_plan" in r.content[0].text

    def test_tts_narrate_no_edge(self, mcp):
        """tts_narrate：无 edge-tts 环境返回错误（不崩溃）。"""
        import asyncio
        r = asyncio.run(mcp.call_tool("tts_narrate", {"text": "测试旁白"}))
        # ok:false 或 ok:true（取决于环境是否有 edge-tts）——不崩溃即可
        assert r.is_error is False

    def test_mux_no_video(self, mcp):
        """mux_video_assets：无视频返回 ok:false（不崩溃）。"""
        import asyncio
        r = asyncio.run(mcp.call_tool("mux_video_assets",
                                      {"video_path": "/nonexistent/v.mp4"}))
        assert r.is_error is False
