# -*- coding: utf-8 -*-
"""Manim 真实渲染落盘（隔离子进程）——render_manim_code。

移植自主项目 `manim_service.render_manim`（v6.1），剥离宿主的隔离 venv /
MiKTeX 路径耦合，改为自动探测系统 manim：
- 优先 `manim`（PATH），其次 `python -m manim`
- 无 LaTeX 时 MathTex/Tex → Text 降级（避免 latex.exe FileNotFound）
- 全角标点 / markdown 代码块外壳 / $ 残留自动清洗（复用 manim_quality.clean_manim_code）
- subprocess 超时 + 错误 tail 回传（供 RITL 修复回路使用）

依赖：manim（可选 extras "manim"）+ ffmpeg。未安装时优雅降级：
`manim_available()` 返回 False；`render_manim_code` 抛 RuntimeError（含提示），
由上层生成器捕获并返回「渲染环境不可用」提示，绝不中断主流程。
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import uuid
from typing import List, Optional, Tuple

from ._paths import default_out_dir, safe_stem
from ..manim_quality import clean_manim_code

# 安全校验：禁用的 import / 调用（防恶意代码——与主项目一致）
_BLOCKED_IMPORTS = {"os", "sys", "subprocess", "socket", "shutil", "ctypes",
                    "multiprocessing", "signal", "importlib", "pathlib", "requests"}
_BLOCKED_CALLS = {"eval", "exec", "__import__", "compile", "globals", "locals",
                  "open", "getattr", "setattr", "delattr"}


def manim_available() -> bool:
    """检测系统是否有可用的 manim 命令。"""
    return _find_manim() is not None


def _find_manim() -> Optional[List[str]]:
    """定位 manim 启动命令：优先 PATH 中的 `manim`，其次 `python -m manim`。"""
    exe = shutil.which("manim")
    if exe:
        return [exe]
    # 回退 python -m manim（需当前解释器装了 manim 包）
    try:
        import importlib.util
        if importlib.util.find_spec("manim") is not None:
            import sys
            return [sys.executable, "-m", "manim"]
    except Exception:
        pass
    return None


def _latex_available() -> bool:
    """检测 LaTeX 可用性（MathTex/Tex 渲染依赖）。"""
    try:
        if shutil.which("latex") is not None or shutil.which("latex.exe") is not None:
            return True
    except Exception:
        pass
    return False


def _sanitize_no_latex(code: str) -> str:
    """无 LaTeX 环境时把 MathTex/Tex 降级为 Text。"""
    if _latex_available():
        return code
    return code.replace("MathTex(", "Text(").replace("Tex(", "Text(")


def _find_renderable_scene(code: str) -> str:
    """找含 construct 的 Scene 子类（跳过无 construct 的基类）。"""
    import ast as _ast
    try:
        tree = _ast.parse(code)
    except Exception:
        m = re.search(r"class\s+(\w+)\s*\(", code)
        return m.group(1) if m else "Scene"
    class_info = {}
    scene_names = {"Scene", "ThreeDScene", "MovingCameraScene", "ZoomedScene"}
    for node in _ast.walk(tree):
        if isinstance(node, _ast.ClassDef):
            bases = []
            for b in node.bases:
                if isinstance(b, _ast.Name):
                    bases.append(b.id)
                elif isinstance(b, _ast.Attribute):
                    bases.append(b.attr)
            has_construct = any(
                isinstance(i, _ast.FunctionDef) and i.name == "construct"
                for i in node.body)
            class_info[node.name] = {"bases": bases, "construct": has_construct}
    for name, info in class_info.items():
        if any(b in scene_names for b in info["bases"]) and info["construct"]:
            return name
    for name, info in class_info.items():
        if info["construct"]:
            chain = set()
            stack = list(info["bases"])
            while stack:
                b = stack.pop()
                if b in scene_names:
                    chain.add(b)
                elif b in class_info:
                    stack.extend(class_info[b]["bases"])
            if chain:
                return name
    m = re.search(r"class\s+(\w+)\s*\(", code)
    return m.group(1) if m else "Scene"


def _validate_manim_code(code: str) -> Tuple[bool, str]:
    """AST 校验：拒绝危险 import/调用，必须有 Scene 子类 + construct。"""
    import ast as _ast
    try:
        tree = _ast.parse(code)
    except SyntaxError as e:
        return False, f"SyntaxError: {e}"
    has_scene = False
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Import):
            for a in node.names:
                if a.name.split(".")[0] in _BLOCKED_IMPORTS:
                    return False, f"Blocked import: {a.name}"
        if isinstance(node, _ast.ImportFrom):
            if node.module and node.module.split(".")[0] in _BLOCKED_IMPORTS:
                return False, f"Blocked import: {node.module}"
        if isinstance(node, _ast.Call) and isinstance(node.func, _ast.Name):
            if node.func.id in _BLOCKED_CALLS:
                return False, f"Blocked call: {node.func.id}"
        if isinstance(node, _ast.ClassDef):
            for base in node.bases:
                if isinstance(base, _ast.Name) and base.id in ("Scene", "ThreeDScene"):
                    has_scene = True
                    has_construct = any(
                        isinstance(i, _ast.FunctionDef) and i.name == "construct"
                        for i in node.body)
                    if not has_construct:
                        return False, "Scene missing construct()"
    if not has_scene:
        return False, "No Scene class found"
    return True, ""


def save_manim_code(code: str, topic: str, out_dir=None) -> str:
    """清洗并落盘 Manim 代码为 .py（不依赖 manim，永远可执行）。"""
    out_dir = out_dir or default_out_dir("manim")
    os.makedirs(out_dir, exist_ok=True)
    clean = clean_manim_code(code)
    fname = safe_stem(topic, maxlen=40) + ".py"
    path = os.path.join(out_dir, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(clean if clean.strip() else str(code))
    return os.path.abspath(path)


def render_manim_code(code: str, topic: str, out_dir=None,
                      quality: str = "-ql", timeout: int = 300) -> str:
    """渲染 Manim 代码 → mp4 路径。成功返回 mp4 绝对路径，失败抛 RuntimeError。

    每次渲染前先把清洗后的代码落盘为 .py（保证即使渲染失败也有代码产物）。
    依赖缺失（manim 未安装）时抛 RuntimeError("MANIM_UNAVAILABLE: ...")。
    """
    code_path = save_manim_code(code, topic, out_dir=out_dir)

    manim_cmd = _find_manim()
    if manim_cmd is None:
        raise RuntimeError(
            f"MANIM_UNAVAILABLE: manim 未安装（pip install manim；已保存代码: {code_path}）")

    code = clean_manim_code(code)
    ok, err = _validate_manim_code(code)
    if not ok:
        raise RuntimeError(f"代码校验失败: {err}（代码已保存: {code_path}）")

    code = _sanitize_no_latex(code)
    # 重新写回降级后的代码（MathTex→Text）
    with open(code_path, "w", encoding="utf-8") as f:
        f.write(code)

    media_dir = os.path.join(out_dir or default_out_dir("manim"), "jobs",
                             str(uuid.uuid4())[:8])
    os.makedirs(media_dir, exist_ok=True)
    scene_class = _find_renderable_scene(code)
    cmd = manim_cmd + ["render", quality, "--media_dir", media_dir,
                       code_path, scene_class]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                encoding="utf-8", errors="replace",
                                cwd=media_dir, timeout=timeout, shell=False)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"渲染超时（{timeout}s）: {code_path}")
    except FileNotFoundError:
        raise RuntimeError(f"MANIM_UNAVAILABLE: 渲染命令不可用: {manim_cmd[0]}")
    except Exception as e:
        raise RuntimeError(f"渲染进程异常: {e}")

    if result.returncode != 0:
        tail = "\n".join((result.stderr or "").splitlines()[-15:])
        raise RuntimeError(f"渲染失败: {tail[:800]}")

    # 定位输出：-ql/-qm/-qh/-qk 对应不同分辨率目录
    for q in ("480p15", "720p30", "1080p60", "1440p60", "2160p60"):
        cand = os.path.join(media_dir, "videos",
                            os.path.splitext(os.path.basename(code_path))[0],
                            q, f"{scene_class}.mp4")
        if os.path.exists(cand):
            return os.path.abspath(cand)
    raise RuntimeError("渲染完成但未找到输出 mp4（Video file not found）")
