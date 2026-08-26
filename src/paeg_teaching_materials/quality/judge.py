# -*- coding: utf-8 -*-
"""paeg_teaching_materials.quality.judge — 物料评审（LLM-as-judge 5 维）。

从 PAEG services/material_judge.py 平移。注入 LLM 后 5 维评分：
factuality / correctness / completeness / relevance / pedagogy。
无 LLM 时返回确定性启发式评分（弱模式）。
"""

from __future__ import annotations

from typing import Any, Dict

from ..registry import MaterialRegistry

# 5 维评审标准
_JUDGE_SYSTEM = """你是教学物料评审专家。对生成的物料按 5 维打分（每维 0-10）：
1. factuality（事实准确性）：是否与学科事实一致
2. correctness（内容正确性）：概念/公式/推理是否正确
3. completeness（完整性）：是否覆盖主题关键点
4. relevance（相关性）：是否紧扣主题、无离题内容
5. pedagogy（教学法）：是否循循善诱、适合学生
输出 JSON: {"scores": {"factuality": n, ...}, "total": n, "comment": "..."}"""


def judge_material(text: str, topic: str = "", subject: str = "通用") -> Dict[str, Any]:
    """评审物料（LLM 注入则强评审；否则确定性启发式）。"""
    if not text:
        return {"total": 0, "scores": {}, "comment": "内容为空"}
    llm = MaterialRegistry.llm
    try:
        if hasattr(llm, "__call__") and type(llm).__name__ != "NullLLM":
            user = f"主题：{topic}（{subject}）\n\n【物料】\n{text[:3000]}"
            raw = llm(_JUDGE_SYSTEM, user, max_tokens=800)
            import json as _json
            try:
                # 提取 JSON
                start = raw.find("{")
                end = raw.rfind("}") + 1
                if start >= 0 and end > start:
                    data = _json.loads(raw[start:end])
                    scores = data.get("scores", {})
                    total = data.get("total", 0)
                    if not total and scores:
                        total = round(sum(scores.values()) / len(scores), 1)
                    return {"scores": scores, "total": total, "comment": data.get("comment", "")}
            except Exception:
                pass
            return {"total": 5.0, "scores": {}, "comment": raw[:200]}
        # 弱模式：确定性启发式
        scores = {
            "factuality": 5.0, "correctness": 5.0, "completeness": 5.0,
            "relevance": 5.0, "pedagogy": 5.0,
        }
        # 完整度启发：越长越完整
        if len(text) > 500:
            scores["completeness"] = 7.0
        if len(text) > 1000:
            scores["completeness"] = 8.5
        # 占位检测
        if "待生成" in text or "占位" in text:
            for k in scores:
                scores[k] = min(scores[k], 3.0)
        total = round(sum(scores.values()) / 5, 1)
        return {"scores": scores, "total": total, "comment": "弱模式启发式评分（未注入 LLM）"}
    except Exception as e:
        return {"total": 0, "scores": {}, "comment": f"评审失败: {str(e)[:100]}"}
