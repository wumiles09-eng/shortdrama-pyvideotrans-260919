---
name: drama-stt-pipeline
description: 海外短剧翻译全流程 (识别→提取→角色/音色识别→音色分离→音色克隆→去原音→翻译→按角色配音→字幕压制)。支持中/英原文 → 英西葡法德印尼意 7 语种译文。当用户要端到端译制短剧或执行任一环节时使用。
---

# 海外短剧翻译全流程 (7 语种)

## 语种矩阵 (核心速查)

**原文**: 中文(zh-cn) / 英语(en) —— ASR 由 faster-whisper 自动覆盖
**译文**: 英语 en · 西语 es · 葡语 pt · 法语 fr · 德语 de · 印尼语 id · 意语 it (pyvideotrans 全部原生支持)

| 环节 | 首选(已实测) | 免费回退 | 克隆方案 |
|------|-------------|---------|---------|
| ASR 识别 | faster-whisper small (本地) | FunASR(纯中文更优) | — |
| 翻译-付费 | GLM glm-5.3-flash (渠道7, coding端点, 7语种全) | — | — |
| 翻译-免费 | 微软 (渠道1, 7语种全) | 本地 ollama qwen2.5 (渠道9, 见 drama-ollama-local) | — |
| 配音-多音色 | Edge-TTS (渠道0, 7语种全音色) | — | — |
| 配音-**音色克隆** | F5-TTS (渠道2) | — | **en/es/fr/de/it/zh 可克隆; id/pt 无克隆模型 → 回退 Edge-TTS** |

### Edge-TTS 各语色对 (按角色男女交替)

| 语种 | 女声 | 男声 |
|------|------|------|
| en | en-US-AriaNeural / JennyNeural | en-US-BrianNeural / GuyNeural |
| es | es-ES-ElviraNeural | es-ES-AlvaroNeural |
| pt | pt-BR-FranciscaNeural | pt-BR-AntonioNeural |
| fr | fr-FR-DeniseNeural | fr-FR-HenriNeural |
| de | de-DE-KatjaNeural | de-DE-ConradNeural |
| id | id-ID-GadisNeural | id-ID-ArdiNeural |
| it | it-IT-ElsaNeural | it-IT-DiegoNeural |

## 全流程命令 (端到端)

```bash
cd "/Users/mac/Documents/project/py videos/pyvideotrans"
NOPROXY="env -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy -u ALL_PROXY -u all_proxy"

# ── 一条命令全流程 (以 中→西语 + 音色分离 + 按角色配音 + 硬字幕压制为例) ──
# 前置: drama-tools/assign_voices.py 已写好目标语种音色的 line_roles
# ⚠️ 电平/同步三参数 (2026-09-20 实测修复, 缺一会出现"有字幕没配音"听感/音画不同步):
#    --align_sub_audio  字幕时间轴贴合配音实际位置 (译制片标准; 优于 voice_autorate, 见 verification 修复轮2)
#    --volume +15%     配音增益
#    --backaudio-volume 0.35  背景乐降量 (上游默认0.8 会淹没配音; 0.3-0.4 推荐)
$NOPROXY HF_ENDPOINT=https://hf-mirror.com uv run --no-sync cli.py --task vtv \
  --name 第01集.mp4 --source_language_code zh-cn --target_language_code es \
  --model_name small --enable_diariz --nums_diariz 4 \
  --translate_type 7 \
  --is_separate \
  --voice_autorate --volume +15% --backaudio-volume 0.35 \
  --voice_role "es-ES-AlvaroNeural" \
  --subtitle_type 1
```

环节与参数对照 (vtv 内部自动串起):
1. **字幕识别+提取**: 内置 ASR → srt; 硬字幕剧先用 `drama-ocr-subtitle` 无声提取对照
2. **角色/音色识别**: `--enable_diariz --nums_diariz N` (N=剧情角色数, 实测约束后 8→5 人与剧情吻合)
   ⚠️ **源字幕优先用 OCR 硬字幕** (`--source-srt 第01集.ocr.srt`): ASR 断句会吞并短句("老婆/哎呦"类称呼语
   被合并或丢失→无译文无配音); OCR 原文时间轴精确到句 (实测 42条 vs ASR 16条, 修复后 42/42 全覆盖)
3. **音色分离**: `--is_separate` → vocal.wav(人声)+instrument.wav(背景乐)
4. **去原音**: vtv 配音模式天然替换原音轨; `--is_separate` 时背景乐保留、人声被译制配音替换 (embed_bgm 控制)
5. **字幕翻译**: `--translate_type 7`=GLM / `1`=微软免费 / `9`=本地ollama
6. **按角色配音**: params.json `line_roles` (由 assign_voices.py 写入, cli 补丁自动装载)
7. **字幕压制**: `--subtitle_type` 1=硬字幕(译文) 3=硬字幕双语 2/4=软字幕

## 音色克隆 (F5-TTS, 原声克隆)

```bash
# voice_role=clone + tts_type 2 (F5-TTS): 每行用原视频对应人声段作参考音频克隆
$NOPROXY HF_ENDPOINT=https://hf-mirror.com uv run --no-sync cli.py --task vtv \
  --name 第01集.mp4 --source_language_code zh-cn --target_language_code en \
  --enable_diariz --nums_diariz 4 --is_separate \
  --tts_type 2 --voice_role "clone" --subtitle_type 1
```

- 首次运行自动从 HF (走 hf-mirror) 拉克隆模型 (~1.4GB/语种) + vocos 声码器
- **语种覆盖: en/es/fr/de/it/zh 有模型; id/pt 无 → 报错时改用 Edge-TTS 音色方案**
- 克隆质量取决于参考人声纯净度: 务必配 `--is_separate` (用分离后的 vocal 作参考)
- line_roles 中也可对部分角色写 "clone" 部分角色写 Edge 音色 (混合模式)

## 海外短剧译制要点 (@drama 协作)

1. **称呼语统一**: 中文亲属称谓(奶奶/儿媳/叔叔)在西语葡语等无直接对应 → 按剧情关系译 (Señora/Sogra...) 全集一致
2. **文化词**: 系统/境界/逆袭等网文词 → 目标语惯用表达; 金手指类术语建 glossary.md
3. **语气保真**: 短剧对白夸张冲突强, 避免 GLM/翻译渠道输出书面腔 (渠道自带的译制 prompt 已处理, 抽查即可)
4. **字幕长度**: 德语/西语句长普遍长于中文 30%+, 断句上限调大 (settings other_len)
5. **配音节奏**: 目标语长句配音超时时加 `--voice_autorate` (自动加速对齐) 而非删词

## 验收清单

- [ ] **配音可闻性 (差分法)**: 逐行 mix_rms ≥ (instrument_rms + 20·log10(backaudio_volume) + 5dB);
      判据基准必须用「BGM×降量系数」—— 用原始 instrument 当基准会把所有行误判缺失
      (2026-09-20 教训: 18/18 行语音实际都在, 是被 BGM 淹没, 差分基准错导致误诊为"缺段")
- [ ] **同步**: 每条字幕窗尾后 0.1-0.9s 段 = 纯 BGM (混音-BGM有效电平 差≤4dB);
      超长句个别溢出 (<1s) 可接受, 连续多句溢出必须开 --voice_autorate 重跑
- [ ] srt 覆盖>90% 对白时长, 抽 5 条与画面字幕一致
- [ ] speaker.json 角色数 = 剧情设定; 约束参数已用
- [ ] vocal/instrument.wav 存在且听感分离
- [ ] 译制视频: 原音已替换 / 背景乐保留 / 双语或译文硬字幕清晰
- [ ] 多角色配音: 不同说话人音色可辨 (基频抽检或听感)
- [ ] 克隆模式: 音色与原声相似度抽听; 跑前必须清空 params.json 的 line_roles
