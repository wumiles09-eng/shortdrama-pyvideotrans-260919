#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
setup_glm.py — 一键配置智谱 GLM 付费渠道 (翻译/ASR/OCR)

从 Obsidian api.md 读取 key (绝不硬编码), 写入 pyvideotrans/videotrans/params.json:
  - zhipu_key     渠道密钥 (翻译渠道7 / ASR 渠道16 共用)
  - zhipu_model   翻译模型 (glm-5.3-flash 或 glm-5.3-flashx)
  - zhipu_base_url 端点 (cn=open.bigmodel.cn 国内站默认 / intl=api.z.ai 国际站)

配置后 CLI 用法:
  翻译: uv run cli.py --task sts --name x.srt --translate_type 7 --target_language_code en
  识别: uv run cli.py --task stt --name x.mp4 --recogn_type 16
  OCR : drama-tools/ocr_srt.py --engine glm (独立, 不经 pyvideotrans)

用法:
  uv run setup_glm.py --probe                 # 探活双端点并写入默认
  uv run setup_glm.py --endpoint intl --model glm-5.3-flashx --probe
"""

import argparse
import json
import pathlib
import re
import urllib.error
import urllib.request

API_DOC = pathlib.Path.home() / "Documents/Obsidian Vault/project/api/api.md"
PARAMS = pathlib.Path(__file__).resolve().parent.parent / "pyvideotrans/videotrans/params.json"
ENDPOINTS = {
    "cn": "https://open.bigmodel.cn/api/paas/v4/",
    "intl": "https://api.z.ai/api/paas/v4/",
}


def read_key() -> str:
    text = API_DOC.read_text(encoding="utf-8")
    m = re.search(r"key[:：]\s*([0-9a-f]{32}\.[A-Za-z0-9]+)", text)
    if not m:
        raise SystemExit("未能从 api.md 解析出 key (格式: 32hex.suffix)")
    return m.group(1)


def probe(key: str, base_url: str, model: str) -> tuple:
    url = base_url.rstrip("/") + "/chat/completions"
    body = json.dumps({"model": model,
                       "messages": [{"role": "user", "content": "ping"}],
                       "max_tokens": 4}).encode()
    req = urllib.request.Request(url, data=body, headers={
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
    ap.add_argument("--probe", action="store_true", help="写入前探活")
    ap.add_argument("--endpoint", choices=list(ENDPOINTS), default="cn",
                    help="端点: cn=bigmodel.cn 国内站 (默认) / intl=api.z.ai 国际站")
    ap.add_argument("--model", default="glm-5.3-flash",
                    choices=["glm-5.3-flash", "glm-5.3-flashx", "glm-5.3"],
                    help="翻译模型 (默认 glm-5.3-flash)")
    args = ap.parse_args()

    key = read_key()
    print(f"[glm] 读取 key: {key[:6]}...{key[-4:]}")

    if args.probe:
        for name, url in ENDPOINTS.items():
            code, body = probe(key, url, args.model)
            tag = "可用 ✓" if code == 200 else (
                "key有效但余额不足 (1113)" if "1113" in body else "异常")
            print(f"[glm] {name:4s} {url} -> HTTP {code} [{tag}]")

    data = json.loads(PARAMS.read_text(encoding="utf-8")) if PARAMS.exists() else {}
    data["zhipu_key"] = key
    data["zhipu_model"] = args.model
    data["zhipu_base_url"] = ENDPOINTS[args.endpoint]
    data.setdefault("zhipu_thinking", False)
    PARAMS.parent.mkdir(parents=True, exist_ok=True)
    PARAMS.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[glm] 已写入 {PARAMS}")
    print(f"[glm] zhipu_model={args.model} zhipu_base_url={ENDPOINTS[args.endpoint]}")


if __name__ == "__main__":
    main()
