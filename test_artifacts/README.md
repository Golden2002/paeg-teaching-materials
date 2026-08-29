# test_artifacts — 教学物料制作工具 · 测试产物

本目录是 `paeg-teaching-materials` 的**真实测试产物**：6 类物料生成器在接入环境变量
DeepSeek LLM 后，以真实主题（`一元二次方程` / `细胞呼吸`）逐一生成并落盘。

生成时间：2026-08-30 · 工具版本 v0.1.1（含真实渲染适配器）。

---

## 产物清单

| 物料类型 | 文件 | 说明 | 结构检查 |
|---|---|---|---|
| 讲义 | `讲义_一元二次方程.md` | 6 段结构（目标/导入/新课/巩固/小结/作业） | ✅ 通过 |
| PPT 大纲 | `PPT大纲_一元二次方程.md` | 6x6 原则 + 封面/内容/结尾 | ✅ 无占位残留 |
| PPT 渲染 | `一元二次方程.pptx` | python-pptx 真实落盘（42 KB，可打开） | ✅ 真实 .pptx |
| 讲稿 | `讲稿_细胞呼吸.md` | 分段 narration（开场/分节/小结收尾） | ⚠️ 见下注 |
| 讲稿 TTS | `旁白_细胞呼吸.mp3` | edge-tts 合成（1.8 MB，zh-CN-XiaoxiaoNeural） | ✅ 真实 mp3 |
| 思维导图 | `思维导图_细胞呼吸.md` | 中心主题 → 分支 → 子分支 | ✅ 通过 |
| 视频分镜 | `视频分镜_一元二次方程.json` | 8 镜 JSON（8-15s/镜，音画对齐，钩子+recap） | ✅ 合法 JSON |
| Manim 代码 | `Manim_一元二次方程.py` | 可渲染 Scene（含 construct） | ✅ lint 0 问题 / MVQS PASS |
| Manim 渲染 | `一元二次方程_数学动画.mp4` | ManimCE v0.19.0 真实渲染（h264 1280x720@30fps，20.67s） | ✅ 真实 mp4 |

`manifest.json` 记录了每个产物的 `kind / file / bytes / quality_issues`。

---

## 说明

1. **Manim 渲染 mp4 已产出（Round 4）**：本机 Python 3.14 下 `pip install manim`
   失败于 `moderngl / glcontext` 的 MSVC 构建要求（无 cp314 预编译轮子），但主项目
   `manim_env` 自带隔离 venv（Python 3.9.13 + ManimCE v0.19.0 + moderngl 5.12 +
   MiKTeX + ffmpeg）。把该 venv 的 `Scripts`（`manim.exe`/`ffmpeg.exe`）与 MiKTeX
   `bin\x64`（`latex.exe`）加入 `PATH` 后，`manim -qm Manim_一元二次方程.py
   QuadraticEquation` 成功产出 `一元二次方程_数学动画.mp4`（h264 1280x720@30fps，
   时长 20.67s）。工具自身 `render_manim_code()` 亦复验通过：`manim_available()=True`
   → 自动落盘清洗后 `.py` → `manim render -ql --media_dir <jobs/uuid>` → 返回 mp4 绝对
   路径（480p15 259805 B）。在无 manim 的环境里工具仍**优雅降级**：保存清洗后的
   `.py` 并在结果里返回 `render_skip` 提示，而非崩溃。

2. **讲稿结构检查的 1 条提示**：确定性检查器 `check_material_structure` 要求出现字面
   关键词「结束」，而 LLM 生成的讲稿用「小结收尾 / 总结 / 下节课再见」收尾（内容完整、
   有收尾）。属检查器启发式限制，非内容缺陷。

3. **PPT / 视频 / Manim 的「结构检查」**：`check_material_structure` 对这三类只做
   通用「占位残留」检测（讲义 6 段 / 讲稿开场小结 / 思维导图层级是类型专属检查），
   因此 `quality_issues` 为空即表示无占位残留、内容完整。

4. **LLM 接入**：所有产物由环境变量 DeepSeek LLM（`DEEPSEEK_API_KEY` 或
   `~/.local/share/opencode/auth.json`）生成，未注入任何 mock。

---

## Round 2 · 真实 DeepSeek LLM 回归（2026-08-30）

复跑 6 类物料生成器（`MaterialRegistry.generate` + 默认 `EnvLLM` → 真实 DeepSeek，
主题 `一元二次方程`），验证 LLM 路径 + L0 校对接线仍全通。摘要见
`teach_llm_regression.json`：

| 物料类型 | ok | 输出长度 | L0 校对 | 说明 |
|---|---|---|---|---|
| ppt | ✅ | 805 | 已跑 `apply_language_l0` | 大纲 6x6 + 封面/内容/结尾 |
| handout | ✅ | 3447 | 已跑 `apply_language_l0` | 6 段结构完整 |
| script | ✅ | 2724 | 已跑 `apply_language_l0` | 开场/分节/小结 |
| video | ✅ | 1171 | 已跑 `apply_language_l0` | 8 镜 JSON 分镜 |
| mindmap | ✅ | 500 | 已跑 `apply_language_l0` | 层级缩进完整 |
| manim | ✅ | 1997 | 已跑 `apply_language_l0` | Scene 含 construct |

**结论**：`llm_available=True`，6/6 全 ok（无弱模式占位）。每份输出均经
`apply_language_l0`（复用 `paeg_lang_style` 14.1 的 `gate_short` + `fix_known_gaffes`）
校对后落盘——LLM 生成文本本身无已知病句，故 L0 为「零改动安全网」；L0 的确定性修正
能力（`我在这里听着你。` → `我就在这里听你说说。`）与优雅降级由 14.1 的
`14_生态联通_L0校对验证.md` 独立验证。

> **Round 3 · 可复现脚本**：`teach_llm_regression.py` 已纳入本目录（从 `paeg_scratch`
> 迁移），运行 `python teach_llm_regression.py` 即重新跑 6 类物料真实 LLM 回归并覆写
> `teach_llm_regression.json`（需 DeepSeek key；约 2-4 分钟）。

---

## Round 8 · 第二主题「视频分镜 → Manim → mp4」闭环（2026-08-31）

承接 Round 4 已打通的一元二次方程闭环，本轮把「视频分镜 → Manim 代码 → mp4」扩展到
**第二主题「细胞呼吸」**，形成可复用的双主题动画证据。复用主项目 `manim_env` 隔离
venv（`manim.exe` + `ffmpeg.exe`）+ MiKTeX portable（`latex.exe`，位于
`miktex\texmfs\install\miktex\bin\x64`），本轮新增：

| 产物 | 文件 | 说明 |
|---|---|---|
| 视频分镜 | `视频分镜_细胞呼吸.json` | 8 镜 JSON（8-15s/镜，钩子→总方程式→三车间→三阶段→无氧→收尾，音画对齐 `讲稿_细胞呼吸.md`） |
| Manim 代码 | `Manim_细胞呼吸.py` | 单 Scene 44 个动画，中文标签显式指定 `font="Microsoft YaHei"`（避免默认字体豆腐块），化学式走 `MathTex`（LaTeX） |
| Manim 渲染 | `细胞呼吸_教学动画.mp4` | ManimCE v0.19.0 真实渲染，h264 **1920×1080@60fps**（`-qh`），时长 **43.50s**（2.09 MB） |

**质量核验**：

- `lint_manim_code`（12 崩溃模式静态检测）→ **0 问题**；`mvqs_score` → **PASS（0.87）**。
- 分镜 JSON 合法、8 镜齐全、与讲稿段落一一对应。
- 中文渲染修复：本轮排查到 Manim `Text` 默认字体不含 CJK，中文会渲染成豆腐块，
  通过 `manimpango.list_fonts()` 确认系统含 `Microsoft YaHei`，改为显式
  `font="Microsoft YaHei"`（并用 ffmpeg 抽帧 + 时长/码流复核 mp4 有效性）。
- 低清 `-ql` 先行排错（43.60s/854×480@15fps 验证 Scene 无崩溃）后再 `-qh` 出高清。

**渲染命令（复现）**：

```powershell
$env_root = "D:\桌面\智能体架构与开发（含大模型）\14_教育者Agent项目\manim_env"
$env:PATH = "$env_root\venv\Scripts;$env_root\miktex\texmfs\install\miktex\bin\x64;$env:PATH"
manim -qh --disable_caching Manim_细胞呼吸.py CellularRespiration
```

至此 6 类物料 + 两个主题的 Manim 动画（一元二次方程 720p + 细胞呼吸 1080p60）全部
真实落盘，`视频分镜 → Manim → mp4` 闭环覆盖两个主题，可复用。
