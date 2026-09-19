#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
assign_voices.py — 按说话人分配多音色 (Edge-TTS, 7 目标语种)

读取 pyvideotrans 说话人分离结果 speaker.json (每行字幕的说话人 id 列表),
将每个说话人映射到一个 Edge-TTS 音色, 生成 line_roles {行号: 音色} 写入
pyvideotrans/videotrans/params.json, 之后 vtv/tts 配音阶段即按行使用不同音色。

用法:
  # 指定语种, 男女交替自动池
  uv run assign_voices.py --speaker-json spk.json --params-json ../pyvideotrans/videotrans/params.json --lang es
  # 显式映射 / 逗号音色序列 (同旧版)
  uv run assign_voices.py --speaker-json spk.json --params-json ... \
      --voices zh-CN-YunyangNeural,zh-CN-XiaoxiaoNeural
  uv run assign_voices.py --speaker-json spk.json --params-json ... \
      --map "说话人0=zh-CN-YunxiNeural,说话人1=zh-CN-XiaoyiNeural"
"""

import argparse
import json
from pathlib import Path

# Edge-TTS 音色池 (2026-09-19 逐个 list_voices 校验存在); 每语种 [女,男,女,男...] 延伸
VOICE_POOLS = {
    "en": ["en-US-AriaNeural", "en-US-BrianNeural", "en-US-JennyNeural", "en-US-GuyNeural"],
    "es": ["es-ES-ElviraNeural", "es-ES-AlvaroNeural", "es-MX-DaliaNeural", "es-MX-JorgeNeural"],
    "pt": ["pt-BR-FranciscaNeural", "pt-BR-AntonioNeural", "pt-PT-FernandaNeural", "pt-PT-DuarteNeural"],
    "fr": ["fr-FR-DeniseNeural", "fr-FR-HenriNeural", "fr-CA-SylvieNeural", "fr-CA-AntoineNeural"],
    "de": ["de-DE-KatjaNeural", "de-DE-ConradNeural", "de-DE-AmalaNeural", "de-DE-KillianNeural"],
    "id": ["id-ID-GadisNeural", "id-ID-ArdiNeural"],  # 印尼语仅 2 个音色, 多角色循环使用
    "it": ["it-IT-ElsaNeural", "it-IT-DiegoNeural", "it-IT-FabiolaNeural"],
    "zh": ["zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural", "zh-CN-XiaoyiNeural", "zh-CN-YunjianNeural"],
}


def parse_args():
    p = argparse.ArgumentParser(description="说话人 -> 多音色分配 (7语种)")
    p.add_argument("--speaker-json", required=True, help="pyvideotrans speaker.json 路径")
    p.add_argument("--params-json", required=True, help="pyvideotrans videotrans/params.json 路径")
    p.add_argument("--lang", default=None, choices=list(VOICE_POOLS),
                   help="目标语种自动池 (en/es/pt/fr/de/id/it/zh), 男女交替")
    p.add_argument("--voices", default=None, help="按说话人顺序音色, 逗号分隔 (优先于 --lang)")
    p.add_argument("--map", default=None, help="显式映射 '说话人0=音色,...' (最高优先)")
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
    elif args.voices:
        pool = [v.strip() for v in args.voices.split(",")]
        for i, s in enumerate(speakers):
            mapping[s] = pool[i % len(pool)]
    elif args.lang:
        pool = VOICE_POOLS[args.lang]
        for i, s in enumerate(speakers):
            mapping[s] = pool[i % len(pool)]
    else:
        raise SystemExit("需指定 --lang / --voices / --map 之一")
    print(f"[voices] 说话人->音色: {json.dumps(mapping, ensure_ascii=False)}")

    line_roles = {str(i + 1): mapping[s] for i, s in enumerate(spk)}

    pj = Path(args.params_json)
    params = json.loads(pj.read_text(encoding="utf-8")) if pj.exists() else {}
    params["line_roles"] = line_roles
    pj.write_text(json.dumps(params, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[voices] 已写 line_roles ({len(line_roles)} 行) -> {pj}")


if __name__ == "__main__":
    main()
