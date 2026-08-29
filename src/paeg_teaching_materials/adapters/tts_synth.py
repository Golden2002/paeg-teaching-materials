# -*- coding: utf-8 -*-
"""讲稿旁白 TTS 落盘（edge-tts）——synthesize_script_audio。

移植自主项目 `video_service._tts_to_file`（v0.45），剥离宿主视频管线，
保留核心：edge-tts 合成中文旁白 mp3（默认 zh-CN-XiaoxiaoNeural，略慢速适合教学）。

依赖：edge-tts（可选）。未安装 / 合成失败时抛 RuntimeError，由上层生成器
捕获并优雅降级（返回提示而非崩溃）。
"""

from __future__ import annotations

import asyncio
import os
import re

from ._paths import default_out_dir, safe_stem

DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"


def to_speakable(text: str) -> str:
    """把 markdown 讲稿转成适合朗读的纯文本（去标题号/加粗/表格/列表符号）。"""
    if not text:
        return ""
    t = str(text)
    # 表格分隔行（|---|）整行剔除
    t = re.sub(r"^\s*\|[\s\-:|]+\|\s*$", "", t, flags=re.M)
    # 表格单元格分隔符 → 逗号
    t = t.replace("|", "，")
    # 标题号 / 加粗 / 行内代码 / 链接
    t = re.sub(r"^#{1,6}\s*", "", t, flags=re.M)
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t, flags=re.S)
    t = re.sub(r"\*(.+?)\*", r"\1", t, flags=re.S)
    t = re.sub(r"`([^`]*)`", r"\1", t)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    # 列表符号 → 停顿
    t = re.sub(r"^\s*[-*•]\s+", "", t, flags=re.M)
    t = re.sub(r"^\s*\d+[.、)]\s*", "", t, flags=re.M)
    # 压缩多余空行
    t = re.sub(r"\n{2,}", "\n", t).strip()
    return t


def synthesize_script_audio(text: str, topic: str = "", out_dir=None,
                            voice: str = DEFAULT_VOICE, rate: str = "-5%") -> str:
    """把讲稿文本合成为 mp3 旁白，返回绝对路径。

    Args:
        text: 讲稿 markdown 全文。
        topic: 主题（用于文件名）。
        out_dir: 输出目录（默认 <plugin_root>/render_output/tts/）。
        voice: edge-tts 音色。
        rate: 语速（教学场景默认 -5% 略慢）。

    Returns:
        str: mp3 绝对路径。

    Raises:
        RuntimeError: edge-tts 未安装 / 合成失败 / 无有效音频。
    """
    try:
        import edge_tts
    except Exception as e:
        raise RuntimeError(f"edge-tts 未安装（pip install edge-tts）: {e}")

    speakable = to_speakable(text)
    if not speakable:
        raise RuntimeError("讲稿内容为空，无法合成旁白")

    out_dir = out_dir or default_out_dir("tts")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, safe_stem(topic, maxlen=40) + ".mp3")

    async def _synth():
        comm = edge_tts.Communicate(speakable[:1500], voice, rate=rate)
        await comm.save(path)

    # 网络抖动重试（edge-tts 走网络流式下载，偶发连接中断）
    last_err = ""
    for attempt in range(3):
        try:
            asyncio.run(_synth())
        except Exception as e:
            last_err = str(e)
        if os.path.isfile(path) and os.path.getsize(path) > 0:
            return os.path.abspath(path)
        # 失败后清掉残留的 0 字节文件再重试
        try:
            if os.path.isfile(path):
                os.remove(path)
        except Exception:
            pass
        if attempt < 2:
            import time
            time.sleep(1.0)

    if last_err:
        raise RuntimeError(f"TTS 合成失败: {last_err[:200]}")
    raise RuntimeError("TTS 合成未产生有效音频文件")
