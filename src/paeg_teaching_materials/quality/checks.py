# -*- coding: utf-8 -*-
"""paeg_teaching_materials.quality.checks — 物料确定性检查（零依赖 ⭐）。

从 PAEG services/material_quality.py 平移：结构完整性 + 占位残留检测。
另含 apply_language_l0（语言规范 L0 规则兜底——复用 paeg_lang_style 若可用）。
"""

from __future__ import annotations

import re
from typing import List


def check_material_structure(text: str, material_type: str = "handout") -> List[str]:
    """确定性结构检查（无 LLM）。返回问题列表（空 = 通过）。

    - handout: 6 段结构（教学目标/课堂导入/新课讲授/巩固练习/课堂小结/课后作业）
    - script: 开场/主体/小结
    - mindmap: 层级缩进
    - 通用: 占位残留检测
    """
    if not text or not text.strip():
        return ["内容为空"]
    issues: List[str] = []

    # 占位残留检测（通用）
    placeholders = re.findall(r"(待生成|占位|TODO|待补充|（待|\(待)", text)
    if placeholders:
        issues.append(f"存在 {len(placeholders)} 处占位残留（待生成/TODO/待补充）")

    # 结构检查
    if material_type == "handout":
        required = ["教学目标", "课堂导入", "新课讲授", "巩固练习", "课堂小结", "课后作业"]
        missing = [s for s in required if s not in text]
        if missing:
            issues.append(f"讲义缺 {len(missing)} 段结构: {', '.join(missing)}")
        if len(text) < 300:
            issues.append("讲义内容过短（<300 字）")

    elif material_type == "script":
        for kw in ("开场", "小结", "结束"):
            if kw not in text:
                issues.append(f"讲稿缺『{kw}』部分")
        if len(text) < 200:
            issues.append("讲稿内容过短（<200 字）")

    elif material_type == "mindmap":
        if not re.search(r"\n\s{2,}[-*]", text):
            issues.append("思维导图缺层级缩进结构（应有二级分支）")

    return issues


def apply_language_l0(text: str) -> str:
    """语言规范 L0 规则兜底（病句修正——复用 paeg_lang_style 若已安装）。"""
    if not text:
        return text
    try:
        from paeg_lang_style import fix_known_gaffes
        return fix_known_gaffes(text)
    except Exception:
        return text
