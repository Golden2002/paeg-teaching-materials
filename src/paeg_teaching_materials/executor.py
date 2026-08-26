# -*- coding: utf-8 -*-
"""paeg_teaching_materials.executor — 统一执行入口（Oracle R4 ⭐ 对标 constraint_engine.execute）。

设计目标：MCP 工具统一入口。name ∈ {generate_ppt, generate_handout, ...}。
返回 JSON 字符串（MCP 契约），内部 try/except 隔离，失败返回 ok=False + error（绝不抛异常）。

用法：
    from paeg_teaching_materials import execute
    result = execute("generate_ppt", {"topic": "一元二次方程", "subject": "数学"})
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from .registry import MaterialRegistry

# 工具 → 物料类型映射
_TOOL_MATERIAL_MAP = {
    "generate_ppt": "ppt",
    "generate_handout": "handout",
    "generate_script": "script",
    "generate_video": "video",
    "generate_video_script": "video",
    "generate_mindmap": "mindmap",
    "generate_manim": "manim",
    "generate_animation": "manim",
}


def execute(name: str, arguments: Optional[Dict[str, Any]] = None) -> str:
    """MCP 工具统一入口（对标 constraint_engine.execute）。

    Args:
        name: 工具名（generate_ppt / generate_handout / ... / material_quality_check / material_judge / list_material_types）。
        arguments: 参数字典（topic/subject/learner_id 等）。

    Returns:
        JSON 字符串（ok/result/error）。任何异常 → ok=False + error（绝不抛异常）。
    """
    args = arguments or {}

    # ── 自省工具 ──
    if name == "list_material_types":
        return json.dumps({
            "ok": True,
            "material_types": MaterialRegistry.available_types(),
            "registered": sorted(MaterialRegistry._generators.keys()),
            "pipelines": sorted(MaterialRegistry._pipelines.keys()),
        }, ensure_ascii=False)

    # ── 物料生成工具 ──
    if name in _TOOL_MATERIAL_MAP:
        material_type = _TOOL_MATERIAL_MAP[name]
        topic = args.get("topic", "")
        subject = args.get("subject", "通用")
        learner_id = args.get("learner_id", "anon")
        if not topic:
            return json.dumps({"ok": False, "error": f"缺少 topic 参数（{name}）"},
                              ensure_ascii=False)
        try:
            # 移除已显式传递的键（避免 **args 重复传参）
            extra = {k: v for k, v in args.items()
                     if k not in ("topic", "subject", "learner_id")}
            result = MaterialRegistry.generate(
                material_type, topic, subject, learner_id, **extra)
            # 语言规范 L0（规则兜底）
            from .quality.checks import apply_language_l0
            if result.get("output"):
                result["output_l0"] = apply_language_l0(str(result["output"]))
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({"ok": False, "error": f"{name} 执行失败: {str(e)[:200]}"},
                              ensure_ascii=False)

    # ── 质量工具 ──
    if name == "material_quality_check":
        try:
            from .quality.checks import check_material_structure
            text = args.get("text", "")
            material_type = args.get("material_type", "handout")
            if not text:
                return json.dumps({"ok": False, "error": "缺少 text 参数"},
                                  ensure_ascii=False)
            issues = check_material_structure(text, material_type)
            return json.dumps({"ok": True, "material_type": material_type,
                               "issues": issues, "pass": len(issues) == 0},
                              ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": f"material_quality_check 失败: {str(e)[:200]}"},
                              ensure_ascii=False)

    if name == "material_judge":
        try:
            from .quality.judge import judge_material
            text = args.get("text", "")
            topic = args.get("topic", "")
            if not text:
                return json.dumps({"ok": False, "error": "缺少 text 参数"},
                                  ensure_ascii=False)
            score = judge_material(text, topic)
            return json.dumps({"ok": True, "score": score}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": f"material_judge 失败: {str(e)[:200]}"},
                              ensure_ascii=False)

    return json.dumps({"ok": False, "error": f"未知物料工具: {name}（支持 generate_*/material_quality_check/material_judge/list_material_types）"},
                      ensure_ascii=False)
