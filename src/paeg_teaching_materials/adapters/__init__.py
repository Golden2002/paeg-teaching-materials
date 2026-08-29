# -*- coding: utf-8 -*-
"""paeg_teaching_materials.adapters — 真实渲染落盘适配器（可拆卸 ⭐）。

三个可选渲染后端，依赖缺失时优雅降级（由上层生成器捕获并返回提示）：
- pptx_renderer : python-pptx 生成真实 .pptx（PPT 大纲 → 演示文稿）
- manim_runtime : Manim 渲染 mp4（LLM 代码 → 数学动画视频）
- tts_synth     : edge-tts 合成讲稿旁白 mp3（讲稿 → 语音）

这些模块对核心包**零强制依赖**：python-pptx / manim / edge-tts 均在各
函数内懒加载，未安装时抛 RuntimeError（含安装提示），生成器捕获后
在 result 里返回「渲染失败/环境不可用」提示，绝不中断主流程。
"""

from __future__ import annotations

__all__ = ["pptx_renderer", "manim_runtime", "tts_synth"]
