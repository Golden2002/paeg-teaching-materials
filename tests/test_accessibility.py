# -*- coding: utf-8 -*-
"""§3.114 可及性测试：pip 安装 + 自动注册（像 Python 库一样）。"""
import os
import subprocess
import sys

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import pytest

import paeg_teaching_materials as ptm


# ─────────────────────────────────────
# 1. 包结构（pip 可安装的前提）
# ─────────────────────────────────────
class TestPackageStructure:
    def test_src_layout_pyproject(self):
        """pyproject 配置 src 布局（§3.114 修复）。"""
        import tomllib
        p = os.path.join(os.path.dirname(_SRC), "pyproject.toml")
        with open(p, "rb") as f:
            data = tomllib.load(f)
        sd = data.get("tool", {}).get("setuptools", {})
        assert sd.get("package-dir", {}).get("") == "src", "必须配置 src 布局"
        find = sd.get("packages", {}).get("find", {})
        assert find.get("where") == ["src"], "必须自动发现 src 下包"

    def test_subpackages_discoverable(self):
        """子包（core/generators/quality 等）应被自动发现。"""
        import tomllib
        p = os.path.join(os.path.dirname(_SRC), "pyproject.toml")
        with open(p, "rb") as f:
            data = tomllib.load(f)
        inc = data.get("tool", {}).get("setuptools", {}).get("packages", {}).get("find", {}).get("include", [])
        assert any("paeg_teaching_materials*" in i for i in inc), "必须包含通配子包"

    def test_import_auto_registers(self):
        """import 即自动注册（register_defaults 在 __init__ 触发）。"""
        from paeg_teaching_materials import MaterialRegistry
        types = MaterialRegistry.available_types()
        assert "handout" in types
        assert "ppt" in types
        assert "manim" in types


# ─────────────────────────────────────
# 2. 自动注册（他人场景）
# ─────────────────────────────────────
class TestAutoRegister:
    def test_execute_weak_mode(self):
        """import 后 execute 立即可用（弱模式，无 LLM）。"""
        import json
        from paeg_teaching_materials import execute
        r = json.loads(execute("generate_handout", {"topic": "力学", "subject": "物理"}))
        assert "material_type" in r
        assert r["material_type"] == "handout"

    def test_inject_llm_then_use(self):
        """注入自己的 LLM → 强实现生效（外部智能体场景）。"""
        import json
        from paeg_teaching_materials import MaterialRegistry, execute

        def my_llm(system, user, max_tokens=2000, temperature=0.7):
            return "## 教学目标\n掌握概念\n## 课堂导入\n## 新课讲授\n## 巩固练习\n## 课堂小结\n## 课后作业"

        MaterialRegistry.inject(llm=my_llm)
        r = json.loads(execute("generate_handout", {"topic": "导数", "subject": "数学"}))
        assert r.get("ok") is True
        assert "教学目标" in r.get("output", "")

    def test_mcp_scripts_declared(self):
        """pyproject 声明 MCP console_scripts（装后可执行）。"""
        import tomllib
        p = os.path.join(os.path.dirname(_SRC), "pyproject.toml")
        with open(p, "rb") as f:
            data = tomllib.load(f)
        scripts = data.get("project", {}).get("scripts", {})
        assert "paeg-teaching-materials-mcp" in scripts
