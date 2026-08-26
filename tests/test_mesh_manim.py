# -*- coding: utf-8 -*-
"""R9 网状联通 manim 节点消费增强测试（§3.111 ⭐）。"""
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import pytest

from paeg_teaching_materials import MaterialRegistry


@pytest.fixture(autouse=True)
def _llm():
    MaterialRegistry.reset()

    def mock_llm(system, user, max_tokens=2000, temperature=0.7):
        return "class Demo(Scene):\n    def construct(self):\n        c = Circle().move_to(LEFT)\n        s = Square().next_to(c, RIGHT)\n        self.play(Create(c), Create(s))\n        self.wait(1)"

    MaterialRegistry.inject(llm=mock_llm)
    yield


class TestManimNode:
    def test_manim_tool_registered(self):
        """manim 是网状节点（一等公民）。"""
        from paeg_teaching_materials.tools import register_mesh_tools
        register_mesh_tools()
        assert "manim" in MaterialRegistry.available_tools()

    def test_manim_dependencies(self):
        """manim 节点前置 = research（广播边）。"""
        from paeg_teaching_materials.tools import register_mesh_tools
        register_mesh_tools()
        tool = MaterialRegistry.get_tool("manim")
        srcs = [d.source for d in tool.requires]
        assert "research" in srcs

    def test_manim_generate_with_enhancements(self):
        """manim 生成含顶尖化增强（mvqs + lint）。"""
        from paeg_teaching_materials.generators import ManimGenerator
        gen = ManimGenerator()
        r = gen.generate("导数", "数学")
        assert r.get("ok") is True
        assert "mvqs" in r  # R5
        assert "lint_issues" in r  # R3
        assert r["mvqs"]["verdict"] == "PASS"

    def test_manim_execute_pipeline(self):
        """execute_pipeline("manim") 自动 research → manim。"""
        import json
        from paeg_teaching_materials import execute
        r = json.loads(execute("generate_manim", {"topic": "导数", "subject": "数学"}))
        assert r.get("ok") is True
        assert "mvqs" in r.get("mvqs", {}) or "output" in r
