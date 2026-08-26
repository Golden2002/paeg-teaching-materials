# -*- coding: utf-8 -*-
"""paeg_teaching_materials — 教学物料制作插件（可拆卸、可独立、可接入任何智能体 ⭐）。

用户需求（§3.110）：
1. 6 类物料生成：PPT / 讲义 / 讲稿 / 思维导图 / 教学视频 / Manim 数学动画
2. 像 MCP server 一样直接安装即可用（console_scripts + python -m 入口 + stdio）
3. 零宿主依赖（6 个 Protocol 抽象 + Null 实现弱模式）
4. 可扩充（MaterialRegistry 注册自定义物料类型）
5. 主项目零破坏接入（bridge 注入）

公共 API：
    MaterialRegistry          — 生成器注册表 + 宿主依赖注入
    execute(name, args)       — 统一执行入口（MCP 契约）
    protocols.*               — 6 个宿主依赖抽象
    generators.*              — 6 类物料生成器
    quality.checks / judge    — 质量检查与评审
    mcp_server.build_server   — MCP server 构建
"""

from __future__ import annotations

from .registry import MaterialRegistry, MATERIAL_TYPES
from .executor import execute
from .generators import (
    HandoutGenerator, PptGenerator, ScriptGenerator, MindmapGenerator,
    VideoGenerator, ManimGenerator, register_defaults,
)
from .protocols import (
    LLMCallable, RefinerProtocol, HandoutGenerator as HandoutProtocol,
    ScriptGenerator as ScriptProtocol, MindmapGenerator as MindmapProtocol,
    ResourceProvider,
    NullLLM, NullRefiner, NullResourceProvider,
)
from .quality.checks import check_material_structure, apply_language_l0
from .quality.judge import judge_material

# ⭐ 网状联通（Oracle §3.110）
from .core import (
    Tool, MaterialContext, Dependency,
    broadcast, directed, optional,
    Pipeline, Resolver, ExecutionPlan, ExecutionStep,
)

__version__ = "0.1.0"

# 导入时注册默认生成器（弱模式可跑通）
register_defaults()

# ⭐ 网状联通：注册功能节点（Research/Outline/PPT/讲义/讲稿/视频/思维导图/Manim/方法/计划）
from .tools import register_mesh_tools
register_mesh_tools()

__all__ = [
    # 核心 API
    "MaterialRegistry", "MATERIAL_TYPES", "execute",
    # 生成器
    "HandoutGenerator", "PptGenerator", "ScriptGenerator", "MindmapGenerator",
    "VideoGenerator", "ManimGenerator", "register_defaults",
    # 协议（宿主依赖抽象）
    "LLMCallable", "RefinerProtocol",
    "HandoutProtocol", "ScriptProtocol", "MindmapProtocol", "ResourceProvider",
    "NullLLM", "NullRefiner", "NullResourceProvider",
    # 质量
    "check_material_structure", "apply_language_l0", "judge_material",
    # ⭐ 网状联通（Tool 节点 + Context + 边 + Pipeline + Resolver）
    "Tool", "MaterialContext", "Dependency",
    "broadcast", "directed", "optional",
    "Pipeline", "Resolver", "ExecutionPlan", "ExecutionStep",
    # 元信息
    "__version__",
]
