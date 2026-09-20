#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kokoro_server.py — Kokoro-82M 本地 OpenAI 兼容 TTS 服务 (轻量, 无需 Kokoro-FastAPI)

端点: POST /v1/audio/speech  {"input": text, "voice": "af_heart", "speed": 1.0}
返回: audio/wav
pyvideotrans 对接: params.json "kokoro_api": "http://127.0.0.1:5066" (渠道29)

语种/音色 (hexgrad/Kokoro-82M):
  en: af_heart/bella/nicole... am_adam/michael... | es: ef_dario/em_alex | fr: ff_siwis
  it: if_sara/im_nicola | pt: pf_dora/pm_alex | zh: zf_xiaobei(中文仅女声)
  ⚠️ 不支持 de/id → 这两语种回退 Edge-TTS

依赖(独立环境): uv venv && uv pip install kokoro fastapi uvicorn soundfile
模型首次运行自动从 HF 下载 (走 HF_ENDPOINT=https://hf-mirror.com)

用法: uv run kokoro_server.py [--port 5066]
"""

import argparse
import io

import soundfile as sf
import uvicorn
from fastapi import FastAPI, Response
from pydantic import BaseModel

KOKORO = None


class SpeechReq(BaseModel):
    input: str
    voice: str = "af_heart"
    speed: float = 1.0
    model: str = "kokoro"
    response_format: str = "wav"


app = FastAPI(title="drama-kokoro-tts")


@app.post("/v1/audio/speech")
def speech(req: SpeechReq):
    if KOKORO is None:
        return Response(status_code=503, content="model not loaded")
    audio, sr = KOKORO.create(req.input, voice=req.voice, speed=req.speed)
    buf = io.BytesIO()
    sf.write(buf, audio, sr, format="WAV")
    return Response(content=buf.getvalue(), media_type="audio/wav")


@app.get("/health")
def health():
    return {"status": "ok", "loaded": KOKORO is not None}


def main():
    global KOKORO
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=5066)
    args = ap.parse_args()
    from kokoro import KPipeline
    KOKORO = KPipeline(lang_code="a")  # 按 voice 前缀自动切语言
    print(f"[kokoro] 模型就绪, 监听 :{args.port}")
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
