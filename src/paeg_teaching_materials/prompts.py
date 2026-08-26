# -*- coding: utf-8 -*-
"""paeg_teaching_materials.prompts — 物料提示词模板（5 类 + 拼装器）。

从 PAEG material_prompts.py 平移（数据层，零依赖）。
"""

from __future__ import annotations

from typing import Dict

# 5 类物料模板（role / schema / hard_checks）
_MATERIAL_TEMPLATES: Dict[str, Dict] = {
    "handout": {
        "role": "你是一位资深教师，为指定主题编写结构化讲义。",
        "schema": "6 段结构：教学目标 / 课堂导入 / 新课讲授 / 巩固练习 / 课堂小结 / 课后作业",
        "hard_checks": ["每段有 ## 标题", "语言规范（词法完整/句法完整/充分状语）", "内容具体不空洞", "适合目标学段", "不含占位符"],
    },
    "ppt": {
        "role": "你是演示文稿专家，为指定主题设计 PPT 大纲。",
        "schema": "6x6 原则（每页≤6行、每行≤6字）+ 封面/内容/结尾",
        "hard_checks": ["每页信息不超载", "大纲可渲染", "语言规范", "视觉层级清晰", "不含占位符"],
    },
    "video": {
        "role": "你是教学视频导演，为指定主题设计分镜脚本。",
        "schema": "每镜头 8-15 秒 + 音画对齐（画面+旁白）",
        "hard_checks": ["钩子开头", "recap 结尾", "渐进披露", "时长合理", "不含占位符"],
    },
    "manim": {
        "role": "你是 Manim 动画专家，为数学/物理概念生成 Manim 代码。",
        "schema": "import 完整 + Scene 类含 construct + 渐进披露",
        "hard_checks": ["可渲染", "数学正确", "动画≤5s/个", "结构清晰", "不含占位符"],
    },
    "mindmap": {
        "role": "你是知识结构化专家，为指定主题生成思维导图。",
        "schema": "中心主题→3-5 一级分支→2-4 二级分支",
        "hard_checks": ["层级清晰", "关键词简洁", "覆盖主题", "不冗余", "不含占位符"],
    },
}


def build_material_system(material_type: str = "handout", topic: str = "",
                          subject: str = "通用") -> str:
    """拼装物料系统提示词（角色 + schema + 硬约束）。"""
    tpl = _MATERIAL_TEMPLATES.get(material_type, _MATERIAL_TEMPLATES["handout"])
    lines = [
        tpl["role"],
        f"主题：{topic or '（由用户指定）'}；学科：{subject}。",
        f"## 结构要求\n{tpl['schema']}",
        "## 硬性检查",
    ]
    for i, c in enumerate(tpl["hard_checks"], 1):
        lines.append(f"{i}. {c}")
    lines.append("## 语言规范\n- 词法完整（用完整词形，禁止单字压缩：倦→疲倦）\n- 句法完整（主谓宾齐全）\n- 充分状语（动作交代时间/方式/对象）")
    return "\n".join(lines)
