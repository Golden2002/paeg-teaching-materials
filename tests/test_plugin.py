# -*- coding: utf-8 -*-
"""paeg-teaching-materials 插件测试（P1 骨架 + 弱模式 + 注入 + MCP）。"""
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

# 语言规范插件路径（apply_language_l0 复用 paeg_lang_style 时用）
# paeg_project/paeg-lang-style-plugin/src（与 paeg-teaching-materials 平级）
_PLUGIN_ROOT = os.path.dirname(os.path.dirname(_SRC))  # paeg_project/
_LANG_SRC = os.path.join(_PLUGIN_ROOT, "paeg-lang-style-plugin", "src")
if os.path.isdir(_LANG_SRC) and _LANG_SRC not in sys.path:
    sys.path.insert(0, _LANG_SRC)

import pytest

import paeg_teaching_materials as ptm
from paeg_teaching_materials import (
    MaterialRegistry, execute, MATERIAL_TYPES,
    check_material_structure, judge_material,
)


# ─────────────────────────────────────
# 1. 公共 API / 基础
# ─────────────────────────────────────
class TestPublicAPI:
    def test_version(self):
        assert ptm.__version__ == "0.1.0"

    def test_material_types(self):
        assert "ppt" in MATERIAL_TYPES
        assert "handout" in MATERIAL_TYPES
        assert "script" in MATERIAL_TYPES
        assert "mindmap" in MATERIAL_TYPES
        assert "video" in MATERIAL_TYPES
        assert "manim" in MATERIAL_TYPES

    def test_register_defaults(self):
        """6 默认生成器已注册。"""
        assert MaterialRegistry.has("handout")
        assert MaterialRegistry.has("ppt")


# ─────────────────────────────────────
# 2. 弱模式（无宿主也能跑通——零宿主依赖）
# ─────────────────────────────────────
class TestWeakMode:
    def setup_method(self):
        MaterialRegistry.reset()

    def test_handout_weak(self):
        r = MaterialRegistry.generate("handout", "一元二次方程", "数学")
        assert r["material_type"] == "handout"
        assert r["ok"] is False  # 弱模式标记
        assert "待生成" in r["output"] or "弱模式" in r["output"]

    def test_ppt_weak(self):
        r = MaterialRegistry.generate("ppt", "光合作用", "生物")
        assert "待生成" in r["output"]

    def test_unknown_type_fallback(self):
        r = MaterialRegistry.generate("unknown_type", "x")
        assert r["ok"] is False


# ─────────────────────────────────────
# 3. 宿主注入（可及性 ⭐ 外部项目接入点）
# ─────────────────────────────────────
class TestInjection:
    def setup_method(self):
        MaterialRegistry.reset()

    def test_inject_llm(self):
        """注入 LLM 后强实现生效。"""
        def my_llm(system, user, max_tokens=2000, temperature=0.7):
            return "## 教学目标\n掌握概念\n## 课堂导入\n看一个例子\n## 新课讲授\n（内容）\n## 巩固练习\n（练习）\n## 课堂小结\n（小结）\n## 课后作业\n（作业）"

        MaterialRegistry.inject(llm=my_llm)
        r = MaterialRegistry.generate("handout", "导数", "数学")
        assert r["ok"] is True
        assert "教学目标" in r["output"]

    def test_inject_refiner(self):
        class MyRefiner:
            def detect_ai_tells(self, text):
                return ["总的来说"] if "总的来说" in text else []
            def refine(self, text, context=""):
                return text.replace("总的来说", "")

        MaterialRegistry.inject(refiner=MyRefiner())
        assert MaterialRegistry.refiner.detect_ai_tells("总的来说") == ["总的来说"]

    def test_reset(self):
        MaterialRegistry.inject(llm=lambda s, u, **k: "x")
        MaterialRegistry.reset()
        assert type(MaterialRegistry.llm).__name__ == "NullLLM"


# ─────────────────────────────────────
# 4. 统一执行入口 execute(name, args)
# ─────────────────────────────────────
class TestExecute:
    def setup_method(self):
        MaterialRegistry.reset()

    def test_execute_handout(self):
        result = execute("generate_handout", {"topic": "力学", "subject": "物理"})
        assert '"ok"' in result  # JSON 字符串
        assert "力学" in result

    def test_execute_missing_topic(self):
        result = execute("generate_ppt", {})
        assert '"ok": false' in result or '"ok": False' in result

    def test_execute_unknown(self):
        result = execute("unknown_tool", {})
        assert "未知物料工具" in result

    def test_execute_list_types(self):
        import json
        result = json.loads(execute("list_material_types", {}))
        assert result["ok"] is True
        assert "handout" in result["material_types"]

    def test_execute_never_raises(self):
        """任何异常都返回字符串错误（MCP 契约）。"""
        result = execute("generate_manim", {"topic": "x", "render": True})
        assert isinstance(result, str)


# ─────────────────────────────────────
# 5. 质量检查与评审
# ─────────────────────────────────────
class TestQuality:
    def test_check_structure_placeholder(self):
        issues = check_material_structure("这是内容（待生成）", "handout")
        assert any("占位" in i for i in issues)

    def test_check_structure_handout_sections(self):
        good = "## 教学目标\n## 课堂导入\n## 新课讲授\n## 巩固练习\n## 课堂小结\n## 课后作业\n" + "内容" * 200
        issues = check_material_structure(good, "handout")
        assert issues == [] or all("占位" not in i for i in issues)

    def test_judge_weak(self):
        r = judge_material("（待生成占位）", "主题")
        assert r["total"] <= 3.0  # 占位 → 低分

    def test_judge_complete(self):
        r = judge_material("这是一段完整的教学物料内容。" * 100, "主题")
        assert r["total"] >= 5.0

    def test_language_l0(self):
        """语言规范 L0 兜底（复用 paeg_lang_style）。"""
        from paeg_teaching_materials.quality.checks import apply_language_l0
        out = apply_language_l0("我在这里听着你。")
        assert "听你说说" in out  # 病句修正


# ─────────────────────────────────────
# 6. MCP server
# ─────────────────────────────────────
class TestMcpServer:
    pytest.importorskip("fastmcp")

    def test_build_server(self):
        from paeg_teaching_materials.mcp_server import build_server
        mcp = build_server()
        assert mcp is not None

    def test_tools_registered(self):
        import asyncio
        from paeg_teaching_materials.mcp_server import build_server
        mcp = build_server()
        tools = asyncio.run(mcp.list_tools())
        names = {t.name for t in tools}
        assert "generate_handout" in names
        assert "generate_ppt" in names
        assert "generate_script" in names
        assert "generate_mindmap" in names
        assert "generate_video_script" in names
        assert "generate_manim" in names
        assert "material_quality_check" in names
        assert "material_judge" in names
        assert "list_material_types" in names
        assert len(names) >= 9

    def test_call_generate_handout(self):
        import asyncio
        from paeg_teaching_materials.mcp_server import build_server
        mcp = build_server()
        r = asyncio.run(mcp.call_tool("generate_handout", {"topic": "力学", "subject": "物理"}))
        assert r.is_error is False
        assert "力学" in r.content[0].text
