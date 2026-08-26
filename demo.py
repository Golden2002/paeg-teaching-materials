# -*- coding: utf-8 -*-
"""paeg-teaching-materials 独立运行 demo（无宿主弱模式 + 注入演示）。

用法：
    python demo.py                    # 弱模式（无 LLM）
    python demo.py --inject           # 注入模拟 LLM（强实现）
"""
from __future__ import annotations

import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if os.path.isdir(_SRC) and _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from paeg_teaching_materials import (
    MaterialRegistry, execute, MATERIAL_TYPES,
    check_material_structure, judge_material,
)


def _demo_weak():
    print("=" * 60)
    print("paeg-teaching-materials demo（弱模式——无宿主）")
    print("=" * 60)

    print("\n[1] 物料类型:", ", ".join(MATERIAL_TYPES))

    print("\n[2] 统一执行入口 execute()")
    for name in ("generate_handout", "generate_ppt"):
        r = execute(name, {"topic": "一元二次方程", "subject": "数学"})
        print(f"  {name} -> {r[:100]}...")

    print("\n[3] 质量检查")
    issues = check_material_structure("（待生成占位）内容", "handout")
    print(f"  check_material_structure -> {issues}")

    print("\n[4] 评审（弱模式启发式）")
    score = judge_material("这是一段完整教学物料。" * 100, "主题")
    print(f"  judge_material -> {score['total']} 分（{score['comment']}）")


def _demo_inject():
    print("\n" + "=" * 60)
    print("注入模拟 LLM（强实现演示）")
    print("=" * 60)

    def mock_llm(system, user, max_tokens=2000, temperature=0.7):
        return (
            "## 教学目标\n掌握一元二次方程的解法\n"
            "## 课堂导入\n看一个实际例子\n"
            "## 新课讲授\n（详细内容）\n"
            "## 巩固练习\n（练习题）\n"
            "## 课堂小结\n（小结）\n"
            "## 课后作业\n（作业）"
        )

    MaterialRegistry.inject(llm=mock_llm)
    r = MaterialRegistry.generate("handout", "一元二次方程", "数学")
    print(f"  handout ok={r['ok']}")
    print(f"  输出前 80 字: {r['output'][:80]}...")


if __name__ == "__main__":
    _demo_weak()
    if "--inject" in sys.argv:
        _demo_inject()
