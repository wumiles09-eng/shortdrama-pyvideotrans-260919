---
name: drama-ollama-local
description: 本地 ollama 免费模型评估与接入 (基于 32GB Apple M4 实测)。当用户要用本地大模型做字幕翻译/LLM断句,或问本机能跑什么模型时使用。
---

# 本地 ollama 免费模型 (32GB Apple M4 实测评估)

## 本机基线 (2026-09-19 实测)

- Apple M4 / 统一内存 32GB / macOS
- ollama 0.32.15 (服务 localhost:11434)
- 可跑规模经验值 (留 8GB 给系统+whisper+F5 并发):
  - **7B Q4_K_M (~4.7GB): 流畅, 翻译首选** ← 已选
  - 14B Q4 (~9GB): 可跑, 单条慢 2-3 倍, 质量小升 — 追求质量再上
  - 32B Q4 (~20GB): 勉强能跑但挤占 ASR/TTS 内存, 不推荐全流程并发
  - 70B+: 32GB 不可行

## 已选模型与理由

| 用途 | 模型 | 大小 | 理由 |
|------|------|------|------|
| 字幕翻译 (中↔英↔多语) | **qwen2.5:7b-instruct-q4_K_M** | 4.7GB | Qwen 系中英最强开源, 指令遵循好, 7B Q4 速度/质量平衡; 7 目标语种全覆盖 |
| 备选升档 | qwen2.5:14b-instruct-q4_K_M | 9GB | 质量提升, 速度换 |
| LLM 断句/纠错 (rephrase) | 同上复用 | — | — |

参考源: HF qwen/Qwen2.5-7B-Instruct (GitHub QwenLM), Apache-2.0。

## 接入 pyvideotrans (渠道9 CompatibleAI/LocalModel)

```bash
ollama pull qwen2.5:7b-instruct-q4_K_M   # 已拉取
# GUI (sp.py) → 翻译设置 → CompatibleAI: api url=http://localhost:11434/v1, model=qwen2.5:7b-instruct-q4_K_M, key 任意
# 或写 params.json:
python3 -c "
import json,pathlib
p=pathlib.Path('pyvideotrans/videotrans/params.json'); d=json.loads(p.read_text())
d['localllm_api']='http://localhost:11434/v1'; d['localllm_model']='qwen2.5:7b-instruct-q4_K_M'; d['localllm_key']='ollama'
p.write_text(json.dumps(d,ensure_ascii=False,indent=1))"
# 使用: cli.py --task sts --translate_type 9 --target_language_code es
```

## 评估结论备忘

- ASR/说话人分离/TTS **不迁 ollama**: whisper-ONNX/CT2 与 pyannote 系在专用推理上远优于 LLM 方案; ollama 只补 LLM 环节 (翻译/断句/纠错)
- 本地翻译适用场景: 断网/大批量/隐私敏感; 日常推荐 GLM coding 端点 (质量已实测更优)
- 7 语种翻译实测: 见 docs/verification.md 对应轮次

## 排障

| 现象 | 处理 |
|------|------|
| ollama 请求超时 | 检查 `pgrep ollama`; `OLLAMA_HOST=127.0.0.1:11434` |
| 首 token 慢 | 模型冷加载, 第二次起正常; 常驻可 `ollama run qwen2.5:7b --keepalive 1h` 预热 |
| 内存吃紧 (并发全流程) | 用 7B 不用 14B; 或翻译与 ASR 分步跑 |
