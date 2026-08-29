# -*- coding: utf-8 -*-
"""paeg_teaching_materials.mcp_server — 教学物料制作 MCP server（可直接安装使用 ⭐）。

可及性标准（用户 §3.110）：像 MCP server 一样**直接安装即可用**——
任何项目 pip install 后，在 MCP 客户端配置声明本 server 即可接入，零代码桥。

## 使用方式

```bash
# 方式 1：console_scripts 入口（pip install 后）
paeg-teaching-materials-mcp

# 方式 2：python -m 入口（源码运行）
python -m paeg_teaching_materials.mcp_server

# 方式 3：stdio 声明（MCP 客户端配置）
# {"command": "python", "args": ["-m", "paeg_teaching_materials.mcp_server"], "cwd": "..."}
```

## 暴露的 MCP 工具（12 个）

| 工具名 | 功能 |
|---|---|
| generate_ppt | PPT 大纲生成（6x6 原则） |
| generate_handout | 讲义生成（6 段结构） |
| generate_script | 讲稿生成（分段 narration） |
| generate_mindmap | 思维导图生成（层级） |
| generate_video_script | 教学视频分镜脚本（8-15s/镜） |
| generate_manim | Manim 数学动画代码生成 |
| material_quality_check | 物料确定性结构检查 |
| material_judge | 物料 5 维评审 |
| list_material_types | 物料类型自省 |
| build_material_prompt | 物料提示词拼装 |
| check_language | 物料语言规范检查（L0） |
| normalize_material | 物料语言规范守门 |
"""

from __future__ import annotations

import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

try:
    from fastmcp import FastMCP
except ImportError:
    FastMCP = None

from .executor import execute
from .registry import MaterialRegistry
from .generators import register_defaults

SERVER_NAME = "paeg-teaching-materials"


def build_server() -> "FastMCP":
    """构建 MCP server（幂等）。"""
    if FastMCP is None:
        raise RuntimeError("fastmcp 未安装：pip install 'paeg-teaching-materials[mcp]'")

    register_defaults()  # 注册 6 默认生成器（可被宿主 inject 覆盖）
    mcp = FastMCP(name=SERVER_NAME, strict_input_validation=True)

    @mcp.tool()
    def generate_ppt(topic: str, subject: str = "通用", learner_id: str = "anon") -> str:
        """生成 PPT 大纲（6x6 原则：每页≤6行、每行≤6字）。返回 markdown 大纲。"""
        return execute("generate_ppt", {"topic": topic, "subject": subject, "learner_id": learner_id})

    @mcp.tool()
    def generate_handout(topic: str, subject: str = "通用", learner_id: str = "anon") -> str:
        """生成讲义（6 段结构：教学目标/导入/新课/巩固/小结/作业）。返回 markdown。"""
        return execute("generate_handout", {"topic": topic, "subject": subject, "learner_id": learner_id})

    @mcp.tool()
    def generate_script(topic: str, subject: str = "通用", learner_id: str = "anon") -> str:
        """生成讲稿（分段 narration，可 TTS）。返回 markdown。"""
        return execute("generate_script", {"topic": topic, "subject": subject, "learner_id": learner_id})

    @mcp.tool()
    def generate_mindmap(topic: str, subject: str = "通用", learner_id: str = "anon") -> str:
        """生成思维导图（中心主题→3-5 分支→2-4 子分支）。返回 markdown 缩进列表。"""
        return execute("generate_mindmap", {"topic": topic, "subject": subject, "learner_id": learner_id})

    @mcp.tool()
    def generate_video_script(topic: str, subject: str = "通用", learner_id: str = "anon") -> str:
        """生成教学视频分镜脚本（8-15s/镜，音画对齐，钩子开头+recap 结尾）。返回 JSON 数组。"""
        return execute("generate_video_script", {"topic": topic, "subject": subject, "learner_id": learner_id})

    @mcp.tool()
    def generate_manim(topic: str, subject: str = "通用", learner_id: str = "anon",
                       render: bool = False) -> str:
        """生成 Manim 数学动画代码（可选渲染 mp4）。返回 Python 代码。"""
        return execute("generate_manim", {"topic": topic, "subject": subject,
                                          "learner_id": learner_id, "render": render})

    @mcp.tool()
    def material_quality_check(text: str, material_type: str = "handout") -> str:
        """物料确定性结构检查（占位残留/结构完整/长度）。返回问题列表。"""
        return execute("material_quality_check", {"text": text, "material_type": material_type})

    @mcp.tool()
    def material_judge(text: str, topic: str = "") -> str:
        """物料 5 维评审（factuality/correctness/completeness/relevance/pedagogy）。返回评分。"""
        return execute("material_judge", {"text": text, "topic": topic})

    @mcp.tool()
    def list_material_types() -> str:
        """物料类型自省：列出已注册的物料类型与生成器。"""
        return execute("list_material_types", {})

    @mcp.tool()
    def build_material_prompt(material_type: str = "handout", topic: str = "",
                              subject: str = "通用") -> str:
        """物料提示词拼装（角色+schema+硬约束）。返回系统提示词片段。"""
        try:
            from .prompts import build_material_system
            return build_material_system(material_type, topic, subject)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:200]}, ensure_ascii=False)

    @mcp.tool()
    def check_language(text: str) -> str:
        """物料语言规范检查（L0 规则：词法完整/句法完整/充分状语）。返回问题列表。"""
        try:
            from .quality.checks import check_material_structure
            issues = check_material_structure(text)
            return json.dumps({"ok": True, "issues": issues}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:200]}, ensure_ascii=False)

    @mcp.tool()
    def normalize_material(text: str) -> str:
        """物料语言规范守门（L0 病句修正）。返回规范化文本。"""
        from .quality.checks import apply_language_l0
        return apply_language_l0(text)

    # ─────────────────────────────────────
    # ⭐ 网状联通（Oracle §3.110）：独立调用 / 组合编排 / 依赖自省
    # ─────────────────────────────────────
    @mcp.tool()
    def execute_tool(tool_name: str, topic: str = "", subject: str = "通用",
                     learner_id: str = "anon", inputs_json: str = "{}") -> str:
        """独立执行单个功能节点（网状联通：每个功能可独立使用）。
        如 execute_tool("research") / execute_tool("outline") / execute_tool("ppt")。
        返回 JSON 字符串。"""
        try:
            import asyncio
            from .core import MaterialContext
            ctx = MaterialContext(topic=topic or None, subject=subject, learner_id=learner_id)
            import json as _json
            inputs = _json.loads(inputs_json) if inputs_json else {"topic": topic}
            result = asyncio.run(MaterialRegistry.execute_tool(tool_name, ctx, inputs))
            return _json.dumps({"ok": True, "tool": tool_name, "result": result,
                                "ctx": ctx.to_dict()}, ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:300]}, ensure_ascii=False)

    @mcp.tool()
    def execute_pipeline(target: str, topic: str = "", subject: str = "通用",
                         learner_id: str = "anon") -> str:
        """网状编排：按依赖图自动展开 target 的前置环节并执行。
        如 execute_pipeline("ppt") 自动先查资料→大纲→PPT。
        返回最终产物 + 已执行阶段。"""
        try:
            import json as _json
            from .core import MaterialContext
            ctx = MaterialContext(topic=topic or None, subject=subject, learner_id=learner_id)
            result = MaterialRegistry.execute_plan(target, ctx, {"topic": topic})
            return _json.dumps({"ok": True, "target": target, "result": result,
                                "completed_stages": sorted(ctx.completed_stages),
                                "ctx": ctx.to_dict()}, ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:300]}, ensure_ascii=False)

    @mcp.tool()
    def list_dependencies(target: str = "", format: str = "json") -> str:
        """网状联通自省：展示功能依赖图（谁是谁的前置环节）。
        format ∈ {json, ascii}；target 为空输出全网，否则输出该节点子树。"""
        try:
            import json as _json
            resolver = MaterialRegistry.get_resolver()
            graph = resolver.dependency_graph()
            if format == "ascii":
                lines = []
                for name, meta in graph.items():
                    reqs = ", ".join(f"{d['source']}({d['mode']})" for d in meta["requires"]) or "无前置"
                    lines.append(f"{name} 产出[{meta['produces']}] 前置[{reqs}]")
                return "\n".join(lines)
            return _json.dumps({"ok": True, "graph": graph}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:300]}, ensure_ascii=False)

    # ─────────────────────────────────────
    # §3.111 ⭐ R8 Manim 5 工具（顶尖化 MCP 暴露）
    # ─────────────────────────────────────
    @mcp.tool()
    def render_manim(topic: str, subject: str = "数学", audience: str = "高中",
                     duration_target_sec: int = 120) -> str:
        """渲染 Manim 数学动画（完整管线：剧本→代码→渲染→质量审计）。
        返回 {ok, url, script, code, lint_issues, mvqs, stages}。"""
        try:
            import json as _json
            r = json.loads(execute("generate_manim", {"topic": topic, "subject": subject,
                                                      "render": True}))
            return _json.dumps(r, ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:300]}, ensure_ascii=False)

    @mcp.tool()
    def plan_scenes(topic: str, subject: str = "数学", audience: str = "高中",
                    duration_target_sec: int = 120) -> str:
        """Manim 分镜规划（管线第一阶段）：生成剧本 JSON（3B1B 原则 + 叙事结构）。"""
        try:
            import json as _json
            # 复用 manim_quality 的叙事常量注入剧本 prompt
            r = json.loads(execute("generate_manim", {"topic": topic, "subject": subject}))
            return _json.dumps({"ok": True, "topic": topic,
                                "script_plan": r.get("output", "")[:2000],
                                "mvqs": r.get("mvqs"),
                                "lint_issues": r.get("lint_issues", [])},
                               ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:300]}, ensure_ascii=False)

    @mcp.tool()
    def audit_visual(code: str = "", topic: str = "") -> str:
        """Manim 视觉审计：MVQS 几何评估（无需渲染）+ safety lint（12 崩溃模式）。
        返回 {mvqs, lint_issues, verdict}。"""
        try:
            import json as _json
            from .manim_quality import mvqs_score, lint_manim_code
            if not code and topic:
                # 无代码时先生成
                r = json.loads(execute("generate_manim", {"topic": topic, "subject": "数学"}))
                code = r.get("output", "")
            _mvqs = mvqs_score(code)
            _lint = lint_manim_code(code)
            return _json.dumps({"ok": True, "mvqs": _mvqs,
                                "lint_issues": _lint[:10]}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:300]}, ensure_ascii=False)

    @mcp.tool()
    def tts_narrate(text: str, voice: str = "zh-CN-XiaoxiaoNeural") -> str:
        """TTS 旁白合成（edge-tts）：生成 narration MP3。
        返回 {ok, audio_path} 或错误。"""
        try:
            import json as _json
            from .tts_parallel import ParallelTTSSynthesizer
            s = ParallelTTSSynthesizer(voice=voice)
            # 单段旁白：直接合成到临时
            import os as _os
            _tmp = _os.path.join(_os.environ.get("TEMP", "/tmp"), f"paeg_tts_{abs(hash(text)) % 100000}.mp3")
            import asyncio, edge_tts
            async def _synth():
                comm = edge_tts.Communicate(str(text)[:1000], voice)
                await comm.save(_tmp)
            asyncio.run(_synth())
            ok = _os.path.isfile(_tmp) and _os.path.getsize(_tmp) > 0
            return _json.dumps({"ok": ok, "audio_path": _tmp if ok else ""},
                               ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:300]}, ensure_ascii=False)

    @mcp.tool()
    def mux_video_assets(video_path: str, narration: str = "",
                         scene_json: str = "[]") -> str:
        """视频与旁白合成（Audio-First）：ffmpeg mux MP3 → MP4。
        scene_json: [{id, narration}]——并行预合成后 mux。
        返回 {ok, out_path}。"""
        try:
            import json as _json
            from .tts_parallel import ParallelTTSSynthesizer
            scenes = _json.loads(scene_json) if scene_json else []
            s = ParallelTTSSynthesizer()
            if scenes:
                s.start(scenes)
                s.join(timeout=30)
            out = s.mux(video_path, narration)
            return _json.dumps({"ok": out is not None, "out_path": out or ""},
                               ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)[:300]}, ensure_ascii=False)

    # ─────────────────────────────────────
    # §3.116 ⭐ MCP 三原语补全：resources + prompts（给第三方完整接入）
    # ─────────────────────────────────────
    @mcp.resource("material-types://list")
    def material_types_resource() -> str:
        """物料类型清单（read-only 资源）：已注册物料类型与生成器。"""
        return execute("list_material_types", {})

    @mcp.resource("material-dependencies://graph")
    def material_dependencies_resource() -> str:
        """网状依赖图（read-only 资源）：功能节点的前置依赖关系。"""
        return execute("list_dependencies", {})

    @mcp.prompt()
    def material_build_workflow(topic: str) -> str:
        """物料制作工作流模板（6 类物料 → 网状编排）。"""
        return (
            f"请按教学物料制作流程为「{topic}」产出物料：\n"
            "1. 查资料（research，广播前置）：检索主题相关资料\n"
            "2. 大纲（outline）：结构化内容骨架\n"
            "3. 分物料生成：讲义 / 讲稿 / 思维导图 / PPT / 视频 / Manim 动画\n"
            "4. 质量检查：material_quality_check（结构）+ material_judge（5 维评审）\n"
            "5. 语言规范：normalize_material（L0 病句修正）\n"
            "可调用 execute_pipeline 自动编排（如 execute_pipeline('ppt') 自动查资料→大纲→PPT）。"
        )

    @mcp.prompt()
    def manim_production(topic: str) -> str:
        """Manim 数学动画制作流程模板（R8 顶尖化）。"""
        return (
            f"请按 Manim 动画制作管线为「{topic}」产出：\n"
            "1. plan_scenes：分镜规划（3B1B 原则 + 叙事结构）\n"
            "2. generate_manim：生成 Manim 代码（safe 12 崩溃模式防护）\n"
            "3. audit_visual：视觉审计（MVQS 几何评估 + safety lint）\n"
            "4. render_manim：渲染 mp4（质量审计）\n"
            "5. tts_narrate + mux_video_assets：旁白合成 + 音画 mux\n"
        )

    return mcp


def main():
    """CLI 入口：启动 MCP server（stdio 传输）。"""
    if FastMCP is None:
        print("错误：fastmcp 未安装，请先 pip install 'paeg-teaching-materials[mcp]'", file=sys.stderr)
        sys.exit(1)
    server = build_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
