---
name: drama-glm-channels
description: 配置与排障 pyvideotrans 的智谱 GLM 付费渠道 (glm-5.3-flash 翻译渠道7 / GLM-ASR-2512 识别渠道16)。当用户要接 GLM、智谱翻译、glm-asr 识别或遇 1113 报错时使用。
---

# 智谱 GLM 渠道配置 (pyvideotrans)

## 渠道映射 (实测自 videotrans/{translator,recognition}/_constants.py)

| 环节 | CLI 参数 | 渠道号 | 模型 | key 字段 |
|------|---------|-------|------|---------|
| 翻译 | `--translate_type 7` | ZHIPUAI | glm-5.3-flash (可手填) | zhipu_key |
| 识别 | `--recogn_type 16` | ZHIPU_API | glm-asr-2512 (内置) | zhipu_key |

## 配置方式

1. GUI: `cd pyvideotrans && uv run sp.py` → 翻译设置→智谱AI→粘贴 key
2. 直接写 `videotrans/cfg.json`? — 不, key 实际存 `videotrans/params.json` 的 zhipu_key (AppParams)
   ```bash
   python3 -c "import json,pathlib; p=pathlib.Path('videotrans/params.json'); d=json.loads(p.read_text()); d['zhipu_key']='<KEY>'; p.write_text(json.dumps(d,ensure_ascii=False,indent=1))"
   ```
   同时确认 `zhipu_model` 设为 `glm-5.3-flash`。

## 排障 (2026-09-19 实测)

| 现象 | 原因 | 处理 |
|------|------|------|
| HTTP 1113 余额不足 | key 有效但账户无余额 | 充值后重试; 不要改代码 |
| key 在 api.z.ai 与 open.bigmodel.cn 同错 | 同一账号体系 | 无需改 pyvideotrans 内置的 bigmodel.cn 地址 |
| 翻译空结果 | zhipu_model 名不对 | 必须 `glm-5.3-flash` 全小写 |
| GLM-ASR 无时间轴 | 该 API 返回纯文本 | pyvideotrans 已内部切音频分段处理, 属正常 |

## 探活命令 (调用前先测)

```bash
curl -sS -m 15 -X POST 'https://open.bigmodel.cn/api/paas/v4/chat/completions' \
  -H "Authorization: Bearer $ZHIPU_KEY" -H 'Content-Type: application/json' \
  -d '{"model":"glm-5.3-flash","messages":[{"role":"user","content":"ping"}],"max_tokens":5}'
# {"choices":...} = 可用; {"error":{"code":"1113"...}} = 余额不足
```

## 红线

- key 来源 `~/Documents/Obsidian Vault/project/api/api.md`, 绝不写入仓库任何文件
