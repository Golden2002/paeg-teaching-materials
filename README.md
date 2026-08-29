# paeg-teaching-materials

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-74%2F74-brightgreen.svg)](tests/)

<p align="center">
  <strong>paeg-teaching-materials</strong> — 教学物料制作插件：PPT / 讲义 / 讲稿 / 思维导图 / 教学视频 / Manim 数学动画
  <br>
  <em>可拆卸、可独立、可像 MCP server 一样直接安装接入任何智能体。</em>
</p>

> **中文** | [English](README.en.md)

---

## 这是什么

`paeg-teaching-materials` 是**教学物料制作插件**——6 类物料生成器 + 统一执行入口 + MCP server。

| 物料类型 | 能力 | 生成方式 |
|---|---|---|
| **PPT** | 演示文稿大纲（6x6 原则）+ 可选 python-pptx 渲染 | LLM 大纲 → 渲染 |
| **讲义** | 6 段结构（教学目标/导入/新课/巩固/小结/作业） | LLM 生成 markdown |
| **讲稿** | 分段 narration（可 TTS） | LLM 生成 |
| **思维导图** | 中心主题→3-5 分支→2-4 子分支 | LLM 生成缩进列表 |
| **教学视频** | 分镜脚本（8-15s/镜，音画对齐，钩子+recap） | LLM 生成 JSON |
| **Manim 动画** | 数学动画代码 + 可选渲染 mp4 | LLM 代码 → Manim |

源自 PAEG 教育智能体物料系统（v0.87-§3.91 迭代），改造为**零宿主依赖**独立插件。

## 核心特性

- **网状联通架构**（顶尖工具标准 ⭐）：10 个功能节点（查资料/大纲/PPT/讲义/讲稿/思维导图/视频/Manim/学习方法/学习计划）——每个既可独立使用，也是其他功能的前置环节
- **可扩充生成器注册表**：`MaterialRegistry.register("自定义类型", generator)` 即扩展
- **零宿主依赖**：6 个 Protocol 抽象（LLMCallable/RefinerProtocol/HandoutGenerator/ScriptGenerator/MindmapGenerator/ResourceProvider）+ Null 弱模式
- **统一执行入口**：`execute(name, args)` 对标 constraint_engine（JSON 契约，绝不抛异常）
- **MCP server 直接安装**：`pip install` + MCP 配置声明即接入（**20 工具 + 2 resources + 2 prompts** 三原语齐全）
- **语言规范联动**：物料产出自动过 L0 病句修正（复用 paeg-lang-style）
- **质量检查 + 评审**：确定性结构检查 + LLM 5 维评分

## 网状联通架构（功能既可独立，也是前置环节 ⭐）

工具内部是**交织的网状接线与联通**——每个功能是一等公民节点：

```
research（查资料·广播前置）
   ├──→ outline（大纲）──→ ppt（PPT 制作）
   ├──→ script（讲稿）──→ video（教学视频）
   ├──→ handout / manim / method / study_plan / mindmap(可选)
```

**三模式依赖边**：
| 边类型 | 语义 | 例子 |
|---|---|---|
| broadcast（广播） | 源产物被全网消费 | 查资料 → 一切生成 |
| directed（定向） | 强前置 | 大纲→PPT、讲稿→视频 |
| optional（可选） | 缺失时降级 | 资料→思维导图 |

**双暴露**：每个功能既是独立 MCP 工具（`execute_tool`），又可自动编排
（`execute_pipeline` 按依赖图展开前置环节），也可 `|` 链式组合：

```python
from paeg_teaching_materials import MaterialRegistry
from paeg_teaching_materials.tools import ResearchTool, OutlineTool, PptTool

# 1. 独立调用
result = MaterialRegistry.execute_plan("ppt", ctx, {"topic": "导数"})
#   自动执行: research → outline → ppt（查资料是前置环节）

# 2. 链式组合（LangChain Runnable 模式）
pipeline = ResearchTool() | OutlineTool() | PptTool()  # 组合结果仍是 Tool

# 3. 依赖图自省（MCP: list_dependencies）
graph = MaterialRegistry.get_resolver().dependency_graph()
```

**中间产物**（MaterialContext 类型化 Blackboard）：
`resources`（查资料·append 累积）/ `outline` / `lecture_script` / `ppt_outline` /
`completed_stages`（阶段标记·union）——前置环节产物被下游自动消费。

## 安装

```bash
pip install -e /path/to/paeg-teaching-materials
# 可选依赖：
pip install -e "paeg-teaching-materials[pptx]"    # PPT 渲染
pip install -e "paeg-teaching-materials[manim]"   # Manim 渲染
pip install -e "paeg-teaching-materials[mcp]"     # MCP server
```

要求 Python 3.9+。

## 快速开始

```python
from paeg_teaching_materials import MaterialRegistry, execute

# 1. 注入你的 LLM（任何项目接入点）
def my_llm(system, user, max_tokens=2000, temperature=0.7):
    return call_your_llm(system, user, max_tokens=max_tokens)
MaterialRegistry.inject(llm=my_llm)

# 2. 生成物料（统一执行入口）
result = execute("generate_handout", {"topic": "一元二次方程", "subject": "数学"})
# → {"material_type": "handout", "topic": "...", "ok": true, "output": "## 教学目标..."}

# 3. 质量检查 + 评审
from paeg_teaching_materials import check_material_structure, judge_material
issues = check_material_structure(result["output"], "handout")
score = judge_material(result["output"], "一元二次方程")
```

## 以 MCP server 方式接入（像 MCP 一样直接安装即可用）

```bash
# 方式 1：console_scripts 入口（pip install 后）
paeg-teaching-materials-mcp

# 方式 2：python -m 入口（源码运行）
python -m paeg_teaching_materials.mcp_server
```

**MCP 客户端配置声明**（config/mcp_servers.json）：

```json
{
  "mcpServers": {
    "paeg-teaching-materials": {
      "command": "python",
      "args": ["-m", "paeg_teaching_materials.mcp_server"],
      "cwd": "D:/wbo-workspace/paeg_project/paeg-teaching-materials"
    }
  }
}
```

**暴露的 MCP 工具（15 个）**：

| 工具名 | 功能 |
|---|---|
| `generate_ppt` | PPT 大纲生成 |
| `generate_handout` | 讲义生成 |
| `generate_script` | 讲稿生成 |
| `generate_mindmap` | 思维导图生成 |
| `generate_video_script` | 教学视频分镜脚本 |
| `generate_manim` | Manim 数学动画代码 |
| `material_quality_check` | 物料确定性结构检查 |
| `material_judge` | 物料 5 维评审 |
| `list_material_types` | 物料类型自省 |
| `build_material_prompt` | 物料提示词拼装 |
| `check_language` | 语言规范检查 |
| `normalize_material` | 语言规范守门 |
| `execute_tool` | 网状：独立执行功能节点 |
| `execute_pipeline` | 网状：自动编排前置环节 |
| `list_dependencies` | 网状：功能依赖图自省 |

## 可及性（像 Python 库一样 · §3.114）

任何项目/智能体想用本插件，**只需 pip install 一个包**：

```bash
pip install paeg-teaching-materials          # 安装
pip install "paeg-teaching-materials[mcp]"   # 含 MCP server
```

安装后 **import 即自动注册**（6 物料类型 + 规则自动加载），注入自己的 LLM 立即可用：

```python
import paeg_teaching_materials                # import 自动注册
from paeg_teaching_materials import MaterialRegistry, execute
MaterialRegistry.inject(llm=my_llm)           # 注入自己的 LLM
result = execute("generate_handout", {"topic": "力学", "subject": "物理"})
```

- 零宿主依赖（核心 stdlib）
- 干净 venv 实测：pip install → import → 注入 LLM → 立即可用
- MCP server 入口：`paeg-teaching-materials-mcp`（console_scripts）

## 外部项目接入指南

### 场景 A：只用统一执行入口（推荐）

```python
from paeg_teaching_materials import execute
result = execute("generate_ppt", {"topic": "微积分", "subject": "数学"})
```

### 场景 B：注入自己的 LLM（强实现）

```python
from paeg_teaching_materials import MaterialRegistry
MaterialRegistry.inject(llm=my_llm, refiner=my_refiner)
result = MaterialRegistry.generate("handout", "力学", "物理")
```

### 场景 C：注册自定义物料类型（可扩展性）

```python
from paeg_teaching_materials import MaterialRegistry
from paeg_teaching_materials.generators.base import Generator

class QuizGenerator(Generator):
    material_type = "quiz"
    def generate(self, topic, subject="通用", learner_id="anon", **kw):
        return {"material_type": "quiz", "topic": topic, "ok": True, "output": "..."}

MaterialRegistry.register("quiz", generator=QuizGenerator())
# 现在 execute("generate_quiz", {...}) 可用
```

### 场景 D：MCP server（零代码桥）

pip install + MCP 配置声明（见上）——任何 MCP 客户端（Claude/OpenCode/自研）直接调用。

## 可扩展性

| 扩展点 | 方式 | 机制 |
|---|---|---|
| **物料类型** | `MaterialRegistry.register("type", generator)` | 注册表动态扩充 |
| **LLM 后端** | `MaterialRegistry.inject(llm=...)` | Protocol 注入 |
| **语言规范** | `MaterialRegistry.inject(refiner=...)` | RefinerProtocol（缺省复用 paeg-lang-style L0） |
| **资源检索** | `MaterialRegistry.inject(resources=...)` | ResourceProvider |
| **质量评审** | 注入 LLM 后 5 维自动启用 | judge_material |
| **渲染后端** | pptx/manim 可选依赖 | extras_require |

## 可维护性

- **零宿主依赖**：核心包只依赖 stdlib；宿主功能全部 Protocol 注入
- **统一契约**：execute 返回 JSON 字符串（MCP 契约），失败不抛异常
- **弱模式**：无宿主可跑通（Null 生成器占位），便于测试与演示
- **语言规范联动**：物料产出自动过 L0 病句修正
- **74 项测试**：公共 API/弱模式/注入/execute/质量/MCP 全覆盖

## 架构

```
宿主系统（任何 Python 项目 / 智能体）
  MaterialRegistry.inject(llm=..., refiner=..., resources=...)  <- 宿主注入
  execute("generate_handout", {...})                            <- 统一入口
        |
        | 零宿主依赖（Protocol 抽象）
        v
paeg_teaching_materials（独立插件）
  +-------------------+  +-------------------+  +----------------+
  | registry.py       |  | generators/       |  | quality/       |
  | MaterialRegistry  |  | ppt/handout/...   |  | checks/judge   |
  +---------+---------+  +---------+---------+  +----------------+
            |                      |
            v                      v
  +-----------------------------------------------------------+
  | executor.py（execute 统一入口，JSON 契约）                   |
  | mcp_server.py（FastMCP 15 工具，stdio 直接安装）            |
  +-----------------------------------------------------------+
```

## 与 PAEG 主项目集成

PAEG 通过 `services/material_bridge.py` 接入（宿主注入 + 零破坏回退）：

```python
from services.material_bridge import install_material_plugin
install_material_plugin()   # server.py 启动时调用一次
# 注入 PAEG LLM（subagents._safe_chat）+ Refiner（paeg.refiner）+ 资源（library）
# 插件未安装 → 静默回退 PAEG 原物料实现（旧文件永不删除）
```

## 测试

```bash
python -m pytest tests/ -q
# 22 项：公共 API / 弱模式 / 注入 / execute / 质量 / MCP server
```

## 贡献指南

欢迎贡献！
- 新增物料类型：继承 `Generator` 基类 + `MaterialRegistry.register()`
- 新增质量检查：`quality/checks.py` 加函数
- 代码风格：遵循现有模块结构 + 注释规范

## 致谢

- **PAEG 教育智能体**——本插件提取自其物料制作系统（§3.87-§3.100）
- **paeg-lang-style**——语言规范插件（L0 联动）
- **Presenton / ppt-agent-skills**——LLM+渲染管线范式
- **ManimTrainer**——Manim 渲染闭环范式

## 许可证

MIT © 2026 PAEG Team

## 能力提升路线（依据 2026-08 市面 agent/AI 项目调研）

调研了市面 PPT / 讲义 / 教学视频 / Manim 动画制作 agent 与开源项目后，按收益排序的能力补齐清单：

| 优先级 | 能力 | 参考实现 |
|---|---|---|
| 1 | Markdown/大纲 → PPTX 渲染落盘 | python-pptx 引擎 |
| 2 | 模板/主题系统（逐页编辑 + 可编辑导出） | presentation-ai / Slidev / LRriver-AIPPT |
| 3 | 单源多出导出（PPTX/PDF/DOCX/HTML） | pandoc |
| 4 | 讲稿 → TTS 旁白合成（默认 edge-tts，可克隆 F5-TTS/fish-speech） | edge-tts / F5-TTS / fish-speech |
| 5 | ASR 字幕 + 讲稿↔画面时间轴对齐 | whisper |
| 6 | 分镜脚本 → 视频合成（片段+旁白+字幕拼接） | moviepy / MoneyPrinterTurbo |
| 7 | Manim 代码语法/静态校验器（渲染前拦截崩溃） | Poietra/qual |
| 8 | Manim 渲染失败自动修复循环（writer+reviewer 双角色） | makefinks/manim-generator |
| 9 | 逐场景分镜（动画组织成可翻页段落） | manim-slides |
| 10 | grounded 生成 + 素材引用（避免幻觉） | course-builder / learnflow-ai |
| 11 | 交互式 HTML 讲义 / 课程站点 | reveal.js / chiron / mkdocs-material |
| 12 | 质量评测回归基准 | ManiBench 缺陷分类 + LLM-as-judge |

## 参考文献（GitHub 库调研合集）

### A. PPT / 演示文稿制作

| 仓库 | URL | 借鉴点 |
|---|---|---|
| scanny/python-pptx | https://github.com/scanny/python-pptx | PPT 真正落盘的最底层引擎 |
| slidevjs/slidev | https://github.com/slidevjs/slidev | Markdown→演示，内容样式分离 |
| marp-team/marp-cli | https://github.com/marp-team/marp-cli | Markdown 批渲染 HTML/PDF/PPTX |
| hakimel/reveal.js | https://github.com/hakimel/reveal.js | HTML 交互式放映 |
| LRriver/AIPPT | https://github.com/LRriver/AIPPT | AI PPT 工作台，逐页编辑 + 可编辑 PPTX 导出 |
| chenxingqiang/ppt-agents | https://github.com/chenxingqiang/ppt-agents | agent 从 Markdown 生成 PowerPoint |
| allweonedev/presentation-ai | https://github.com/allweonedev/presentation-ai | Gamma 替代，主题/模板系统 |
| jgm/pandoc | https://github.com/jgm/pandoc | 单源多出（pptx/docx/pdf/beamer） |

### B. 讲义 / 教学文档制作

| 仓库 | URL | 借鉴点 |
|---|---|---|
| klausners/course-builder | https://github.com/klausners/course-builder | 研究驱动课程生成，grounded 避免幻觉 |
| raphaelmansuy/course_generator | https://github.com/raphaelmansuy/course_generator | 多步骤 LLM 课程流水线 |
| gyasis/chiron | https://github.com/gyasis/chiron | 输出自包含交互式 HTML 讲义 |
| Bbar0n234/learnflow-ai | https://github.com/Bbar0n234/learnflow-ai | 一套素材 fan-out 成讲义/笔记/课件/幻灯片 |
| docxology/curriculum | https://github.com/docxology/curriculum | 教学大纲生成 + agent 约定 |
| squidfunk/mkdocs-material | https://github.com/squidfunk/mkdocs-material | Markdown→课程站点 |
| X-Lab-Group/teachers-karatuai | https://github.com/X-Lab-Group/teachers-karatuai | 教师备课工具 |
| maccman/101-school | https://github.com/maccman/101-school | 自动课程目录 + 学习路径 |

### C. 教学视频制作

| 仓库 | URL | 借鉴点 |
|---|---|---|
| remotion-dev/remotion | https://github.com/remotion-dev/remotion | React 可编程时间轴→视频 |
| Zulko/moviepy | https://github.com/Zulko/moviepy | 片段+旁白+字幕拼接成片 |
| openai/whisper | https://github.com/openai/whisper | 字幕/ASR + 时间轴对齐 |
| coqui-ai/TTS | https://github.com/coqui-ai/TTS | 本地旁白合成 + 音色微调 |
| rany2/edge-tts | https://github.com/rany2/edge-tts | 零成本中文旁白（默认方案） |
| SWivid/F5-TTS | https://github.com/SWivid/F5-TTS | 零样本音色克隆 |
| fishaudio/fish-speech | https://github.com/fishaudio/fish-speech | SOTA 中文 TTS/克隆 |
| OpenTalker/SadTalker | https://github.com/OpenTalker/SadTalker | 音频驱动数字人 |
| TMElyralab/MuseTalk | https://github.com/TMElyralab/MuseTalk | 实时口型同步 |
| harry0703/MoneyPrinterTurbo | https://github.com/harry0703/MoneyPrinterTurbo | 主题→脚本→素材→配音→字幕→成片全自动 |
| linyqh/NarratoAI | https://github.com/linyqh/NarratoAI | 影视解说自动化 |
| RayVentura/ShortGPT | https://github.com/RayVentura/ShortGPT | 短视频自动化框架 |

### D. Manim 数学动画

| 仓库 | URL | 借鉴点 |
|---|---|---|
| ManimCommunity/manim | https://github.com/ManimCommunity/manim | 数学动画渲染引擎 |
| 3b1b/manim | https://github.com/3b1b/manim | 3Blue1Brown 定制版 manim |
| jeertmans/manim-slides | https://github.com/jeertmans/manim-slides | 动画组织成可翻页教学视频段落 |
| ManimCommunity/manim-voiceover | https://github.com/ManimCommunity/manim-voiceover | 动画 + TTS 音频同步 |
| makefinks/manim-generator | https://github.com/makefinks/manim-generator | 代码编写者+评审者+执行日志反馈自动修复闭环（最关键） |
| Poietra/qual | https://github.com/Poietra/qual | Manim 场景静态分析器，渲染前拦截语法/正确性问题 |
| gqy20/manim-agent | https://github.com/gqy20/manim-agent | LLM Manim 代码生成 agent |
| paulnegz/manim-mcp | https://github.com/paulnegz/manim-mcp | Manim MCP 工具化封装 |
| ken2190/stemviz | https://github.com/ken2190/stemviz | STEM 可视化生成 |
| Alonpenker/math-animate | https://github.com/Alonpenker/math-animate | 数学动画生成器 |
| gqy20/vid-agent | https://github.com/gqy20/vid-agent | 视频生成 agent |
| Bugsbunnydev2000/Math-Animation-Generator | https://github.com/Bugsbunnydev2000/Math-Animation-Generator | 数学动画生成器 |
| 3b1b/videos | https://github.com/3b1b/videos | 3Blue1Brown 视频生成脚本（风格语料） |
| Ding-weiyi/3b_1b_videos | https://github.com/Ding-weiyi/3b_1b_videos | 3b1b 风格复刻 |

### E. 基础标准 / 协议

| 参考 | 网址 | 参考内容 |
|---|---|---|
| Anthropic Skills 规范 | https://github.com/anthropics/skills | Agent Skills 标准格式（SKILL.md） |
| MCP（Model Context Protocol） | https://modelcontextprotocol.io | MCP server 标准化接入 |
| PAEG 主项目 | https://github.com/Golden2002/PAEG | 教学物料制作体系（网状联通架构来源） |

> 说明：ManiBench（数学动画评测基准）为 HuggingFace 数据集 + arXiv 论文（https://arxiv.org/abs/2404.12175），无独立 GitHub 仓库，故未列入上表。
