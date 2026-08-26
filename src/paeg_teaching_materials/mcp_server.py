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
