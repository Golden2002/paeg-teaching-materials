# -*- coding: utf-8 -*-
"""Round-2 真实 DeepSeek LLM 回归：paeg-teaching-materials 6 类物料 + L0 校对。

用法：
    python teach_llm_regression.py

行为：
  1. 校验 llm_client.available()（读 DEEPSEEK_API_KEY / opencode auth.json）
  2. 对 6 类物料（ppt/handout/script/video/mindmap/manim）逐一调用
     MaterialRegistry.generate()（默认 EnvLLM → 真实 DeepSeek）
  3. 对每份 output 跑 apply_language_l0（复用 paeg_lang_style 14.1 gate_short+fix_known_gaffes）
  4. 记录 ok/长度/L0 是否改动；把摘要 JSON 落盘到本脚本所在目录
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SRC = r"D:\wbo-workspace\paeg-teaching-materials\src"
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from paeg_teaching_materials import MaterialRegistry, MATERIAL_TYPES
from paeg_teaching_materials.llm_client import available as llm_available
from paeg_teaching_materials.quality.checks import apply_language_l0

TOPIC = "一元二次方程"
SUBJECT = "数学"

summary = {
    "llm_available": llm_available(),
    "topic": TOPIC,
    "subject": SUBJECT,
    "materials": [],
}

print("=" * 72)
print(f"LLM available: {summary['llm_available']}")
print(f"topic={TOPIC} subject={SUBJECT}")
print("=" * 72)

for mt in MATERIAL_TYPES:
    r = MaterialRegistry.generate(mt, TOPIC, SUBJECT, "round2_regression")
    out = str(r.get("output", ""))
    out_l0 = apply_language_l0(out) if out else ""
    changed = out_l0 != out
    row = {
        "material_type": mt,
        "ok": bool(r.get("ok")),
        "output_len": len(out),
        "l0_changed": changed,
        "error": r.get("error", ""),
        "head": out[:80].replace("\n", "\\n"),
    }
    summary["materials"].append(row)
    flag = "L0-CHANGED" if changed else "l0-same"
    print(f"\n[{mt}] ok={row['ok']} len={row['output_len']} {flag}")
    print(f"  head: {row['head']}")
    if r.get("error"):
        print(f"  error: {r['error'][:120]}")
    if changed:
        print(f"  L0 before: {out[:100]!r}")
        print(f"  L0 after : {out_l0[:100]!r}")

out_json = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "teach_llm_regression.json")
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 72)
print(f"[saved] {out_json}")
print(f"LLM ok count: {sum(1 for m in summary['materials'] if m['ok'])}/{len(MATERIAL_TYPES)}")
print(f"L0 changed count: {sum(1 for m in summary['materials'] if m['l0_changed'])}")
