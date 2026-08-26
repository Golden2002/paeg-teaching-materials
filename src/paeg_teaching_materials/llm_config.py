# -*- coding: utf-8 -*-
"""paeg_teaching_materials.llm_config — 模型配置外置（§3.111 ⭐ R4 用户修正）。

用户要求：
1. **当前统一接入同一个模型**（不接多模型）
2. **保留接入不同模型的能力**（路由能力在，默认同一模型）
3. **模型配置外置**（便于扩展，不写死内部）

配置外置：data/llm_config.json（或环境变量 PAEG_LLM_CONFIG 覆盖）。
默认 profile="default" → 使用注入的 LLM（MaterialRegistry.llm，统一同模型）。
未来接专用模型：配置加一条 profile 即可，不改代码。
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "data", "llm_config.json")
_ENV_CONFIG = os.environ.get("PAEG_LLM_CONFIG", "")


def _load_config() -> Dict[str, Any]:
    path = _ENV_CONFIG or _CONFIG_PATH
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {
        "default_profile": "default",
        "profiles": {
            "default": {"note": "统一使用注入的 LLM（MaterialRegistry.llm，同主项目模型）"},
        },
    }


def get_llm_config(profile: Optional[str] = None) -> Dict[str, Any]:
    cfg = _load_config()
    profile = profile or cfg.get("default_profile", "default")
    return cfg.get("profiles", {}).get(profile, cfg.get("profiles", {}).get("default", {}))


def available_profiles() -> list:
    return list(_load_config().get("profiles", {}).keys())


def config_path() -> str:
    return _ENV_CONFIG or _CONFIG_PATH
