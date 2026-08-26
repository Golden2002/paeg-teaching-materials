# -*- coding: utf-8 -*-
"""paeg_teaching_materials.manim_quality — Manim 顶尖化（§3.111 ⭐ 同步主项目改造）。

主项目 manim_pipeline 的顶尖化改造（RITL 渲染错误回灌 + safe_manim 12 崩溃模式）
同步到独立插件，供 ManimTool / ManimGenerator 消费——保证独立工具同样获得顶尖质量。

包含：
1. lint_manim_code（12 崩溃模式静态检测）
2. build_safety_feedback（RITL 反馈注入）
3. extract_error_tail / classify_error（错误签名分类）
4. build_ritl_prompt（渲染失败回灌提示）
"""

from __future__ import annotations

import ast
from typing import List, Tuple


# ─────────────────────────────────────
# 1. safe_manim 12 崩溃模式 lint（3brown1blue 证据）
# ─────────────────────────────────────
def _find_create_text(tree: ast.AST) -> List[Tuple[int, str]]:
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id == "Create" and node.args:
            arg = node.args[0]
            if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name) \
                    and arg.func.id in ("Text", "MathTex", "Tex"):
                hits.append((node.lineno, "C1: Create(Text) 描边而非书写 → 应改 Write(Text())"))
    return hits


def _find_brace_get_text(tree: ast.AST) -> List[Tuple[int, str]]:
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr == "get_text":
            for kw in node.keywords:
                if kw.arg == "font_size":
                    hits.append((node.lineno, "C3: Brace.get_text(font_size=) 崩溃 → 用 safe_brace_label"))
    return hits


def _find_math_tex_dollar(tree: ast.AST) -> List[Tuple[int, str]]:
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id == "MathTex":
            for a in node.args:
                if isinstance(a, ast.Constant) and isinstance(a.value, str) \
                        and "$" in a.value:
                    hits.append((node.lineno, "C4: MathTex 含 $ → 去掉（双 dollar 模式冲突）"))
    return hits


def _find_lagged_start_map_write(tree: ast.AST) -> List[Tuple[int, str]]:
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id == "LaggedStartMap" and node.args:
            arg0 = node.args[0]
            if isinstance(arg0, ast.Name) and arg0.id == "Write":
                hits.append((node.lineno, "C5: LaggedStartMap(Write, group) 崩溃 → 用 safe_lagged_write"))
    return hits


def _find_transform_after(tree: ast.AST) -> List[Tuple[int, str]]:
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id == "Transform":
            hits.append((node.lineno, "C7: Transform(A,B) 后 B 无效果 → 用 ReplacementTransform"))
    return hits


def _find_animate_vgroup(tree: ast.AST) -> List[Tuple[int, str]]:
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr == "animate":
            hits.append((node.lineno, "C8: .animate 只能用于 self.play() 内"))
    return hits


def _find_interpolate_color_str(tree: ast.AST) -> List[Tuple[int, str]]:
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id == "interpolate_color":
            for a in node.args:
                if isinstance(a, ast.Constant) and isinstance(a.value, str):
                    hits.append((node.lineno, "C10: interpolate_color 传 hex 字符串 → 用 ManimColor()"))
    return hits


def _find_get_part(tree: ast.AST) -> List[Tuple[int, str]]:
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr == "get_part_by_tex":
            hits.append((node.lineno, "C11: get_part_by_tex 可能返回 None → 用 safe_get_part"))
    return hits


_LINT_RULES = [
    ("C1", "Create(Text) 误用", _find_create_text),
    ("C3", "Brace.get_text 崩溃", _find_brace_get_text),
    ("C4", "MathTex 双 dollar", _find_math_tex_dollar),
    ("C5", "LaggedStartMap(Write)", _find_lagged_start_map_write),
    ("C7", "Transform 后操作", _find_transform_after),
    ("C8", ".animate 误用", _find_animate_vgroup),
    ("C10", "interpolate_color 字符串", _find_interpolate_color_str),
    ("C11", "get_part_by_tex None", _find_get_part),
]


def lint_manim_code(code: str) -> List[str]:
    """静态 lint：检测 Manim 崩溃/静默 bug 模式。返回违规列表（空=通过）。"""
    if not code:
        return ["代码为空"]
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [f"SyntaxError: {e}"]
    issues = []
    for _id, _desc, _fn in _LINT_RULES:
        try:
            for lineno, msg in _fn(tree):
                issues.append(f"L{lineno} [{_id}] {msg}")
        except Exception:
            continue
    return issues


def build_safety_feedback(code: str) -> str:
    """lint 违规转 RITL 修复反馈。"""
    issues = lint_manim_code(code)
    if not issues:
        return ""
    return "Manim 代码安全 lint 发现以下问题（请修复）：\n" + "\n".join(f"- {i}" for i in issues[:8])


# ─────────────────────────────────────
# 2. RITL（渲染错误回灌）
# ─────────────────────────────────────
def extract_error_tail(error: str, n: int = 10) -> str:
    """只取错误最后 N 行 traceback（ManimTrainer 论文 N=10 最优）。"""
    if not error:
        return "NONE"
    lines = str(error).splitlines()
    return "\n".join(lines[-n:]) if len(lines) > n else str(error)


def classify_error(error: str) -> str:
    """错误签名分类：code_api / latex / resource / generic。"""
    e = str(error).lower()
    if any(k in e for k in ("syntaxerror", "indentationerror", "nameerror",
                            "attributeerror", "typeerror", "importerror")):
        return "code_api"
    if any(k in e for k in ("latex", "tex", "dvi", "missing package")):
        return "latex"
    if any(k in e for k in ("timeout", "out of memory", "killed", "segmentation")):
        return "resource"
    return "generic"


def build_ritl_prompt(stage: str, artifact: str, error: str, code: str = "") -> str:
    """RITL 修复提示：错误 tail + safety lint + 上轮产物。"""
    tail = extract_error_tail(error)
    cls = classify_error(error)
    parts = [f"你是 {stage} 修复器。上一次 {stage} 失败（类型: {cls}）：\n{tail}"]
    if code:
        sf = build_safety_feedback(code)
        if sf:
            parts.append(sf)
    if cls == "latex":
        parts.append("提示：LaTeX 不可用——请用 Text() 替代 MathTex()/Tex()（或纯几何动画）。")
    parts.append("请修复后重新输出完整产物（结构不变）。")
    parts.append(f"上次产物：{str(artifact)[:1500]}")
    return "\n".join(parts)


# 兼容主项目命名（同步改造）
_extract_error_tail = extract_error_tail
_classify_error = classify_error
_build_ritl_prompt = build_ritl_prompt
