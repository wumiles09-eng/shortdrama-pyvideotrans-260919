---
name: drama-glm-channels
description: 配置与排障智谱 GLM 付费渠道 (glm-5.3-flash/flashx 翻译渠道7、GLM-ASR-2512 识别渠道16、GLM-OCR layout_parsing)。当用户要接 GLM、智谱翻译、glm-asr/glm-ocr,或遇 1113/429 报错时使用。
---

# 智谱 GLM 渠道配置与排障 (pyvideotrans + drama-tools)

## 渠道/引擎映射 (实测 2026-09-19)

| 环节 | 入口 | 渠道/参数 | 模型 | key 字段 |
|------|------|----------|------|---------|
| 翻译 | cli `--translate_type 7` | ZHIPUAI | glm-5.3-flash / glm-5.3-flashx / glm-5.3 | zhipu_key |
| 识别 | cli `--recogn_type 16` | ZHIPU_API | glm-asr-2512 (内置) | zhipu_key |
| OCR | `ocr_srt.py --engine glm` | layout_parsing | glm-ocr | api.md 直读 |

可用模型清单 (源: Obsidian 小说/国内小说/基础信息.md + api.md):
**GLM-5.3-Flash / GLM-5.3-FlashX / GLM-5.3 / GLM-ASR-2512 / GLM-OCR**
官方文档: https://docs.z.ai/api-reference/introduction (OCR: docs.z.ai/api-reference/tools/layout-parsing.md)

## 双端点事实 (关键)

同一 key 在两个端点**认证均通过**, 余额不足 (1113) 两端同时报:
- cn 国内站: `https://open.bigmodel.cn/api/paas/v4/` (pyvideotrans 默认)
- intl 国际站: `https://api.z.ai/api/paas/v4/` (z.ai 文档站)

**充值侧决定可用端点** → 上游已补丁支持 `params.json` 的 `zhipu_base_url` 切换
(若只在国际站充值, 必须切 intl, 否则打不通)。

## 一键配置

```bash
cd "/Users/mac/Documents/project/py videos/drama-tools"
uv run setup_glm.py --probe                          # 双端点探活 + 写默认 (cn + glm-5.3-flash)
uv run setup_glm.py --endpoint intl --model glm-5.3-flashx --probe   # 国际站 + FlashX
```

## 排障表 (全部实测)

| 现象 | 原因 | 处理 |
|------|------|------|
| HTTP 429 + body code 1113 | key 有效但余额不足 (状态码是 429, 别误判为限流) | 充值; 不要改代码 |
| HTTP 429 无 1113 | 真限流 (短时多次探活会触发) | 等 30s 重试 |
| 翻译空结果 | zhipu_model 名不对 | 必须全小写 `glm-5.3-flash`; flashx 是 `glm-5.3-flashx` |
| 打通intl仍报1113 | 账户在另一端点充值 | `setup_glm.py --endpoint <另一端> --probe` |
| GLM-ASR 无时间轴 | API 返回纯文本 | pyvideotrans 内部切音频分段, 正常 |
| GLM-OCR base64 格式错 | 文档未明示前缀 | ocr_srt.py 已内置 纯b64→dataURL 自动回退 |
| urllib `module has no attribute error` | 少 import urllib.error | 已修 (drama-tools) |

## 探活命令 (curl 直测)

```bash
KEY=$(python3 -c "print(open('$HOME/Documents/Obsidian Vault/project/api/api.md').read().split('key:')[1].strip())")
curl -sS -m 15 -w '\nHTTP %{http_code}\n' -X POST 'https://api.z.ai/api/paas/v4/chat/completions' \
  -H "Authorization: Bearer $KEY" -H 'Content-Type: application/json' \
  -d '{"model":"glm-5.3-flash","messages":[{"role":"user","content":"ping"}],"max_tokens":5}'
# choices = 可用; {"error":{"code":"1113"}}+HTTP429 = 余额不足
```

## GLM-OCR (layout_parsing) 要点

- `POST /api/paas/v4/layout_parsing` body: `{"model":"glm-ocr","file":"<url或base64>"}`
- 响应文本在 `md_results`; 结构化在 `layout_details[[{content,bbox_2d(归一化),label}]]`
- 已封装: `ocr_srt.py --engine glm` (区域标定仍用本地 RapidOCR 省 API 调用)
- 1113 时会明确报错退出, 不会产出空 srt

## 上游补丁关联 (本仓库)

- `videotrans/translator/_zhipuai.py`: api_url 读 `zhipu_base_url` (默认 cn, 保持上游兼容)
- `videotrans/configure/constants.py`: Zhipuai_Model 补 glm-5.3-flash/glm-5.3-flashx
- GLM-ASR 渠道 (_glmasr.py) 仍硬编码 bigmodel.cn —— 若走国际站 ASR, 需同样补丁 (待真需求再做)

## 红线

- key 来源 `~/Documents/Obsidian Vault/project/api/api.md` (小说/国内小说/基础信息.md 同 key), 绝不写入仓库
