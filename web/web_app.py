# -*- coding: utf-8 -*-
"""teaching_materials_web — 教学物料制作独立网页后端（Flask API）。

提供：主题/学科 → 选物料类型（PPT/讲义/讲稿/思维导图/视频/Manim）→ 生成 → 质量检查。
复用 paeg-teaching-materials 的 execute 统一入口（环境变量 LLM 独立接入）。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from flask import Flask, jsonify, request

# 插件 src（web/ 的上一级 = 插件根目录）
_PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.path.join(_PLUGIN_ROOT, "src")
if os.path.isdir(_SRC) and _SRC not in sys.path:
    sys.path.insert(0, _SRC)

_WEB_DIR = Path(__file__).resolve().parent  # web 目录

# 物料类型 → execute 工具名
_MATERIAL_TOOLS = {
    "ppt": "generate_ppt",
    "handout": "generate_handout",
    "script": "generate_script",
    "mindmap": "generate_mindmap",
    "video": "generate_video_script",
    "manim": "generate_manim",
}

# 物料类型元信息（前端展示用）
# §3.116 ⭐ 前端图标一律内联 SVG（不用 emoji——跨平台渲染一致、可缩放着色）
_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round">{}</svg>'
)
_MATERIAL_META = {
    "ppt": {"label": "PPT 演示文稿",
            "icon": _SVG.format('<path d="M2 3h20"/><path d="M21 3v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V3"/><path d="m7 21 5-5 5 5"/>'),
            "desc": "6x6 原则大纲，可选 python-pptx 渲染"},
    "handout": {"label": "讲义",
                "icon": _SVG.format('<path d="M12 5v16"/><path d="M20 19a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2l-4 .998A5 5 0 0 0 12 5a5 5 0 0 0-4-2H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h4a5 5 0 0 1 4 2 5 5 0 0 1 4-2z"/>'),
                "desc": "6 段结构（目标/导入/新课/巩固/小结/作业）"},
    "script": {"label": "讲稿",
               "icon": _SVG.format('<path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/>'),
               "desc": "分段 narration，可 TTS 朗读"},
    "mindmap": {"label": "思维导图",
                "icon": _SVG.format('<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" x2="15.42" y1="13.51" y2="17.49"/><line x1="15.41" x2="8.59" y1="6.51" y2="10.49"/>'),
                "desc": "中心主题 → 3-5 分支 → 2-4 子分支"},
    "video": {"label": "教学视频分镜",
              "icon": _SVG.format('<path d="M20.2 6 3 11l-.9-2.4c-.3-1.1.3-2.2 1.3-2.5l13.5-4c1.1-.3 2.2.3 2.5 1.3Z"/><path d="m6.2 5.3 3.1 3.9"/><path d="m12.4 3.4 3.1 4"/><path d="M3 11h18v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/>'),
              "desc": "8-15s/镜，音画对齐，钩子+recap"},
    "manim": {"label": "Manim 数学动画",
              "icon": _SVG.format('<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M7 3v18"/><path d="M3 7.5h4"/><path d="M3 12h18"/><path d="M3 16.5h4"/><path d="M17 3v18"/><path d="M17 7.5h4"/>'),
              "desc": "数学动画代码 + 安全 lint + MVQS 评估"},
}


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)

    @app.route("/api/health")
    def health():
        from paeg_teaching_materials.llm_client import available
        return jsonify({"ok": True, "service": "teaching-materials-web",
                        "llm_available": available()})

    @app.route("/api/materials")
    def materials():
        return jsonify({"ok": True, "materials": [
            {"type": t, **_MATERIAL_META[t]} for t in _MATERIAL_TOOLS
        ]})

    @app.route("/api/generate", methods=["POST"])
    def generate():
        data = request.get_json(force=True) or {}
        topic = (data.get("topic", "") or "").strip()
        material_type = data.get("material_type", "handout")
        subject = (data.get("subject", "") or "通用").strip()
        if not topic:
            return jsonify({"ok": False, "error": "缺少 topic"}), 400
        if material_type not in _MATERIAL_TOOLS:
            return jsonify({"ok": False, "error": f"未知物料类型: {material_type}"}), 400
        try:
            from paeg_teaching_materials import execute
            tool = _MATERIAL_TOOLS[material_type]
            raw = execute(tool, {"topic": topic, "subject": subject})
            result = json.loads(raw)
            result["material_type"] = material_type
            return jsonify(result)
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)[:300]})

    @app.route("/api/quality", methods=["POST"])
    def quality():
        data = request.get_json(force=True) or {}
        text = data.get("text", "")
        material_type = data.get("material_type", "handout")
        if not text:
            return jsonify({"ok": False, "error": "缺少 text"}), 400
        try:
            from paeg_teaching_materials import execute
            raw = execute("material_quality_check",
                          {"text": text, "material_type": material_type})
            return jsonify(json.loads(raw))
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)[:200]})

    @app.route("/")
    def index():
        idx = _WEB_DIR / "index.html"
        if idx.exists():
            return idx.read_text(encoding="utf-8")
        return "教学物料制作网页运行中（前端待构建）"

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5001, debug=False)
