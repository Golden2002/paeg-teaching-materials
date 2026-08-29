# -*- coding: utf-8 -*-
"""adapters._paths — 输出目录与安全文件名的共享工具（零依赖）。"""

from __future__ import annotations

import os
import re

# adapters/_paths.py 的上级两级 = paeg_teaching_materials 包；再上一级 = src；再上一级 = 插件根
_PKG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ROOT = os.path.dirname(os.path.dirname(_PKG_DIR))

_INVALID = re.compile(r'[\\/:*?"<>|\s]+')


def plugin_root() -> str:
    """插件根目录（pyproject.toml 所在）。"""
    return _ROOT


def default_out_dir(kind: str) -> str:
    """默认输出目录 <plugin_root>/downloads/<kind>/（与主项目 downloads/ 约定一致，且已被 .gitignore 忽略）。"""
    d = os.path.join(_ROOT, "downloads", kind)
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    return d


def safe_stem(text, maxlen: int = 48) -> str:
    """主题 → 文件系统安全前缀（去非法字符/空白）。"""
    s = _INVALID.sub("_", str(text or "material"))
    s = re.sub(r"_+", "_", s).strip("_")
    return s[:maxlen] or "material"
