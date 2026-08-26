# -*- coding: utf-8 -*-
"""paeg_teaching_materials.generators.handout — 讲义生成器（强+弱双轨）。

强实现：注入 LLM 后按 6 段教学结构（教学目标/导入/新课/巩固/小结/作业）生成。
弱实现：无 LLM 时返回结构化占位（弱模式）。
"""

from __future__ import annotations

import json
from typing import Any, Dict

from ..registry import MaterialRegistry
from .base import Generator

# 讲义 6 段结构
HANDOUT_SECTIONS = ["教学目标", "课堂导入", "新课讲授", "巩固练习", "课堂小结", "课后作业"]

# 讲义生成提示词（弱实现用规则，强实现注入 LLM）
_HANDOUT_SYSTEM = """你是一位资深教师，为指定主题编写讲义。要求：
1. 按 6 段结构组织：教学目标 / 课堂导入 / 新课讲授 / 巩固练习 / 课堂小结 / 课后作业
2. 语言规范（词法完整/句法完整/充分状语——用完整词形、句子成分齐全、动作带状语）
3. 朴素、有力量、循循善诱（薇依式语言：不煽情、不空洞、具体）
4. 目标学员：{learner}；学科：{subject}
5. 输出 markdown，用 ## 标题分节"""


class HandoutGenerator(Generator):
    """讲义生成器（注入 LLM 则强实现；否则弱实现）。"""

    material_type = "handout"

    def generate(self, topic: str, subject: str = "通用",
                 learner_id: str = "anon", **kw) -> Dict[str, Any]:
        llm = MaterialRegistry.llm
        try:
            user = f"请为『{topic}』编写讲义（{subject}）。"
            system = _HANDOUT_SYSTEM.format(learner=kw.get("learner", "学生"), subject=subject)
            if hasattr(llm, "__call__") and type(llm).__name__ != "NullLLM":
                output = llm(system, user, max_tokens=2000)
                return {
                    "material_type": "handout", "topic": topic, "subject": subject,
                    "ok": True, "output": output,
                }
            # 弱实现：结构化占位
            output = "\n".join(f"## {sec}\n\n（{sec}内容待生成——未注入 LLM 实现）"
                               for sec in HANDOUT_SECTIONS)
            return {
                "material_type": "handout", "topic": topic, "subject": subject,
                "ok": False, "output": f"# {topic} 讲义（弱模式占位）\n\n{output}",
            }
        except Exception as e:
            return {"material_type": "handout", "topic": topic, "subject": subject,
                    "ok": False, "error": f"讲义生成失败: {str(e)[:200]}"}
