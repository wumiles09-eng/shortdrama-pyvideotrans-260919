#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ocr_srt.py — 短剧硬字幕 OCR 提取器 (免费开源方案: OpenCV + RapidOCR)

从带内嵌(硬)字幕的短剧视频中,周期采样帧 -> 裁剪字幕区域 -> OCR 识别 ->
相邻帧文本去重合并 -> 输出带时间轴的 .srt 字幕文件。

用法:
  uv run ocr_srt.py --input 第01集.mp4 --output 第01集.ocr.srt
  uv run ocr_srt.py --input in.mp4 --region 0.72:0.94 --fps 5 --min-conf 0.6

输出:
  SRT 字幕文件; 同名 .debug.json 记录逐帧 OCR 原始结果便于调参。
"""

import argparse
import difflib
import json
import sys
from pathlib import Path

import cv2
import numpy as np


def parse_args():
    p = argparse.ArgumentParser(description="短剧硬字幕 OCR 提取 -> SRT")
    p.add_argument("--input", required=True, help="输入视频路径")
    p.add_argument("--output", default=None, help="输出 SRT 路径 (默认: 输入名.ocr.srt)")
    p.add_argument("--fps", type=float, default=4.0, help="采样帧率 (默认 4, 即每 0.25s 一帧)")
    p.add_argument("--region", default="auto",
                   help="字幕区域, 高度比例 start:end 或 auto 自动标定 (默认 auto)")
    p.add_argument("--min-conf", type=float, default=0.55, help="OCR 置信度阈值 (默认 0.55)")
    p.add_argument("--min-chars", type=int, default=2, help="单条字幕最少字符数 (默认 2)")
    p.add_argument("--min-dur", type=float, default=0.3, help="单条字幕最短时长秒 (默认 0.3)")
    p.add_argument("--similarity", type=float, default=0.75,
                   help="相邻帧判定为同一字幕的文本相似度 (默认 0.75)")
    p.add_argument("--pad", type=float, default=0.12, help="字幕条首尾时间外扩秒 (默认 0.12)")
    p.add_argument("--debug", action="store_true", help="同时输出逐帧调试 json")
    return p.parse_args()


def fmt_ts(sec: float) -> str:
    sec = max(0.0, sec)
    ms = int(round(sec * 1000))
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def is_chinese_count(t: str, n: int = 2) -> bool:
    return sum(1 for ch in t if '\u4e00' <= ch <= '\u9fff') >= n


def probe_subtitle_band(video: str, ocr, n_probe: int = 16) -> tuple:
    """全图探测若干帧,按文本框 y 中心聚类,选唯一文本数最多的带作为字幕带。

    原理: 对白字幕位置固定且内容不断变化; 水印/角标位置固定但文本几乎不变。
    返回 (y0, y1)。
    """
    cap = cv2.VideoCapture(video)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
    if total <= 0:
        return 0.0, 1.0
    hits = []  # (y_center, text)
    for i in range(n_probe):
        pos = int(total * (i + 0.5) / n_probe)
        cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
        ok, frame = cap.retrieve() if cap.grab() else (False, None)
        if not ok:
            continue
        res, _ = ocr(frame)
        if not res:
            continue
        h = frame.shape[0]
        for box, text, conf in res:
            if conf < 0.6 or not is_chinese_count(text):
                continue
            yc = (box[0][1] + box[2][1]) / 2 / h
            hits.append((yc, text))
    cap.release()
    if not hits:
        return 0.0, 1.0
    # 以 0.05 高度容差聚类
    ys = sorted(y for y, _ in hits)
    clusters = []
    cur = [ys[0]]
    for y in ys[1:]:
        if y - cur[-1] <= 0.06:
            cur.append(y)
        else:
            clusters.append(cur)
            cur = [y]
    clusters.append(cur)
    best, best_unique = None, -1
    for c in clusters:
        texts = {t for y, t in hits if c[0] - 0.03 <= y <= c[-1] + 0.03}
        if len(texts) > best_unique:
            best_unique = len(texts)
            best = c
    if best is None:
        return 0.0, 1.0
    y0, y1 = max(0.0, best[0] - 0.06), min(1.0, best[-1] + 0.06)
    print(f"[ocr_srt] 自动标定字幕带 y={y0:.2f}:{y1:.2f} (唯一文本 {best_unique} 条, 命中 {len(hits)})", file=sys.stderr)
    return y0, y1


def clean_text(t: str) -> str:
    # 去掉 OCR 常见噪声字符与空白
    for ch in " \u3000\t|":
        t = t.replace(ch, "")
    return t.strip(" 。.,，·、:：")


def similar(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def ocr_frames(video: str, y0: float, y1: float, fps: float, ocr):
    """顺序读视频,按目标帧率采样,返回 [(t_sec, text, conf), ...]。"""
    cap = cv2.VideoCapture(video)
    if not cap.isOpened():
        raise SystemExit(f"无法打开视频: {video}")
    vfps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    step = max(1, int(round(vfps / fps)))  # 每 step 帧取一帧
    idx = 0
    results = []
    while True:
        ok = cap.grab()
        if not ok:
            break
        if idx % step == 0:
            ok, frame = cap.retrieve()
            if not ok:
                break
            t = idx / vfps
            h = frame.shape[0]
            crop = frame[int(h * y0): int(h * y1), :]
            # 放大 2 倍提升小字识别率 (保持彩色, RapidOCR 内部自行处理)
            crop = cv2.resize(crop, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
            ocr_res, _ = ocr(crop)
            text, conf = "", 0.0
            if ocr_res:
                # 字幕可能被识别成多段,拼接; 取平均置信度
                parts = [it[1] for it in ocr_res]
                text = "".join(parts)
                conf = sum(float(it[2]) for it in ocr_res) / len(ocr_res)
            results.append((t, clean_text(text), conf))
        idx += 1
    cap.release()
    return results


def merge_segments(frames, min_conf, min_chars, similarity, min_dur, pad):
    """把逐帧 OCR 结果合并为字幕段。"""
    segs = []
    cur = None  # [text, start, end]

    def close(seg):
        if seg and seg[0] and (seg[2] - seg[1]) >= min_dur:
            segs.append(tuple(seg))

    for t, text, conf in frames:
        if not text or conf < min_conf or len(text) < min_chars:
            # 空帧: 允许短暂闪烁, 超过 1.5*采样间隔才断开
            if cur and t - cur[2] > 0.5:
                close(cur)
                cur = None
            continue
        if cur is None:
            cur = [text, t, t]
        elif similar(cur[0], text) >= similarity:
            cur[2] = t
            # 用最新文本兜底 (长字幕滚动补全场景)
            if len(text) > len(cur[0]):
                cur[0] = text
        else:
            close(cur)
            cur = [text, t, t]
    close(cur)

    # 去掉被更长字幕完全覆盖的碎片 (相似且时间重叠)
    dedup = []
    for seg in segs:
        overlap = False
        for i, kept in enumerate(dedup):
            ov = min(seg[2], kept[2]) - max(seg[1], kept[1])
            if ov > 0 and similar(seg[0], kept[0]) >= similarity:
                if len(seg[0]) > len(kept[0]):
                    dedup[i] = seg
                overlap = True
                break
        if not overlap:
            dedup.append(seg)

    # 首尾外扩, 更贴近真实字幕出现时间
    return [(txt, max(0.0, s - pad), e + pad) for txt, s, e in dedup]


def write_srt(path: str, segs):
    lines = []
    for i, (txt, s, e) in enumerate(segs, 1):
        lines.append(f"{i}\n{fmt_ts(s)} --> {fmt_ts(e)}\n{txt}\n")
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main():
    args = parse_args()
    inp = Path(args.input)
    if not inp.exists():
        raise SystemExit(f"文件不存在: {inp}")
    out = args.output or str(inp.with_suffix(".ocr.srt"))

    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR()

    if str(args.region).lower() == "auto":
        y0, y1 = probe_subtitle_band(str(inp), ocr)
    else:
        y0, y1 = (float(x) for x in args.region.split(":"))
    print(f"[ocr_srt] {inp.name} region={args.region} fps={args.fps}", file=sys.stderr)
    frames = ocr_frames(str(inp), y0, y1, args.fps, ocr)
    print(f"[ocr_srt] 采样 {len(frames)} 帧, 非空 {sum(1 for _,t,_ in frames if t)}", file=sys.stderr)

    if args.debug:
        dbg = out + ".debug.json"
        Path(dbg).write_text(json.dumps(
            [{"t": round(t, 3), "text": t2, "conf": round(c, 3)} for t, t2, c in frames],
            ensure_ascii=False, indent=1), encoding="utf-8")

    segs = merge_segments(frames, args.min_conf, args.min_chars, args.similarity, args.min_dur, args.pad)
    write_srt(out, segs)
    print(f"[ocr_srt] 输出 {len(segs)} 条字幕 -> {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
