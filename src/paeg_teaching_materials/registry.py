# -*- coding: utf-8 -*-
"""paeg_teaching_materials.registry — 生成器注册表（Oracle R3 ⭐ 可扩充性核心）。

设计目标（对标 paeg-lang-style RuleRegistry 可扩展原则）：
- 物料类型 → 生成器注册（可扩充：第三方注册自定义物料类型）
- 宿主依赖注入（LLM / Refiner / ResourceProvider / 各生成器）
- 无宿主时 Null 实现跑通（弱模式）

用法：
    from paeg_teaching_materials import MaterialRegistry
    MaterialRegistry.inject(llm=my_llm, refiner=my_refiner)
    MaterialRegistry.register("ppt", generator=MyPptGenerator())
    gen = MaterialRegistry.get("ppt")
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .protocols import (
    LLMCallable, RefinerProtocol, HandoutGenerator, ScriptGenerator,
    MindmapGenerator, ResourceProvider,
    DEFAULT_LLM, DEFAULT_REFINER, DEFAULT_HANDOUT, DEFAULT_SCRIPT,
    DEFAULT_MINDMAP, DEFAULT_RESOURCES,
)

# 内置物料类型
MATERIAL_TYPES = ("ppt", "handout", "script", "video", "mindmap", "manim")


class MaterialRegistry:
    """物料生成器注册表：物料类型 → 生成器 + 宿主依赖注入。"""

    # 注册表（类级，全局单例）
    _generators: Dict[str, Any] = {}
    _pipelines: Dict[str, Any] = {}
    _extra_types: set = set()

    # 宿主依赖（类级，inject 注入）
    llm: LLMCallable = DEFAULT_LLM
    refiner: RefinerProtocol = DEFAULT_REFINER
    handout_gen: HandoutGenerator = DEFAULT_HANDOUT
    script_gen: ScriptGenerator = DEFAULT_SCRIPT
    mindmap_gen: MindmapGenerator = DEFAULT_MINDMAP
    resources: ResourceProvider = DEFAULT_RESOURCES

    # ── 宿主依赖注入（可及性 ⭐ 任何项目接入点）──
    @classmethod
    def inject(cls, *, llm: Optional[LLMCallable] = None,
               refiner: Optional[RefinerProtocol] = None,
               handout_gen: Optional[HandoutGenerator] = None,
               script_gen: Optional[ScriptGenerator] = None,
               mindmap_gen: Optional[MindmapGenerator] = None,
               resources: Optional[ResourceProvider] = None) -> None:
        """注入宿主实现（外部项目接入时调用）。"""
        if llm is not None:
            cls.llm = llm
        if refiner is not None:
            cls.refiner = refiner
        if handout_gen is not None:
            cls.handout_gen = handout_gen
        if script_gen is not None:
            cls.script_gen = script_gen
        if mindmap_gen is not None:
            cls.mindmap_gen = mindmap_gen
        if resources is not None:
            cls.resources = resources

    @classmethod
    def reset(cls) -> None:
        """重置为 Null 依赖（保留默认生成器——弱模式可跑通）。"""
        cls.llm = DEFAULT_LLM
        cls.refiner = DEFAULT_REFINER
        cls.handout_gen = DEFAULT_HANDOUT
        cls.script_gen = DEFAULT_SCRIPT
        cls.mindmap_gen = DEFAULT_MINDMAP
        cls.resources = DEFAULT_RESOURCES
        # 保留默认生成器（重新注册弱实现）；清空用户注册
        cls._extra_types = set()

    # ── 生成器注册（可扩充 ⭐）──
    @classmethod
    def register(cls, material_type: str, generator: Any = None,
                 pipeline: Any = None) -> bool:
        """注册物料生成器/流水线。同类型覆盖。"""
        if generator is not None:
            cls._generators[material_type] = generator
        if pipeline is not None:
            cls._pipelines[material_type] = pipeline
        if material_type not in MATERIAL_TYPES:
            cls._extra_types.add(material_type)
        return True

    @classmethod
    def unregister(cls, material_type: str) -> bool:
        cls._generators.pop(material_type, None)
        cls._pipelines.pop(material_type, None)
        cls._extra_types.discard(material_type)
        return True

    # ── 查询 ──
    @classmethod
    def get(cls, material_type: str) -> Any:
        """取生成器；未注册返回 None。"""
        return cls._generators.get(material_type)

    @classmethod
    def get_pipeline(cls, material_type: str) -> Any:
        return cls._pipelines.get(material_type)

    @classmethod
    def available_types(cls) -> list:
        """可用物料类型（内置 + 用户注册）。"""
        return sorted(set(MATERIAL_TYPES) | cls._extra_types)

    @classmethod
    def has(cls, material_type: str) -> bool:
        return material_type in cls._generators or material_type in MATERIAL_TYPES

    # ── 生成 ──
    @classmethod
    def generate(cls, material_type: str, topic: str, subject: str = "通用",
                 learner_id: str = "anon", **kw) -> Dict[str, Any]:
        """按物料类型生成（Registry 路由到生成器/流水线）。

        优先流水线（pipeline）；其次生成器（generator）；都无 → 返回占位错误。
        """
        # 1. 流水线优先
        pipeline = cls._pipelines.get(material_type)
        if pipeline is not None:
            try:
                if hasattr(pipeline, "run"):
                    return pipeline.run(topic=topic, subject=subject,
                                        learner_id=learner_id, **kw)
                return pipeline(topic=topic, subject=subject,
                                learner_id=learner_id, **kw)
            except Exception as e:
                return {"ok": False, "material_type": material_type,
                        "error": f"流水线执行失败: {e}"}

        # 2. 生成器
        gen = cls._generators.get(material_type)
        if gen is not None:
            try:
                if hasattr(gen, "generate"):
                    return gen.generate(topic=topic, subject=subject,
                                        learner_id=learner_id, **kw)
                return gen(topic=topic, subject=subject, learner_id=learner_id, **kw)
            except Exception as e:
                return {"ok": False, "material_type": material_type,
                        "error": f"生成器执行失败: {e}"}

        # 3. 未注册 → 弱模式降级（各 Null 生成器）
        return cls._fallback(material_type, topic, subject, learner_id, **kw)

    @classmethod
    def _fallback(cls, material_type: str, topic: str, subject: str,
                  learner_id: str, **kw) -> Dict[str, Any]:
        """弱模式降级（无宿主/未注册时）。"""
        if material_type == "handout":
            return cls.handout_gen.generate(topic, subject, learner_id, **kw)
        if material_type == "script":
            return cls.script_gen.generate(topic, subject, learner_id, **kw)
        if material_type == "mindmap":
            return cls.mindmap_gen.generate(topic, subject, **kw)
        return {
            "material_type": material_type, "topic": topic, "subject": subject,
            "ok": False,
            "output": f"（物料类型 '{material_type}' 未注册生成器——需注入宿主实现或注册生成器）",
        }
