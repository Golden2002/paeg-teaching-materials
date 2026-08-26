# -*- coding: utf-8 -*-
"""paeg_teaching_materials.core.edges — 依赖边（三模式 ⭐）。

网状联通架构（Oracle §3.110）：功能间的前置关系通过依赖边表达。

三类边：
- broadcast（广播边）：源产物被全网多消费者并行读取（查资料 → 一切生成）
- directed（定向边）：强一对一前置（大纲 → PPT、讲稿 → 视频）
- optional（可选边）：缺失时降级而非报错（资料 → 思维导图）
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Dependency:
    """一条前置依赖边：source 工具的产物（field）被本工具消费。"""

    source: str                              # 源工具名
    field: str                               # MaterialContext 字段名
    mode: Literal["broadcast", "directed", "optional"] = "directed"

    def __repr__(self) -> str:
        return f"<{self.source}.{self.field} [{self.mode}]>"


# 便捷构造器
def broadcast(source: str, field: str) -> Dependency:
    """广播边：source 产物被全网消费（一对多）。"""
    return Dependency(source, field, mode="broadcast")


def directed(source: str, field: str) -> Dependency:
    """定向边：强前置（一对一）。"""
    return Dependency(source, field, mode="directed")


def optional(source: str, field: str) -> Dependency:
    """可选边：缺失时降级。"""
    return Dependency(source, field, mode="optional")
