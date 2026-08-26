# -*- coding: utf-8 -*-
"""manim_quality 测试（§3.111 ⭐ 独立插件同步 Manim 顶尖化改造）。"""
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import pytest

from paeg_teaching_materials.manim_quality import (
    lint_manim_code, build_safety_feedback,
    extract_error_tail, classify_error, build_ritl_prompt,
)


# ─────────────────────────────────────
# 1. safety lint（12 崩溃模式）
# ─────────────────────────────────────
class TestLint:
    def test_create_text(self):
        code = "class S(Scene):\n    def construct(self):\n        self.play(Create(Text('hi')))"
        assert any("C1" in i for i in lint_manim_code(code))

    def test_brace_get_text(self):
        code = "class S(Scene):\n    def construct(self):\n        b.get_text('x', font_size=24)"
        assert any("C3" in i for i in lint_manim_code(code))

    def test_math_tex_dollar(self):
        code = "class S(Scene):\n    def construct(self):\n        eq = MathTex(r'$E=mc^2$')"
        assert any("C4" in i for i in lint_manim_code(code))

    def test_lagged_start_map(self):
        code = "class S(Scene):\n    def construct(self):\n        self.play(LaggedStartMap(Write, g))"
        assert any("C5" in i for i in lint_manim_code(code))

    def test_clean_code(self):
        code = "class S(Scene):\n    def construct(self):\n        self.play(FadeIn(Circle()))\n        self.wait(1)"
        assert lint_manim_code(code) == []

    def test_syntax_error(self):
        assert any("SyntaxError" in i for i in lint_manim_code("class {"))


# ─────────────────────────────────────
# 2. RITL（错误回灌）
# ─────────────────────────────────────
class TestRitl:
    def test_error_tail(self):
        e = "\n".join(f"line {i}" for i in range(30))
        assert extract_error_tail(e) == "\n".join(f"line {i}" for i in range(20, 30))

    def test_classify(self):
        assert classify_error("SyntaxError: x") == "code_api"
        assert classify_error("latex failed") == "latex"
        assert classify_error("timeout") == "resource"
        assert classify_error("unknown") == "generic"

    def test_ritl_prompt_has_error(self):
        p = build_ritl_prompt("Manim 代码", {"code": "x"}, "NameError: y")
        assert "NameError" in p
        assert "Manim 代码 修复器" in p

    def test_ritl_prompt_has_safety(self):
        bad = "class S(Scene):\n    def construct(self):\n        self.play(Create(Text('hi')))"
        p = build_ritl_prompt("Manim 代码", bad, "NameError", code=bad)
        assert "C1" in p

    def test_latex_hint(self):
        p = build_ritl_prompt("Manim 代码", "x", "latex error")
        assert "Text() 替代 MathTex" in p


# ─────────────────────────────────────
# 4. R5 MVQS（几何评估，同步主项目）
# ─────────────────────────────────────
class TestMvqs:
    def test_good_code_pass(self):
        from paeg_teaching_materials.manim_quality import mvqs_score
        good = '''
class Demo(Scene):
    def construct(self):
        c = Circle().move_to(LEFT)
        s = Square().next_to(c, RIGHT)
        self.play(Create(c), Create(s))
'''
        r = mvqs_score(good)
        assert r["verdict"] == "PASS"
        assert r["mvqs"] >= 0.6

    def test_bad_code_warn(self):
        from paeg_teaching_materials.manim_quality import mvqs_score
        bad = '''
class Demo(Scene):
    def construct(self):
        a = Circle()
        b = Square()
        c = Text("x")
        self.add(a, b, c)
'''
        r = mvqs_score(bad)
        assert r["verdict"] in ("WARN", "FAIL")
        assert len(r["issues"]) >= 1

    def test_build_mvqs_feedback(self):
        from paeg_teaching_materials.manim_quality import build_mvqs_feedback
        bad = '''
class Demo(Scene):
    def construct(self):
        a = Circle()
        b = Square()
        self.add(a, b)
'''
        fb = build_mvqs_feedback(bad)
        assert "MVQS 几何评估" in fb


# ─────────────────────────────────────
# 5. 与 ManimGenerator 集成（MVQS 报告）
# ─────────────────────────────────────
class TestManimGeneratorMvqs:
    def setup_method(self):
        from paeg_teaching_materials import MaterialRegistry
        MaterialRegistry.reset()

    def test_generate_includes_mvqs(self):
        from paeg_teaching_materials import MaterialRegistry
        from paeg_teaching_materials.generators import ManimGenerator

        def mock_llm(system, user, max_tokens=2000, temperature=0.7):
            return "class Demo(Scene):\n    def construct(self):\n        c = Circle().move_to(LEFT)\n        s = Square().next_to(c, RIGHT)\n        self.play(Create(c), Create(s))"

        MaterialRegistry.inject(llm=mock_llm)
        gen = ManimGenerator()
        r = gen.generate("导数", "数学")
        assert r.get("ok") is True
        assert "mvqs" in r
        assert r["mvqs"]["verdict"] == "PASS"
class TestManimGeneratorEnhanced:
    def setup_method(self):
        from paeg_teaching_materials import MaterialRegistry
        MaterialRegistry.reset()

    def test_generate_with_lint_report(self):
        """ManimGenerator 输出含 lint_issues 报告（§3.111）。"""
        from paeg_teaching_materials import MaterialRegistry
        from paeg_teaching_materials.generators import ManimGenerator

        def mock_llm(system, user, max_tokens=2000, temperature=0.7):
            return "class Demo(Scene):\n    def construct(self):\n        self.play(Create(Text('hi')))\n        self.play(FadeIn(Circle()))"

        MaterialRegistry.inject(llm=mock_llm)
        gen = ManimGenerator()
        r = gen.generate("导数", "数学")
        assert r["ok"] is True
        assert "lint_issues" in r
        assert any("C1" in i for i in r["lint_issues"])  # Create(Text) 被检测

    def test_generate_clean_no_lint(self):
        from paeg_teaching_materials import MaterialRegistry
        from paeg_teaching_materials.generators import ManimGenerator

        def mock_llm(system, user, max_tokens=2000, temperature=0.7):
            return "class Demo(Scene):\n    def construct(self):\n        self.play(FadeIn(Circle()))\n        self.wait(1)"

        MaterialRegistry.inject(llm=mock_llm)
        gen = ManimGenerator()
        r = gen.generate("圆", "数学")
        assert r["lint_issues"] == []
