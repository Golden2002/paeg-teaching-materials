# CHANGELOG — paeg-teaching-materials（PAEG 工具生态 14.2 教学物料）

## v0.1.1 (2026-08-30) — 独立接入 LLM + 独立前端网页 + GitHub 调研

**更新路径**：src/paeg_teaching_materials/{llm_client.py（新增）, registry.py, generators/*} + web/{web_app.py, index.html}（新增）+ README.md + tests/test_plugin.py

**独立 LLM 接入（环境变量）**
- 新增 llm_client.py：DeepSeek 客户端（OpenAI 兼容，零第三方依赖），`EnvLLM` 实现 LLMCallable 协议
- Key 读取：`DEEPSEEK_API_KEY` 环境变量 → `~/.local/share/opencode/auth.json`（与主项目/词汇表/简历工具同一套约定）
- `MaterialRegistry.llm` 默认改为 `EnvLLM()`——工具独立运行即可调 LLM，宿主仍可 `inject(llm=...)` 覆盖
- 生成器健壮化：无 key 时 LLM 返回空串 → 降级弱模式（不再返回空 success）

**独立前端网页（教学物料工作台）**
- 新增 web/web_app.py（Flask）+ web/index.html：主题/学科 → 选 6 类物料 → 生成 → 质量检查 → 复制/下载
- 端点：`/api/health`（含 LLM 状态）、`/api/materials`、`/api/generate`、`/api/quality`

**GitHub 调研（README 参考文献合集）**
- 调研 PPT/讲义/教学视频/Manim 动画四类共 40+ 仓库，统一收录进 README「参考文献」+「能力提升路线」
- 关键借鉴：python-pptx（PPT 落盘）、edge-tts/whisper/moviepy（视频成片）、makefinks/manim-generator（渲染自动修复闭环）、Poietra/qual（Manim 静态校验）、MoneyPrinterTurbo（端到端视频流水线）

**测试**：74 全绿（弱模式/注入测试适配 EnvLLM 默认值）

## v0.1.0 (2026-08) — 发布

- 6 类物料生成器（PPT/讲义/讲稿/思维导图/教学视频/Manim）+ 网状联通架构（10 功能节点）
- 统一执行入口 execute + MCP server（15 工具 + 2 resources + 2 prompts）
- 零宿主依赖（6 Protocol 抽象 + Null 弱模式）+ 74 项测试
