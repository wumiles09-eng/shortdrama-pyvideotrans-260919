# 短剧翻译系统 (基于 pyvideotrans 本地部署适配)

将开源视频翻译系统 [pyvideotrans](https://github.com/jianchang512/pyvideotrans) 本地部署并适配为**短剧翻译系统**:硬字幕 OCR 提取、字幕翻译、多角色识别、音色分离、按角色多音色配音。

## 目录结构

```
py videos/
├── pyvideotrans/      # 上游源码 (见「上游改动」)
├── drama-tools/       # 短剧适配层 (自研工具)
│   ├── ocr_srt.py         # 硬字幕 OCR 提取 -> SRT (免费: OpenCV+RapidOCR)
│   └── assign_voices.py   # 说话人 -> Edge-TTS 音色分配 -> line_roles
├── outputs/           # 实验产物 (第01/02集 srt、视频等)
├── .ai-dev/           # aidevteam 工作区 (agents/skills/state)
└── README.md
```

## 环境要求

- macOS (arm64) / Python 3.10 (uv 自动管理) / FFmpeg / libsndfile
- 两个独立 uv 环境:
  - `pyvideotrans/.venv` — 主系统 (torch 2.7.1 / faster-whisper / funasr / edge-tts 等, ~8GB)
  - `drama-tools/.venv` — OCR 工具 (rapidocr-onnxruntime / opencv)

## 快速开始 (全部实测通过, 2026-09-19)

```bash
# 0) 运行环境约定: 直连不走本地代理 (模型/镜像下载更快且避免挂死)
NOPROXY="env -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy -u ALL_PROXY -u all_proxy"

# 1) OCR 提取硬字幕 (免费本地, auto 字幕带标定)
cd drama-tools
uv run ocr_srt.py --input 第01集.mp4 --output 第01集.ocr.srt --debug

# 2) 语音转录 + 说话人分离 (免费 faster-whisper small + ali_CAM)
cd ../pyvideotrans
$NOPROXY HF_ENDPOINT=https://hf-mirror.com uv run --no-sync cli.py --task stt \
  --name 第01集.mp4 --detect_language zh-cn --model_name small \
  --enable_diariz --nums_diariz 0 --output-dir ../outputs/stt01
# 产物: zh-cn.srt (带 [spkN] 标签) + speaker.json
# 首次运行前 cfg.json 设 speaker_type=ali_CAM (中文更准); 模型已缓存于 pyvideotrans/models/

# 3) 字幕翻译 (免费微软渠道1; Google渠道0被反爬; 付费智谱渠道7)
$NOPROXY uv run --no-sync cli.py --task sts --name x.srt --translate_type 1 \
  --source_language_code zh-cn --target_language_code en

# 4) 多角色配音: 说话人→音色映射 (写入 params.json line_roles)
cd ../drama-tools
uv run assign_voices.py --speaker-json ../outputs/stt01/speaker.json \
  --params-json ../pyvideotrans/videotrans/params.json \
  --voices "en-US-AriaNeural,en-US-GuyNeural,..."   # 按说话人 spk0..spkN 顺序

# 5a) 仅配音: cli 补丁自动装载 line_roles 多音色合成
$NOPROXY uv run --no-sync cli.py --task tts --name x.en.srt --tts_type 0 \
  --voice_role en-US-GuyNeural --target_language_code en

# 5b) 全流程: ASR+分离+翻译+人声分离+多音色配音+硬字幕合成视频 (~8min/90s剧)
$NOPROXY HF_ENDPOINT=https://hf-mirror.com uv run --no-sync cli.py --task vtv \
  --name 第01集.mp4 --source_language_code zh-cn --target_language_code en \
  --model_name small --enable_diariz --is_separate \
  --voice_role en-US-GuyNeural --subtitle_type 1
```

## 模型渠道

| 环节 | 免费/开源 (已验证) | 付费 (已接入, 待充值) |
|------|-------------------|----------------------|
| 字幕识别 OCR | RapidOCR 本地 (drama-tools) | GLM-OCR `--engine glm` (待标准侧充值) |
| 语音识别 ASR 档 | **FireRedASR (渠道5, 错字最少)** / SenseVoice(渠道3+SenseVoiceSmall) / faster-whisper | GLM-ASR (渠道16, 待充值) |
| 音色克隆 | **CosyVoice2 (渠道14, 本地webui:8000, 贴合8/9)**; F5(渠道2, 备用) | — |
| 语音识别 ASR | faster-whisper / FunASR 本地 | 智谱 GLM-ASR-2512 (渠道16, zhipu_key) |
| 字幕翻译 | Google (渠道0, 本机被反爬) / 微软 (渠道1, 可用) | **智谱 glm-5.3-flash (渠道7) ✅已实测**, 质量优于免费 (coding 端点) |
| 多音色配音 | Edge-TTS (渠道0) | — (可扩 Azure/OpenAI) |
| 说话人分离 | 内置 built / ali_CAM (ModelScope) | pyannote (需 HF token) |
| 人声/背景分离 | uvr 本地 (--is_separate) | — |

付费 key/端点: `drama-tools/setup_glm.py --probe` 一键探活三端点 (cn / intl / **coding**)。当前 key 为 GLM Coding Plan 类型 ("glme key"): **翻译已打通并实测**; ASR/OCR 不在 Plan 内, 需标准产品充值。

## 上游改动 (fork diff, 提交在 git 历史)

均为 macOS 部署适配, darwin 条件排除非关键重依赖 (Linux/Windows 不受影响):

1. `pyproject.toml`: `pynini` 与 `WeTextProcessing` 标记 `sys_platform != 'darwin'`
   — 原因: pynini 2.1.6 无 macOS arm64 wheel, 源码构建需 OpenFst 且极慢;
   二者仅被 MOSS-TTS/孔子TTS 文本正则化使用, 主流程 (Edge-TTS/whisper) 不依赖。
2. `pyproject.toml`: `chatterbox-tts` 标记 `sys_platform != 'darwin'` (含 override 与 uv.sources)
   — 原因: 其依赖 resemble-perth 是 GitHub 直链源码包, 本机网络拉取反复 early EOF;
   chatterbox 是声音克隆 TTS 渠道, 主流程 (Edge-TTS) 不依赖, 代码内为懒加载。
3. `pyproject.toml`: torch/torchaudio 移除 darwin 的 pytorch.org 源路由 → 走默认镜像
   — 原因: pytorch.org 直链在本机网络仅 ~35KB/s; PyPI 同版本 arm64 CPU wheel 等价且镜像 2.2MB/s。
4. `cli.py`: tts/vtv 任务装载 params.json 的 `line_roles{行号:音色}` 实现无界面多角色配音
   — 原因: 上游多角色配音仅 GUI 接线 (fn_peiyinrole → 内存 dubbing_role/line_roles), CLI 无入口;
   补丁: tts_fun → app_cfg.dubbing_role + is_multi_role; vtv_fun → app_cfg.line_roles。
5. `_zhipuai.py` + `constants.py`: 智谱渠道端点可配置 (`zhipu_base_url`, 默认 bigmodel.cn 兼容上游,
   可切 api.z.ai) ; Zhipuai_Model 常量补 glm-5.3-flash / glm-5.3-flashx
   — 原因: 同一 key 双端点认证均通过, 充值侧决定可用端点; 上游模型列表缺失本任务要用的模型。

环境补丁 (重建 venv 后需重做, 见 .ai-dev/agents/ops.md):
- soundfile 软链: `mkdir -p .venv/lib/python3.10/site-packages/_soundfile_data && ln -sf /opt/homebrew/lib/libsndfile.dylib .venv/lib/python3.10/site-packages/_soundfile_data/libsndfile.dylib`

## 素材

- 实验短剧: `/Users/mac/Documents/reso/翻译用/第01集.mp4`、`第02集.mp4` (720x1280 竖屏, ~90s, 内嵌中文字幕 y≈0.59-0.71)

## 验证记录

见 `docs/verification.md`。
