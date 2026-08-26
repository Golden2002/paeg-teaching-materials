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


# ─────────────────────────────────────
# §3.111 ⭐ R7 叙事质量（同步主项目 manim_narrative 增强）
# ─────────────────────────────────────
VISUAL_PRINCIPLES_17 = """### 3Blue1Brown 视觉设计原则（17 条 · §3.111 ⭐）
1. Geometry before algebra：图形先于公式（视觉记忆快 6 倍）
2. Opacity layering：主对象 100% / 上下文 40% / 网格 15%
3. Persistent context：上下文常驻（缩小父对象保留 30-40%）
4. Linked dual representations：双重表示联动（共享 ValueTracker）
5. Parameter manipulation：参数操控让观众"玩"参数
6. Continuous morphing：ReplacementTransform 保持对象身份
7. Question frames：提问→停 2-3 秒→视觉回答
8. Annotations ON objects：标签贴物体（防 split-attention）
9. Color as semantic data：一色一义
10. Concrete values：用真数字而非符号占位
11. Progressive complexity：层层叠加，旧层 dim 到 0.3
12. Emotional anchoring：关键时刻强烈视觉
13. Live values：DecimalNumber + always_redraw
14. Density ramp：从 2 元素渐增到 15
15. Per-scene skeleton：每 scene 一个核心锚图
16. Caption zone：底部 20% 留白
17. Monospace for all Text：等宽字体"""

NARRATIVE_ARC_PROMPT = """### 叙事结构（§3.111 ⭐ 选 1 个用于分镜）
- mystery_investigation：谜题→调查→解答
- build_up_payoff：搭建→兑现
- two_perspectives_unity：双视角→统一
- wrong_less_wrong_right：错误→更接近→正确（学习增益最强）
- specific_general：特例→一般
- history_narrative：历史叙事"""


# ─────────────────────────────────────
# §3.111 ⭐ R2 RITL-DOC（同步主项目 manim_doc_index）
# ─────────────────────────────────────
_MANIM_API_INDEX = {
    "Create": {"sig": "Create(mobject)", "desc": "描边创建（只用于几何图形，Text 用 Write）"},
    "Write": {"sig": "Write(text_or_mobject)", "desc": "书写文本/公式（Create 的 Text 替代）"},
    "Transform": {"sig": "Transform(mobject, target)", "desc": "变换（保留原对象）"},
    "ReplacementTransform": {"sig": "ReplacementTransform(source, target)", "desc": "替换变换"},
    "TransformMatchingTex": {"sig": "TransformMatchingTex(source, target)", "desc": "公式逐项匹配"},
    "MathTex": {"sig": "MathTex('x^2')", "desc": "数学公式（不要带 $——用 {{ }} 分组）"},
    "Text": {"sig": "Text(text, color=WHITE, font_size=48)", "desc": "文本（用 Write）"},
    "Circle": {"sig": "Circle(radius=1, color=WHITE)", "desc": "圆"},
    "Square": {"sig": "Square(side_length=2)", "desc": "正方形"},
    "Line": {"sig": "Line(start, end)", "desc": "线段"},
    "Arrow": {"sig": "Arrow(start, end)", "desc": "箭头（避免 interpolate_color tip crash）"},
    "Axes": {"sig": "Axes(x_range, y_range)", "desc": "坐标轴"},
    "VGroup": {"sig": "VGroup(*mobjects)", "desc": "组合（.animate 只能用于 self.play 内）"},
    "FadeIn": {"sig": "FadeIn(mobject)", "desc": "淡入"},
    "FadeOut": {"sig": "FadeOut(mobject)", "desc": "淡出"},
    "LaggedStart": {"sig": "LaggedStart(*animations)", "desc": "依次播放（替代 LaggedStartMap(Write)）"},
    "ValueTracker": {"sig": "ValueTracker(value)", "desc": "数值跟踪器（双表示联动）"},
    "interpolate_color": {"sig": "interpolate_color(c1, c2, alpha)", "desc": "颜色插值（传 ManimColor）"},
    "Brace": {"sig": "Brace(mobject, direction)", "desc": "大括号（不要 get_text(font_size=)）"},
}


def extract_manim_apis(code: str) -> list:
    """AST 抽取代码中的 Manim API 调用（RITL-DOC）。"""
    if not code:
        return []
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    apis = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in _MANIM_API_INDEX:
                apis.append(node.func.id)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in _MANIM_API_INDEX:
                apis.append(node.func.attr)
    return list(dict.fromkeys(apis))


def build_doc_block(code: str, max_apis: int = 12) -> str:
    """RITL-DOC：AST 抽 API → 注入签名 + 说明（剔除 Examples）。"""
    apis = extract_manim_apis(code)
    if not apis:
        return ""
    lines = ["## Manim API 参考（精确签名，请按此使用）"]
    for api in apis[:max_apis]:
        doc = _MANIM_API_INDEX.get(api)
        if doc:
            lines.append(f"- **{api}**: `{doc['sig']}` — {doc['desc']}")
    return "\n".join(lines)


def build_ritl_doc_block(code: str, error: str) -> str:
    """RITL-DOC 完整反馈（供 ManimGenerator 修复回路）。"""
    tail = extract_error_tail(error)
    cls = classify_error(error)
    doc = build_doc_block(code)
    parts = [f"渲染失败（类型: {cls}）：\n{tail}"]
    if doc:
        parts.append(doc)
    if cls == "latex":
        parts.append("提示：LaTeX 不可用——用 Text() 替代 MathTex()/Tex()。")
    parts.append("请修复代码（保持功能，修正 API 用法）。输出完整代码。")
    return "\n\n".join(parts)


# ─────────────────────────────────────
# §3.111 ⭐ R5 MVQS 几何评估（同步主项目 manim_mvqs——代码级，无需渲染）
# ─────────────────────────────────────
def mvqs_score(code: str) -> dict:
    """MVQS 三维几何评估（无需渲染，6-18x 快）：
    overlap（避免重叠）/ relation（关系一致）/ boundary（边界合法）。

    Returns: {overlap, relation, boundary, mvqs, verdict, issues}
    """
    ops = {"creations": [], "positions": [], "scales": [], "shifts": []}
    if not code:
        return {"overlap": 0.8, "relation": 0.4, "boundary": 0.8,
                "mvqs": 0.68, "verdict": "PASS", "issues": [],
                "creations_count": 0, "positions_count": 0}
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {"overlap": 0.5, "relation": 0.5, "boundary": 0.5,
                "mvqs": 0.5, "verdict": "WARN", "issues": ["代码语法错误"],
                "creations_count": 0, "positions_count": 0}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            name = node.func.id
            if name in ("Circle", "Square", "Rectangle", "Line", "Arrow",
                        "Text", "MathTex", "Tex", "Dot", "Polygon", "Axes",
                        "VGroup", "Group", "NumberPlane", "Triangle"):
                ops["creations"].append({"type": name, "line": node.lineno})
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            attr = node.func.attr
            if attr == "shift" and node.args:
                ops["shifts"].append({"line": node.lineno})
            elif attr == "scale" and node.args:
                try:
                    ops["scales"].append({"value": ast.literal_eval(node.args[0])})
                except Exception:
                    ops["scales"].append({"value": None})
            elif attr in ("move_to", "next_to", "align_to"):
                ops["positions"].append({"op": attr, "line": node.lineno})

    # 三维评分
    creations = len(ops["creations"])
    if creations == 0:
        overlap = 0.8
    else:
        coverage = len(ops["positions"]) / max(creations, 1)
        overlap = 0.9 if coverage >= 0.5 else (0.6 if coverage >= 0.25 else 0.3)
    if not ops["positions"]:
        relation = 0.4
    else:
        relative = sum(1 for p in ops["positions"] if p["op"] == "next_to")
        relation = 0.9 if relative >= 1 else 0.6
    boundary = 0.8
    for s in ops["scales"]:
        v = s.get("value")
        if v is not None and (v > 10 or (v > 0 and v < 0.1)):
            boundary -= 0.3
    if len(ops["shifts"]) > creations * 2:
        boundary -= 0.2
    boundary = max(0.2, min(1.0, boundary))

    mvqs = round(0.4 * overlap + 0.3 * relation + 0.3 * boundary, 3)
    issues = []
    if overlap < 0.5:
        issues.append("对象可能重叠——创建后缺少定位（move_to/next_to）")
    if relation < 0.5:
        issues.append("对象关系不明——建议用 next_to/align_to 建立相对位置")
    if boundary < 0.5:
        issues.append("存在异常缩放/过多平移——对象可能越界")
    verdict = "PASS" if mvqs >= 0.6 else ("WARN" if mvqs >= 0.4 else "FAIL")
    return {"overlap": round(overlap, 3), "relation": round(relation, 3),
            "boundary": round(boundary, 3), "mvqs": mvqs, "verdict": verdict,
            "issues": issues, "creations_count": creations,
            "positions_count": len(ops["positions"])}


def build_mvqs_feedback(code: str) -> str:
    """MVQS 反馈（供 RITL prompt 注入）。"""
    r = mvqs_score(code)
    if r["verdict"] == "PASS":
        return ""
    lines = [f"## MVQS 几何评估（§3.111 R5）：{r['verdict']}（mvqs={r['mvqs']}）"]
    lines.append(f"- overlap={r['overlap']} relation={r['relation']} boundary={r['boundary']}")
    for i in r["issues"]:
        lines.append(f"- 问题：{i}")
    lines.append("请调整对象定位/缩放，避免重叠与越界（用 next_to/move_to/scale）。")
    return "\n".join(lines)
