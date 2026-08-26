# -*- coding: utf-8 -*-
"""paeg_teaching_materials.generators.base — 生成器基类（Oracle R1）。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class Generator(ABC):
    """物料生成器抽象基类。所有生成器实现统一接口。"""

    material_type: str = "generic"

    @abstractmethod
    def generate(self, topic: str, subject: str = "通用",
                 learner_id: str = "anon", **kw) -> Dict[str, Any]:
        """生成物料。返回 dict（material_type/topic/output/ok）。"""
        ...

    def __call__(self, topic: str, subject: str = "通用",
                 learner_id: str = "anon", **kw) -> Dict[str, Any]:
        return self.generate(topic, subject, learner_id, **kw)
