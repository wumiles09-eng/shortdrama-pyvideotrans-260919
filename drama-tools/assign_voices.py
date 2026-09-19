#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
assign_voices.py — 按说话人分配多音色 (Edge-TTS 免费音色)

读取 pyvideotrans 说话人分离结果 speaker.json (每行字幕的说话人 id 列表),
将每个说话人映射到一个 Edge-TTS 音色, 生成 line_roles {行号: 音色} 写入
pyvideotrans/videotrans/params.json, 之后 vtv/tts 配音阶段即按行使用不同音色。

用法:
  uv run assign_voices.py --speaker-json spk.json --params-json ../pyvideotrans/videotrans/params.json \
      --voices zh-CN-YunyangNeural,zh-CN-XiaoxiaoNeural
  # 音色列表按说话人顺序逗号分隔; 也可 --auto 让男名/女名交替自动配对
"""

import argparse
import json
from pathlib import Path

# Edge-TTS 常用中文音色池 (免费): 男/女
MALE_VOICES = ["zh-CN-YunyangNeural", "zh-CN-YunxiNeural", "zh-CN-YunjianNeural"]
FEMALE_VOICES = ["zh-CN-XiaoxiaoNeural", "zh-CN-XiaoyiNeural", "zh-CN-liaoning-XiaobeiNeural"]


def parse_args():
    p = argparse.ArgumentParser(description="说话人 -> 多音色分配")
    p.add_argument("--speaker-json", required=True, help="pyvideotrans speaker.json 路径")
    p.add_argument("--params-json", required=True, help="pyvideotrans videotrans/params.json 路径")
    p.add_argument("--voices", default=None,
                   help="按说话人顺序的音色, 逗号分隔 (默认: 男女交替自动池)")
    p.add_argument("--map", default=None,
                   help="显式映射, 例: 说话人0=zh-CN-YunxiNeural,说话人1=zh-CN-XiaoyiNeural (优先级最高)")
    return p.parse_args()


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
    else:
        pool = [v.strip() for v in args.voices.split(",")] if args.voices else None
        for i, s in enumerate(speakers):
            if pool:
                mapping[s] = pool[i % len(pool)]
            else:
                # 自动: 男女交替
                mapping[s] = (MALE_VOICES + FEMALE_VOICES)[i] if i < 3 else \
                             (FEMALE_VOICES + MALE_VOICES)[i - 3] if i < 6 else \
                             (MALE_VOICES + FEMALE_VOICES)[i % 6]
    print(f"[voices] 说话人->音色: {json.dumps(mapping, ensure_ascii=False)}")

    line_roles = {str(i + 1): mapping[s] for i, s in enumerate(spk)}

    pj = Path(args.params_json)
    params = json.loads(pj.read_text(encoding="utf-8")) if pj.exists() else {}
    params["line_roles"] = line_roles
    pj.write_text(json.dumps(params, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[voices] 已写 line_roles ({len(line_roles)} 行) -> {pj}")


if __name__ == "__main__":
    main()
