# -*- coding: utf-8 -*-
"""paeg_teaching_materials.generators — 6 类物料生成器（ppt/script/mindmap/video/manim）。

强实现：注入 LLM 后生成；弱实现：无 LLM 时结构化占位（弱模式可跑通）。
PPT 生成器可调用 python-pptx（可选依赖）渲染真实 .pptx。
"""

from __future__ import annotations

from typing import Any, Dict

from ..registry import MaterialRegistry
from .base import Generator
from .handout import HandoutGenerator

__all__ = ["HandoutGenerator", "PptGenerator", "ScriptGenerator", "MindmapGenerator",
           "VideoGenerator", "ManimGenerator"]


class PptGenerator(Generator):
    """PPT 生成器：LLM 生成大纲 → （可选）python-pptx 渲染。"""

    material_type = "ppt"

    def generate(self, topic: str, subject: str = "通用",
                 learner_id: str = "anon", **kw) -> Dict[str, Any]:
        llm = MaterialRegistry.llm
        try:
            if hasattr(llm, "__call__") and type(llm).__name__ != "NullLLM":
                system = ("你是演示文稿专家。为指定主题设计 PPT 大纲。"
                          "要求：6x6 原则（每页≤6行、每行≤6字）、封面+内容+结尾结构、"
                          "语言规范（词法完整/句法完整）。输出 markdown 大纲，用 ## 分页。")
                user = f"主题：{topic}（{subject}）。"
                outline = llm(system, user, max_tokens=1500)
                if not outline:  # 无 key 降级弱模式
                    return {
                        "material_type": "ppt", "topic": topic, "subject": subject,
                        "ok": False,
                        "output": f"# {topic} PPT 大纲（弱模式占位）\n\n## 封面\n{topic}\n## 内容\n（待生成）",
                    }
                # 可选渲染 pptx（真实落盘）
                path = None
                if kw.get("render", False):
                    try:
                        from ..adapters.pptx_renderer import render_outline_to_pptx
                        path = render_outline_to_pptx(outline, topic,
                                                      out_dir=kw.get("out_dir"))
                    except Exception as e:
                        path = f"（渲染失败: {str(e)[:120]}）"
                return {
                    "material_type": "ppt", "topic": topic, "subject": subject,
                    "ok": True, "output": outline,
                    "pptx_path": path,
                }
            return {
                "material_type": "ppt", "topic": topic, "subject": subject,
                "ok": False,
                "output": f"# {topic} PPT 大纲（弱模式占位）\n\n## 封面\n{topic}\n## 内容\n（待生成）",
            }
        except Exception as e:
            return {"material_type": "ppt", "topic": topic, "subject": subject,
                    "ok": False, "error": f"PPT 生成失败: {str(e)[:200]}"}


class ScriptGenerator(Generator):
    """讲稿生成器：LLM 生成分段讲稿（含 narration）。"""

    material_type = "script"

    def generate(self, topic: str, subject: str = "通用",
                 learner_id: str = "anon", **kw) -> Dict[str, Any]:
        llm = MaterialRegistry.llm
        try:
            if hasattr(llm, "__call__") and type(llm).__name__ != "NullLLM":
                system = ("你是教学讲稿撰写专家。为指定主题编写完整讲稿。"
                          "要求：口语化但规范（词法完整/句法完整/充分状语）、"
                          "有开场导入、分节展开、小结收尾、可 TTS 朗读。"
                          "输出 markdown，用 ## 分节。")
                user = f"主题：{topic}（{subject}）。"
                script = llm(system, user, max_tokens=2000)
                if not script:  # 无 key 降级弱模式
                    return {
                        "material_type": "script", "topic": topic, "subject": subject,
                        "ok": False,
                        "output": f"# {topic} 讲稿（弱模式占位）\n\n## 开场\n（待生成）\n## 主体\n（待生成）\n## 小结\n（待生成）",
                    }
                # 可选渲染落盘：TTS 旁白合成 mp3
                audio_path = None
                if kw.get("render", False):
                    try:
                        from ..adapters.tts_synth import synthesize_script_audio
                        audio_path = synthesize_script_audio(
                            script, topic=topic, out_dir=kw.get("out_dir"))
                    except Exception as e:
                        audio_path = f"（TTS 渲染失败: {str(e)[:120]}）"
                return {
                    "material_type": "script", "topic": topic, "subject": subject,
                    "ok": True, "output": script,
                    "audio_path": audio_path,
                }
            return {
                "material_type": "script", "topic": topic, "subject": subject,
                "ok": False,
                "output": f"# {topic} 讲稿（弱模式占位）\n\n## 开场\n（待生成）\n## 主体\n（待生成）\n## 小结\n（待生成）",
            }
        except Exception as e:
            return {"material_type": "script", "topic": topic, "subject": subject,
                    "ok": False, "error": f"讲稿生成失败: {str(e)[:200]}"}


class MindmapGenerator(Generator):
    """思维导图生成器：LLM 生成层级结构。"""

    material_type = "mindmap"

    def generate(self, topic: str, subject: str = "通用",
                 learner_id: str = "anon", **kw) -> Dict[str, Any]:
        llm = MaterialRegistry.llm
        try:
            if hasattr(llm, "__call__") and type(llm).__name__ != "NullLLM":
                system = ("你是知识结构化专家。为指定主题生成思维导图。"
                          "要求：中心主题→3-5 个一级分支→每个 2-4 个二级分支、"
                          "层级清晰、关键词简洁。输出 markdown 缩进列表。")
                user = f"主题：{topic}（{subject}）。"
                mindmap = llm(system, user, max_tokens=1000)
                if not mindmap:  # 无 key 降级弱模式
                    return {
                        "material_type": "mindmap", "topic": topic, "subject": subject,
                        "ok": False,
                        "output": f"# {topic} 思维导图（弱模式占位）\n- 中心主题\n  - （待生成）",
                    }
                return {
                    "material_type": "mindmap", "topic": topic, "subject": subject,
                    "ok": True, "output": mindmap,
                }
            return {
                "material_type": "mindmap", "topic": topic, "subject": subject,
                "ok": False,
                "output": f"# {topic} 思维导图（弱模式占位）\n- 中心主题\n  - （待生成）",
            }
        except Exception as e:
            return {"material_type": "mindmap", "topic": topic, "subject": subject,
                    "ok": False, "error": f"思维导图生成失败: {str(e)[:200]}"}


class VideoGenerator(Generator):
    """教学视频生成器：LLM 生成分镜脚本（8-15s/镜）。"""

    material_type = "video"

    def generate(self, topic: str, subject: str = "通用",
                 learner_id: str = "anon", **kw) -> Dict[str, Any]:
        llm = MaterialRegistry.llm
        try:
            if hasattr(llm, "__call__") and type(llm).__name__ != "NullLLM":
                system = ("你是教学视频导演。为指定主题设计分镜脚本。"
                          "要求：每个镜头 8-15 秒、音画对齐（画面+旁白）、"
                          "钩子开头 + recap 结尾、3B1B 视觉原则（渐进披露）。"
                          "输出 JSON 数组 [{'scene': n, 'duration': s, 'visual': ..., 'narration': ...}]")
                user = f"主题：{topic}（{subject}）。"
                script = llm(system, user, max_tokens=2000)
                if not script:  # 无 key 降级弱模式
                    return {
                        "material_type": "video", "topic": topic, "subject": subject,
                        "ok": False,
                        "output": f"# {topic} 分镜脚本（弱模式占位）\n\n[{{'scene': 1, 'duration': 10, 'visual': '（待生成）', 'narration': '（待生成）'}}]",
                    }
                return {
                    "material_type": "video", "topic": topic, "subject": subject,
                    "ok": True, "output": script,
                }
            return {
                "material_type": "video", "topic": topic, "subject": subject,
                "ok": False,
                "output": f"# {topic} 分镜脚本（弱模式占位）\n\n[{'scene': 1, 'duration': 10, 'visual': '（待生成）', 'narration': '（待生成）'}]",
            }
        except Exception as e:
            return {"material_type": "video", "topic": topic, "subject": subject,
                    "ok": False, "error": f"视频分镜生成失败: {str(e)[:200]}"}


class ManimGenerator(Generator):
    """Manim 数学动画生成器：LLM 生成 Manim 代码（可选渲染 mp4）。

    §3.111 ⭐ 顶尖化：RITL 渲染错误回灌（错误 tail → 修复 → 重试 K 轮）
    + safe_manim 12 崩溃模式 lint（生成后自动检测高危模式）。
    """

    material_type = "manim"

    def generate(self, topic: str, subject: str = "通用",
                 learner_id: str = "anon", **kw) -> Dict[str, Any]:
        llm = MaterialRegistry.llm
        try:
            if hasattr(llm, "__call__") and type(llm).__name__ != "NullLLM":
                # §3.111 ⭐ R7 叙事质量（同步主项目 manim_narrative 增强）
                try:
                    from ..manim_quality import VISUAL_PRINCIPLES_17, NARRATIVE_ARC_PROMPT
                    _vp, _na = VISUAL_PRINCIPLES_17, NARRATIVE_ARC_PROMPT
                except Exception:
                    _vp, _na = "", ""
                system = ("你是 Manim 动画专家。为数学/物理概念生成 Manim 代码。\n"
                          "要求：import 完整、Scene 类含 construct、\n"
                          "渐进披露（TransformMatchingTex）、每动画≤5s、可渲染。\n"
                          "注意：Create 只用于几何图形（Text 用 Write）；MathTex 不要 $；\n"
                          "Brace.get_text 不要传 font_size；transform 用 ReplacementTransform。\n"
                          + (_vp + "\n" if _vp else "")
                          + (_na + "\n" if _na else "")
                          + "只输出 Python 代码。")
                user = f"主题：{topic}（{subject}）。"
                code = llm(system, user, max_tokens=2000)
                if not code:  # 无 key 降级弱模式
                    return {
                        "material_type": "manim", "topic": topic, "subject": subject,
                        "ok": False,
                        "output": f"# {topic} Manim 动画（弱模式占位）\n# 需注入 LLM 后生成代码",
                    }

                # §3.111 ⭐ 清洗 LLM 输出（剥离代码块外壳/说明/全角标点/$ 残留——
                # 否则 lint/mvqs/渲染在 ast.parse 阶段直接失败）
                try:
                    from ..manim_quality import clean_manim_code as _clean
                    code = _clean(code)
                except Exception:
                    _clean = None

                # §3.111 ⭐ safety lint（12 崩溃模式）
                try:
                    from ..manim_quality import lint_manim_code
                    _lint = lint_manim_code(code)
                except Exception:
                    _lint = []

                # §3.111 ⭐ R5 MVQS 几何评估（代码级，无需渲染）
                try:
                    from ..manim_quality import mvqs_score
                    _mvqs = mvqs_score(code)
                except Exception:
                    _mvqs = None

                # §3.111 ⭐ RITL 渲染错误回灌（K=3 轮）
                render_ok = False
                render_info = {}
                if kw.get("render", False):
                    try:
                        from ..adapters.manim_runtime import (
                            render_manim_code, manim_available, save_manim_code)
                        _out_dir = kw.get("out_dir")
                        if not manim_available():
                            # 依赖缺失优雅降级：仍落盘 .py 代码
                            try:
                                render_info["code_path"] = save_manim_code(
                                    code, topic, out_dir=_out_dir)
                            except Exception:
                                pass
                            render_info["render_skip"] = (
                                "Manim 渲染环境不可用（未安装 manim/ffmpeg；已保存 .py 代码）")
                        else:
                            for _r in range(3):
                                try:
                                    mp4 = render_manim_code(code, topic, out_dir=_out_dir)
                                    render_ok = True
                                    render_info = {"mp4_path": mp4}
                                    break
                                except Exception as _re:
                                    _err = str(_re)
                                    if _err.startswith("MANIM_UNAVAILABLE:"):
                                        render_info["render_skip"] = _err[18:].strip()
                                        break
                                    # RITL-DOC：错误 + API 签名注入 → LLM 修复 → 重试
                                    try:
                                        from ..manim_quality import build_ritl_doc_block
                                        _fix_sys = "你是 Manim 代码修复器。根据渲染错误修复代码。输出完整代码。"
                                        _fix_usr = build_ritl_doc_block(code, _err[:500])
                                        _fixed = llm(_fix_sys, _fix_usr, max_tokens=2000)
                                        if _fixed and "class " in _fixed:
                                            code = _clean(_fixed) if _clean else _fixed
                                            continue
                                    except Exception:
                                        pass
                                    render_info["render_error"] = _err[:200]
                                    break
                    except Exception as e:
                        render_info["render_skip"] = f"渲染环境不可用: {str(e)[:100]}"

                result = {
                    "material_type": "manim", "topic": topic, "subject": subject,
                    "ok": True, "output": code,
                    "lint_issues": _lint[:8],   # §3.111 safety lint 报告
                    "mvqs": _mvqs,              # §3.111 R5 MVQS 几何评估
                }
                if render_info:
                    result.update(render_info)
                return result
            return {
                "material_type": "manim", "topic": topic, "subject": subject,
                "ok": False,
                "output": "# {topic} Manim 动画（弱模式占位）\n# 需注入 LLM 后生成代码",
            }
        except Exception as e:
            return {"material_type": "manim", "topic": topic, "subject": subject,
                    "ok": False, "error": f"Manim 生成失败: {str(e)[:200]}"}


def register_defaults() -> None:
    """注册 6 个默认生成器到 MaterialRegistry。"""
    from ..registry import MaterialRegistry as MR
    MR.register("handout", generator=HandoutGenerator())
    MR.register("ppt", generator=PptGenerator())
    MR.register("script", generator=ScriptGenerator())
    MR.register("mindmap", generator=MindmapGenerator())
    MR.register("video", generator=VideoGenerator())
    MR.register("manim", generator=ManimGenerator())
