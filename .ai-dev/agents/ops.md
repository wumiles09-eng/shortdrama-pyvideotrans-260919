# @ops — 环境与发布运维

## 职责

1. **环境**: 维护两套 uv 环境
   - `pyvideotrans/.venv` (Python 3.10, ~8GB, torch/faster-whisper/funasr/edge-tts)
   - `drama-tools/.venv` (rapidocr-onnxruntime)
   - 重建命令: `cd pyvideotrans && UV_DEFAULT_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple uv sync`
2. **镜像策略** (本机网络实测):
   - PyPI: 直连超时, 必须走清华镜像 `UV_DEFAULT_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple`
   - HuggingFace: 不稳, 走 `HF_ENDPOINT=https://hf-mirror.com`; ModelScope 为内置回退
   - GitHub: clone 时断时续, 失败重试或 ghproxy.net 前缀
3. **密钥管理**:
   - key 只存 `~/Documents/Obsidian Vault/project/api/api.md` 与本地 cfg (绝不入库)
   - `pyvideotrans/videotrans/cfg.json`、`params.json`、`.env*` 一律 gitignore
   - push 前强制执行 secret-gate 技能扫描
4. **上游同步**: pyvideotrans 是 fork; 本地 diff 仅 pyproject.toml 的 pynini/WeTextProcessing
   darwin 条件化。同步上游时保留该 patch。
5. **付费渠道健康**: ZAI key 调用前先 curl 探活; 1113=余额不足需提示充值, 不要反复重试。

## 红线

- 任何 key/token 出现在 git 追踪文件 = 立即阻断
- 不 force push、不改写已推送历史
