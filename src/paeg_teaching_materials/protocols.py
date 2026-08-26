# -*- coding: utf-8 -*-
"""paeg_teaching_materials.protocols — 6 个宿主依赖抽象（零宿主依赖关键 ⭐）。

设计目标（Oracle R2）：教学物料插件独立于任何宿主项目（PAEG / 其他智能体）。
所有对宿主的依赖（LLM 调用 / 语言规范 / 各生成器 / 资源检索）抽象为 Protocol，
宿主通过 `MaterialRegistry.inject()` 注入实现；无宿主时用 Null 实现跑通（弱模式）。

6 个 Protocol（替代 PAEG 6 处 P0 耦合）：
1. LLMCallable        — 替代 subagents._safe_chat（11 处引用）
2. RefinerProtocol    — 替代 infra.runtime.get_paeg().refiner（lang_gate L2）
3. HandoutGenerator   — 替代 file_generator.FileGenerator
4. ScriptGenerator    — 替代 services.script_service
5. MindmapGenerator   — 替代 knowledge_map
6. ResourceProvider   — 替代 services.library.collect_all_resources
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


# ─────────────────────────────────────
# 1. LLMCallable（核心——所有生成器都依赖）
# ─────────────────────────────────────
@runtime_checkable
class LLMCallable(Protocol):
    """LLM 调用抽象（替代 subagents._safe_chat）。"""

    def __call__(self, system: str, user: str, *, max_tokens: int = 2000,
                 temperature: float = 0.7) -> str:
        ...


class NullLLM:
    """Null 实现：无宿主时返回空（弱模式，生成器降级为规则输出）。"""

    def __call__(self, system: str, user: str, *, max_tokens: int = 2000,
                 temperature: float = 0.7) -> str:
        return ""


# ─────────────────────────────────────
# 2. RefinerProtocol（语言规范 L2）
# ─────────────────────────────────────
@runtime_checkable
class RefinerProtocol(Protocol):
    """语言规范修正抽象（替代 infra.runtime.get_paeg().refiner）。"""

    def detect_ai_tells(self, text: str) -> List[str]:
        ...

    def refine(self, text: str, context: str = "") -> str:
        ...


class NullRefiner:
    """Null 实现：不做修正（原样返回）。"""

    def detect_ai_tells(self, text: str) -> List[str]:
        return []

    def refine(self, text: str, context: str = "") -> str:
        return text


# ─────────────────────────────────────
# 3. HandoutGenerator（讲义生成）
# ─────────────────────────────────────
@runtime_checkable
class HandoutGenerator(Protocol):
    """讲义生成抽象（替代 file_generator.FileGenerator）。"""

    def generate(self, topic: str, subject: str, learner_id: str = "anon", **kw) -> Dict[str, Any]:
        ...


class NullHandoutGenerator:
    """Null 实现：返回结构化占位讲义。"""

    def generate(self, topic: str, subject: str, learner_id: str = "anon", **kw) -> Dict[str, Any]:
        return {
            "material_type": "handout", "topic": topic, "subject": subject,
            "ok": False, "output": f"（Null 讲义生成器——未注入宿主实现）主题：{topic}",
        }


# ─────────────────────────────────────
# 4. ScriptGenerator（讲稿生成）
# ─────────────────────────────────────
@runtime_checkable
class ScriptGenerator(Protocol):
    """讲稿生成抽象（替代 services.script_service）。"""

    def generate(self, topic: str, subject: str, learner_id: str = "anon", **kw) -> Dict[str, Any]:
        ...


class NullScriptGenerator:
    """Null 实现：返回结构化占位讲稿。"""

    def generate(self, topic: str, subject: str, learner_id: str = "anon", **kw) -> Dict[str, Any]:
        return {
            "material_type": "script", "topic": topic, "subject": subject,
            "ok": False, "output": f"（Null 讲稿生成器——未注入宿主实现）主题：{topic}",
        }


# ─────────────────────────────────────
# 5. MindmapGenerator（思维导图生成）
# ─────────────────────────────────────
@runtime_checkable
class MindmapGenerator(Protocol):
    """思维导图生成抽象（替代 knowledge_map）。"""

    def generate(self, topic: str, subject: str, **kw) -> Dict[str, Any]:
        ...


class NullMindmapGenerator:
    """Null 实现：返回结构化占位思维导图。"""

    def generate(self, topic: str, subject: str, **kw) -> Dict[str, Any]:
        return {
            "material_type": "mindmap", "topic": topic, "subject": subject,
            "ok": False, "output": f"（Null 思维导图生成器——未注入宿主实现）主题：{topic}",
        }


# ─────────────────────────────────────
# 6. ResourceProvider（资源检索）
# ─────────────────────────────────────
@runtime_checkable
class ResourceProvider(Protocol):
    """资源检索抽象（替代 services.library.collect_all_resources）。"""

    def collect_all_resources(self, topic: str, subject: str) -> List[Dict[str, Any]]:
        ...

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        ...


class NullResourceProvider:
    """Null 实现：无资源（返回空列表）。"""

    def collect_all_resources(self, topic: str, subject: str) -> List[Dict[str, Any]]:
        return []

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        return []


# ─────────────────────────────────────
# 默认 Null 实现单例（无宿主时用）
# ─────────────────────────────────────
DEFAULT_LLM: LLMCallable = NullLLM()
DEFAULT_REFINER: RefinerProtocol = NullRefiner()
DEFAULT_HANDOUT: HandoutGenerator = NullHandoutGenerator()
DEFAULT_SCRIPT: ScriptGenerator = NullScriptGenerator()
DEFAULT_MINDMAP: MindmapGenerator = NullMindmapGenerator()
DEFAULT_RESOURCES: ResourceProvider = NullResourceProvider()
