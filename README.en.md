# paeg-teaching-materials

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-22%2F22-brightgreen.svg)](tests/)

**Teaching materials plugin**: PPT / handout / script / mindmap / video / Manim animation generation. Detachable, independent, installable as an MCP server into any agent.

> [中文](README.md) | **English**

---

## What is it

`paeg-teaching-materials` generates 6 types of teaching materials with a unified execution entry and MCP server.

| Material | Capability |
|---|---|
| **PPT** | Outline (6x6 rule) + optional python-pptx render |
| **Handout** | 6-section structure |
| **Script** | Segmented narration (TTS-ready) |
| **Mindmap** | Hierarchy (3-5 branches) |
| **Video** | Storyboard (8-15s/shot, hook + recap) |
| **Manim** | Math animation code + optional mp4 render |

## Features

- **Extensible registry**: `MaterialRegistry.register("type", generator)`
- **Zero host deps**: 6 Protocols (LLMCallable/RefinerProtocol/HandoutGenerator/ScriptGenerator/MindmapGenerator/ResourceProvider) + Null weak-mode
- **Unified entry**: `execute(name, args)` — JSON contract, never raises
- **MCP server installable**: `pip install` + config declaration = 12 tools
- **Language-quality link**: outputs auto-pass L0 gaffe-fix (paeg-lang-style)
- **Quality check + judge**: deterministic structure check + LLM 5-dim scoring

## Install

```bash
pip install -e /path/to/paeg-teaching-materials
pip install -e "paeg-teaching-materials[pptx]"   # PPT render
pip install -e "paeg-teaching-materials[manim]"  # Manim render
pip install -e "paeg-teaching-materials[mcp]"    # MCP server
```

## Quick Start

```python
from paeg_teaching_materials import MaterialRegistry, execute

def my_llm(system, user, max_tokens=2000, temperature=0.7):
    return call_your_llm(system, user, max_tokens=max_tokens)
MaterialRegistry.inject(llm=my_llm)

result = execute("generate_handout", {"topic": "Quadratic equations", "subject": "Math"})
```

## MCP Server (install like any MCP)

```bash
paeg-teaching-materials-mcp          # console_scripts
python -m paeg_teaching_materials.mcp_server
```

```json
{"mcpServers": {"paeg-teaching-materials": {
  "command": "python",
  "args": ["-m", "paeg_teaching_materials.mcp_server"]
}}}
```

**12 MCP tools**: generate_ppt / generate_handout / generate_script / generate_mindmap / generate_video_script / generate_manim / material_quality_check / material_judge / list_material_types / build_material_prompt / check_language / normalize_material

## Integration Guide

```python
# A. Unified entry
result = execute("generate_ppt", {"topic": "Calculus", "subject": "Math"})

# B. Inject your LLM
MaterialRegistry.inject(llm=my_llm, refiner=my_refiner)

# C. Register custom material type (extensibility)
from paeg_teaching_materials.generators.base import Generator
class QuizGenerator(Generator):
    material_type = "quiz"
    def generate(self, topic, subject="通用", learner_id="anon", **kw): ...
MaterialRegistry.register("quiz", generator=QuizGenerator())

# D. MCP server — zero code bridge
```

## Extensibility

| Extension | How | Mechanism |
|---|---|---|
| Material types | `register("type", generator)` | registry |
| LLM backend | `inject(llm=...)` | Protocol |
| Language refiner | `inject(refiner=...)` | RefinerProtocol |
| Resources | `inject(resources=...)` | ResourceProvider |
| Render backends | pptx/manim extras | optional deps |

## Maintainability

- Zero host deps (stdlib only core)
- JSON contract (never raises)
- Weak-mode (works without host)
- Language L0 link
- 22 tests

## PAEG Integration

```python
from services.material_bridge import install_material_plugin
install_material_plugin()   # inject PAEG LLM/refiner/resources; fallback if absent
```

## License

MIT © 2026 PAEG Team
