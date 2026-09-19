---
name: drama-stt-pipeline
description: 短剧 ASR 转录+说话人分离+多音色配音全流程 (faster-whisper/FunASR + Edge-TTS 免费本地)。当用户要转录短剧、分离角色、按角色配音、翻译短剧视频时使用。
---

# 短剧转录→分离→配音 全流程

## 环境

```bash
cd "/Users/mac/Documents/project/py videos/pyvideotrans"
export HF_ENDPOINT=https://hf-mirror.com   # 模型下载走镜像
```

## 流程

### 1) STT + 说话人分离 (免费)

```bash
uv run cli.py --task stt --name "<视频>" --detect_language zh-cn \
  --model_name small --enable_diariz --nums_diariz -1
# 产物: output 目录 zh-cn.srt + speaker.json (每行说话人 id)
```

- 中文识别模型选 `small` 起步; 精度不足升 `medium`/`large-v3` (M 芯 CPU 可跑, 慢)
- 说话人分离默认 built (onnx, ModelScope 回退下载); 中文剧建议 settings 里 speaker_type=ali_CAM

### 2) OCR 与 ASR 互补

硬字幕剧同时跑 `drama-ocr-subtitle` 技能, 以 OCR 为基准 (短剧字幕=台词原文), ASR 补时间轴与无字幕段。

### 3) 翻译 (免费 Google→付费 glm-5.3-flash)

```bash
uv run cli.py --task sts --name "<srt>" --translate_type 0 --target_language_code en  # 免费
uv run cli.py --task sts --name "<srt>" --translate_type 7 --target_language_code en  # 智谱, 需 key+余额
```

### 4) 按角色多音色配音 (Edge-TTS 免费)

```bash
cd ../drama-tools
uv run assign_voices.py --speaker-json <spk.json> \
  --params-json ../pyvideotrans/videotrans/params.json \
  --voices zh-CN-YunxiNeural,zh-CN-XiaoxiaoNeural   # 按说话人顺序
cd ../pyvideotrans
uv run cli.py --task vtv --name "<视频>" --source_language_code zh-cn \
  --target_language_code zh-cn --enable_diariz --is_separate --subtitle_type 2
```

- `line_roles` 按行号分配音色, assign_voices 自动生成
- `--is_separate` 人声/背景分离: 译制配音不压背景乐

### 5) 音色匹配建议 (@drama)

年长男 Yunjian / 年轻男 Yunxi / 女主 Xiaoxiao / 少女 Xiaoyi / 旁白 Yunyang

## 验收

- srt 条数与时长覆盖>95% 对白
- speaker.json 说话人数与剧情主要角色数一致 (短剧通常 2-4)
- 配音产物每行对应音频文件存在且时长≤字幕时长*1.3
