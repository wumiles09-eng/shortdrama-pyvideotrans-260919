#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
setup_glm.py — 一键配置智谱 GLM 付费渠道 (翻译 glm-5.3-flash / 识别 glm-asr-2512)

从 Obsidian api.md 读取 key (绝不硬编码), 写入 pyvideotrans/videotrans/params.json:
  - zhipu_key   渠道密钥 (翻译渠道7 与 ASR 渠道16 共用)
  - zhipu_model 翻译模型名 (glm-5.3-flash)
配置后 CLI 用法:
  翻译: uv run cli.py --task sts --name x.srt --translate_type 7 --target_language_code en
  识别: uv run cli.py --task stt --name x.mp4 --recogn_type 16

用法:
  uv run setup_glm.py [--probe]   # --probe 先探活再写入
"""

import argparse
import json
import pathlib
import re
import sys
import urllib.request

API_DOC = pathlib.Path.home() / "Documents/Obsidian Vault/project/api/api.md"
PARAMS = pathlib.Path(__file__).resolve().parent.parent / "pyvideotrans/videotrans/params.json"
PROBE_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"


def read_key() -> str:
    text = API_DOC.read_text(encoding="utf-8")
    m = re.search(r"key[:：]\s*([0-9a-f]{32}\.[A-Za-z0-9]+)", text)
    if not m:
        raise SystemExit("未能从 api.md 解析出 key (格式: 32hex.suffix)")
    return m.group(1)


def probe(key: str) -> tuple:
    body = json.dumps({"model": "glm-5.3-flash",
                       "messages": [{"role": "user", "content": "ping"}],
                       "max_tokens": 4}).encode()
    req = urllib.request.Request(PROBE_URL, data=body, headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read(200).decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read(200).decode("utf-8", "ignore")
    except Exception as e:
        return 0, str(e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true", help="写入前先探活")
    args = ap.parse_args()

    key = read_key()
    print(f"[glm] 读取 key: {key[:6]}...{key[-4:]}")

    if args.probe:
        code, body = probe(key)
        print(f"[glm] 探活 HTTP {code}: {body[:120]}")
        if code == 200:
            print("[glm] 渠道可用 ✓")
        elif '"code":"1113"' in body or "1113" in body:
            print("[glm] key 有效但余额不足 (1113) — 已写入配置, 充值后即可用")
        else:
            print("[glm] 探活异常, 仍继续写入配置")

    data = json.loads(PARAMS.read_text(encoding="utf-8")) if PARAMS.exists() else {}
    data["zhipu_key"] = key
    data["zhipu_model"] = "glm-5.3-flash"
    data.setdefault("zhipu_thinking", False)
    PARAMS.parent.mkdir(parents=True, exist_ok=True)
    PARAMS.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[glm] 已写入 {PARAMS} (zhipu_key / zhipu_model=glm-5.3-flash)")


if __name__ == "__main__":
    main()
