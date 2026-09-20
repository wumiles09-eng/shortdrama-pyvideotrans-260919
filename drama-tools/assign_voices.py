#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
assign_voices.py — 按说话人分配多音色 (7 语种; 支持原声性别自动识别)

读取 pyvideotrans 说话人分离结果 speaker.json (每行字幕的说话人 id 列表),
将每个说话人映射到 Edge-TTS 音色, 生成 line_roles {行号: 音色} 写入 params.json。

三种分配方式 (优先级 --map > --voices > --lang > --lang+--vocal):
  --lang es                      按语种池顺序 (交替)
  --lang es --vocal vocal.wav    【推荐】用分离出的原声计算每个说话人基频,
                                 女(>170Hz)→女声 男(≤170Hz)→男声 (真正的"音色识别")
  --voices "a,b,c"               显式序列
  --map "spk0=x,spk1=y"          显式映射
"""

import argparse
import json
import re
import subprocess
from pathlib import Path

import numpy as np

# Edge-TTS 音色池 (2026-09-19 逐名校验); 每语种 {f:[女...], m:[男...]}
VOICE_POOLS = {
    "en": {"f": ["en-US-AriaNeural", "en-US-JennyNeural", "en-US-EmmaNeural"],
           "m": ["en-US-BrianNeural", "en-US-GuyNeural", "en-US-AndrewNeural"]},
    "es": {"f": ["es-ES-ElviraNeural", "es-MX-DaliaNeural"],
           "m": ["es-ES-AlvaroNeural", "es-MX-JorgeNeural"]},
    "pt": {"f": ["pt-BR-FranciscaNeural", "pt-PT-FernandaNeural"],
           "m": ["pt-BR-AntonioNeural", "pt-PT-DuarteNeural"]},
    "fr": {"f": ["fr-FR-DeniseNeural", "fr-CA-SylvieNeural"],
           "m": ["fr-FR-HenriNeural", "fr-CA-AntoineNeural"]},
    "de": {"f": ["de-DE-KatjaNeural", "de-DE-AmalaNeural"],
           "m": ["de-DE-ConradNeural", "de-DE-KillianNeural"]},
    "id": {"f": ["id-ID-GadisNeural"], "m": ["id-ID-ArdiNeural"]},
    "it": {"f": ["it-IT-ElsaNeural", "it-IT-FabiolaNeural"],
           "m": ["it-IT-DiegoNeural"]},
    "zh": {"f": ["zh-CN-XiaoxiaoNeural", "zh-CN-XiaoyiNeural"],
           "m": ["zh-CN-YunxiNeural", "zh-CN-YunjianNeural"]},
}

F0_FEMALE_MIN = 170  # Hz: 中位数高于此判女声


def parse_args():
    p = argparse.ArgumentParser(description="说话人 -> 多音色分配 (7语种, 支持原声性别识别)")
    p.add_argument("--speaker-json", required=True)
    p.add_argument("--params-json", required=True)
    p.add_argument("--lang", default=None, choices=list(VOICE_POOLS))
    p.add_argument("--vocal", default=None,
                   help="分离出的原声 vocal.wav 路径; 配合 --lang 按基频自动判性别")
    p.add_argument("--srt", default=None,
                   help="源语 srt (行时间轴需与 speaker.json 对齐), --vocal 时必填")
    p.add_argument("--voices", default=None)
    p.add_argument("--map", default=None)
    return p.parse_args()


def seg_f0(audio, t0, t1):
    out = subprocess.run(['ffmpeg', '-v', 'quiet', '-ss', str(max(0.0, t0)), '-to', str(t1),
                          '-i', audio, '-f', 'f32le', '-ac', '1', '-ar', '16000', '-'],
                         capture_output=True)
    x = np.frombuffer(out.stdout, dtype=np.float32)
    if len(x) < 8000:
        return None
    x = x[int(0.1 * 16000):int(-0.1 * 16000)]
    spec = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    freqs = np.fft.rfftfreq(len(x), 1 / 16000)
    band = (freqs > 70) & (freqs < 400)
    if not band.any():
        return None
    return float(freqs[band][np.argmax(spec[band])])


def speaker_f0(vocal, spk, srt_lines):
    """每说话人收集其行段的原声基频, 取中位数"""
    vals = {}
    for (s, e), who in zip(srt_lines, spk):
        f0 = seg_f0(vocal, s, e)
        if f0:
            vals.setdefault(who, []).append(f0)
    return {k: float(np.median(v)) for k, v in vals.items() if len(v) >= 1}, vals


def parse_srt_times(p):
    out = []
    for b in re.split(r'\n\n+', Path(p).read_text(encoding='utf-8').strip()):
        m = re.search(r'(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)', b)
        g = [int(v) for v in m.groups()]
        out.append((g[0]*3600+g[1]*60+g[2]+g[3]/1000, g[4]*3600+g[5]*60+g[6]+g[7]/1000))
    return out


def main():
    args = parse_args()
    spk = json.loads(Path(args.speaker_json).read_text(encoding="utf-8"))
    if not spk:
        raise SystemExit("speaker.json 为空")
    speakers = sorted(set(spk), key=lambda s: (len(s), s))
    print(f"[voices] 检测到说话人: {speakers}")

    mapping = {}
    if args.map:
        for kv in args.map.split(","):
            k, v = kv.split("=")
            mapping[k.strip()] = v.strip()
    elif args.voices:
        pool = [v.strip() for v in args.voices.split(",")]
        for i, s in enumerate(speakers):
            mapping[s] = pool[i % len(pool)]
    elif args.lang and args.vocal:
        if not args.srt:
            raise SystemExit("--vocal 需要 --srt 提供行时间轴")
        lines = parse_srt_times(args.srt)
        if len(lines) != len(spk):
            raise SystemExit(f"行数不齐: srt {len(lines)} vs speaker {len(spk)}")
        med, _ = speaker_f0(args.vocal, spk, lines)
        pool = VOICE_POOLS[args.lang]
        fi = mi = 0
        for s in speakers:
            f0 = med.get(s)
            if f0 is None:
                gender = 'f'
            else:
                gender = 'f' if f0 > F0_FEMALE_MIN else 'm'
            if gender == 'f':
                mapping[s] = pool['f'][fi % len(pool['f'])]; fi += 1
            else:
                mapping[s] = pool['m'][mi % len(pool['m'])]; mi += 1
            print(f"[voices] {s}: 原声F0中位数={f0 and round(f0,1)}Hz -> {'女' if gender=='f' else '男'} -> {mapping[s]}")
    elif args.lang:
        pool = VOICE_POOLS[args.lang]
        flat = pool['f'] + pool['m']
        for i, s in enumerate(speakers):
            mapping[s] = flat[i % len(flat)]
    else:
        raise SystemExit("需指定 --lang [--vocal] / --voices / --map 之一")

    line_roles = {str(i + 1): mapping[s] for i, s in enumerate(spk)}
    pj = Path(args.params_json)
    params = json.loads(pj.read_text(encoding="utf-8")) if pj.exists() else {}
    params["line_roles"] = line_roles
    pj.write_text(json.dumps(params, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[voices] 已写 line_roles ({len(line_roles)} 行) -> {pj}")


if __name__ == "__main__":
    main()
