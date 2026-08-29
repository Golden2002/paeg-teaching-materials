# -*- coding: utf-8 -*-
"""真实渲染落盘适配器测试（pptx / manim / tts）。

确定性、零网络：只测清洗逻辑、落盘、优雅降级，不依赖真实渲染环境。
"""
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import pytest

from paeg_teaching_materials.manim_quality import clean_manim_code
from paeg_teaching_materials.adapters.pptx_renderer import (
    render_outline_to_pptx, _parse_outline, clean_md,
)
from paeg_teaching_materials.adapters.tts_synth import to_speakable
from paeg_teaching_materials.adapters.manim_runtime import (
    manim_available, save_manim_code, render_manim_code,
)


# ─────────────────────────────────────
# 1. clean_manim_code（修复 LLM 代码块外壳/全角标点 bug）
# ─────────────────────────────────────
class TestCleanManimCode:
    def test_strips_code_fence(self):
        code = "```python\nfrom manim import *\nclass S(Scene):\n    def construct(self):\n        self.play(FadeIn(Circle()))\n```\n"
        out = clean_manim_code(code)
        assert "```" not in out
        assert out.startswith("from manim import *")

    def test_strips_preamble(self):
        code = "这是修复后的代码：\nfrom manim import *\nclass S(Scene):\n    pass\n"
        out = clean_manim_code(code)
        assert "这是修复后的代码" not in out
        assert out.startswith("from manim import *")

    def test_fullwidth_outside_strings(self):
        code = "class S(Scene):\n    def construct(self):\n        self.play(FadeIn(Circle()),\n                  run_time=2)"
        # 中文冒号/逗号在代码语法位置 → 转半角
        code_fw = code.replace("(Circle())", "（Circle()）").replace(":\n", "：\n")
        out = clean_manim_code(code_fw)
        assert "（" not in out and "：" not in out

    def test_preserves_string_content(self):
        # Text 字符串内的中文标点应保持不变（不被全角→半角破坏）
        code = 'class S(Scene):\n    def construct(self):\n        t = Text("你好，世界！")\n        self.play(Write(t))'
        out = clean_manim_code(code)
        assert "你好，世界！" in out

    def test_idempotent(self):
        code = "from manim import *\nclass S(Scene):\n    def construct(self):\n        self.play(FadeIn(Circle()))"
        assert clean_manim_code(code) == clean_manim_code(clean_manim_code(code))


# ─────────────────────────────────────
# 2. pptx_renderer（真实落盘，无网络）
# ─────────────────────────────────────
class TestPptxRenderer:
    def test_parse_outline_markdown(self):
        outline = "## 封面：一元二次方程\n- 定义\n## 解法\n- 因式分解\n- 公式法"
        slides = _parse_outline(outline)
        assert len(slides) == 2
        assert slides[0]["title"] == "封面：一元二次方程"
        assert slides[0]["points"] == ["定义"]

    def test_clean_md(self):
        assert clean_md("**加粗** `代码` [链接](http://x)") == "加粗 代码 链接"

    def test_render_outline_to_pptx(self, tmp_path):
        pytest.importorskip("pptx")
        outline = ("## 封面：测试主题\n- 要点一\n- 要点二\n"
                   "## 第二节\n- 内容 A\n- 内容 B")
        path = render_outline_to_pptx(outline, "测试主题", out_dir=str(tmp_path))
        assert os.path.isfile(path)
        assert path.endswith(".pptx")
        assert os.path.getsize(path) > 0
        # 可被 python-pptx 重新打开（结构合法）
        from pptx import Presentation
        prs = Presentation(path)
        assert len(prs.slides) >= 2


# ─────────────────────────────────────
# 3. tts_synth（markdown 清洗，无网络）
# ─────────────────────────────────────
class TestTtsSynth:
    def test_to_speakable_strips_markdown(self):
        md = "## 开场\n**细胞呼吸**是生命活动的基础。\n| 项目 | 有氧 |\n|---|---|\n| 场所 | 线粒体 |\n- 要点一"
        out = to_speakable(md)
        assert "##" not in out and "**" not in out and "|" not in out
        assert "细胞呼吸" in out

    def test_to_speakable_empty(self):
        assert to_speakable("") == ""


# ─────────────────────────────────────
# 4. manim_runtime（落盘 + 优雅降级，无网络）
# ─────────────────────────────────────
class TestManimRuntime:
    def test_manim_available_returns_bool(self):
        assert isinstance(manim_available(), bool)

    def test_save_manim_code_writes_py(self, tmp_path):
        code = "```python\nfrom manim import *\nclass S(Scene):\n    def construct(self):\n        self.play(FadeIn(Circle()))\n```"
        path = save_manim_code(code, "圆", out_dir=str(tmp_path))
        assert os.path.isfile(path)
        assert path.endswith(".py")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "```" not in content  # 已清洗代码块外壳
        assert "class S" in content

    def test_render_manim_code_degrades_gracefully(self, tmp_path):
        """manim 未安装时抛 RuntimeError（含 MANIM_UNAVAILABLE 提示），且已保存 .py。"""
        if manim_available():
            pytest.skip("本环境已安装 manim，跳过降级断言")
        code = "from manim import *\nclass S(Scene):\n    def construct(self):\n        self.play(FadeIn(Circle()))"
        with pytest.raises(RuntimeError) as exc:
            render_manim_code(code, "圆", out_dir=str(tmp_path))
        assert "MANIM_UNAVAILABLE" in str(exc.value) or "manim" in str(exc.value).lower()
        # 即使降级，.py 代码已落盘
        assert any(f.endswith(".py") for f in os.listdir(tmp_path))
