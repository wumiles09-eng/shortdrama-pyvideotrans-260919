# 模型选型研究 + 四层归因综合评估 (2026-09-20)

任务: 调研 GitHub/HuggingFace 更合适模型; 综合 harness/agent/skill/模型 四层归因。

## 一、各环节模型研究结论 (含实测)

### 音色克隆 (最大痛点, 现用 F5-TTS zero-shot)
| 模型 | 特点 | 实测/社区结论 | 升级成本 |
|------|------|--------------|---------|
| **CosyVoice 2/3** (阿里, Apache-2.0) | 0.5B 轻量, 相似度最高, 流式, 多语种 | 克隆相似度标杆 | 渠道14 已内置, 但需本地起 API 服务 (/generate_audio) |
| **IndexTTS-2/2.5** (B站) | 3s 参考零样本, 情感/音色分离控制, zh/en | 内容保真+情感保真最强, 2.5 跨语种情感韵律 | 需外部服务, pyvideotrans 无内置 |
| **GPT-SoVITS** (60k star) | 5s 零样本弱(社区 ~2/5), **1min few-shot 微调质变** | 有 1 分钟干净样本时最优 | 渠道13 已内置, 需外部服务 |
| F5-TTS (现用) | zero-shot 漂移/拖尾 (本机实测 9/16 行错位) | 公认短板 | — |

### 说话人分离 (现用 CAM++)
- **pyannote 3.1 / community-1**: 2026 仍是开源 SOTA (DER 11-19%); community-1 全面超 3.1
- **短音频过度分割是通用难题** (聚类式数人固有), 社区解法 = 指定说话人数 (我们已做) + 调 clustering threshold (0.765) + min_cluster_size
- pyvideotrans 已支持 speaker_type=pyannote (需 HF token)
- 升级成本: 低 (配置切换); 收益: 中 (配合角色数约束后 CAM++ 已够用)

### 中文 ASR (现用 whisper-small)
**本机实测 (第01集)**:
| | whisper-small | FireRedASR (渠道5, Built-in) | OCR 原文 |
|--|--|--|--|
| 行数 | 16 | **13 (合并更激进)** | 42 (真值) |
| 错字 | 多 (把我走/姜家/胎台气) | **明显少 (赶我走/江家/撵出去全对)** | 基准 |
- **SenseVoice-Small** (234M): 中文 CER 减半、CPU 实时、带情感识别(短剧配音情绪参考价值高) — 需 FunASR 渠道扩展
- **FireRedASR2S**: ASR+VAD+LID+标点一体化 SOTA (CER 2.89%)
- **结论**: 断句合并是所有 ASR 通病 → **OCR 源方法论再次验证**; FireRedASR 定位=无硬字幕视频的识别档 (--recogn_type 5 零成本切换)

### OCR (现用 RapidOCR)
- **PaddleOCR-VL** (0.9B/1.5/1.6): 文档解析 SOTA (OmniDocBench 94.5-96.3%), 但硬字幕场景**传统 PP-OCRv5/v6 仍是标配**(速度+精确坐标); 社区共识=混合方案(传统检测+VLM识别难帧)
- 升级成本: 中; 收益: 低-中 (RapidOCR 实测 42/42 覆盖, 噪声少量) — 优先级低

### TTS 音色质量 (现用 Edge-TTS)
- **Kokoro-82M** (82M, Apache-2.0, 0.3s, CPU): 7 目标语种覆盖 **5 个** (en/es/fr/it/pt+zh; **缺 de/id**) — 渠道29 已内置
- 定位: Edge-TTS 的本地离线备选 (de/id 回退 Edge)

## 二、四层归因 (综合判定)

| 层 | 具体问题 | 判定 |
|----|---------|------|
| **模型层** (真实瓶颈) | F5 zero-shot 克隆漂移/拖尾 (社区公认弱); CAM++ 短音频过度分割 (通用难题); whisper 中文错字+断句合并; RapidOCR 小字噪声 | ✅ 主要瓶颈, 升级路径明确 (见路线图) |
| **harness 层** (上游集成缺陷, 已修 10 个补丁) | 顺序堆叠无 fit(补9); CLI do_diarize 未接线(补10); source_sub 覆盖(补8); backaudio_volume 未暴露(补6); CLI 无多角色入口(补4); pynini/chatterbox/torch darwin(补1-3); zhipu 端点(补5); --source-srt(补7) | ✅ 真实存在, 全部已修复固化 |
| **agent 层** (我的执行教训) | 抽样验收幸存者偏差 (用户纠正→全量); 诊断顺序错 (应字幕→翻译→配音, 用户纠正); fix5 单声交付未完成第二步; 多轮产物目录版本管理混乱 | ✅ 流程纪律问题, 已在验收清单固化 |
| **skill 层** (初版不完整) | 验收判据缺失(差分基准/分级标准后补); 参数推荐摇摆 (voice_autorate→align→voice_autorate+裁剪) 最终固化; OCR 优先源方法论后固化; 性别自动识别后补 | ✅ 随轮次全部固化进 skill |

**结论**: 当前质量问题是**四层叠加**: 模型层决定上限 (克隆/分离/ASR), harness 层放大模型缺陷 (堆叠/do_diarize), agent 层验收不严漏掉问题, skill 层未能提前预防。harness/agent/skill 已闭环, **下一轮收益在模型层**。

## 三、升级路线图 (按 收益/成本 排序)

| 优先级 | 动作 | 成本 | 预期收益 |
|--------|------|------|---------|
| P0 | 无硬字幕视频 ASR 换 FireRedASR (--recogn_type 5, 已实测) | 零 | 中文错字大幅下降 |
| P1 | **克隆换 CosyVoice2** (渠道14 + 本地 API 服务, 0.5B/32G M4 可跑) | 半天 | 克隆相似度/拖尾质变, 替代 F5 |
| P1 | SenseVoice-Small 接入 (FunASR 渠道扩展, 情绪标签反哺配音) | 半天 | 错字↓ + 情绪识别 |
| P2 | pyannote community-1 (HF token, speaker_type 切换) | 2h | 分离精度↑ (角色数约束已兜底) |
| P2 | Kokoro 本地 TTS (渠道29) de/id 外全语种 | 2h | 断网/离线配音 |
| P3 | PaddleOCR-VL 混合 OCR (难帧 VLM 识别) | 1天 | OCR 噪声↓ (现 42/42 覆盖已可用) |
| P3 | GPT-SoVITS few-shot (每角色 1min 干净样本微调) | 1天+素材 | 角色音色定制天花板 |

## 参考
- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) / [FireRedASR](https://github.com/FireRedTeam/FireRedASR) (arXiv 2501.14350)
- [SenseVoice-Small](https://huggingface.co/FunAudioLLM/SenseVoiceSmall) / FunASR vs Whisper benchmark (funasr.com)
- [PaddleOCR-VL](https://arxiv.org/html/2510.14528) / [videocr-PaddleOCR](https://github.com/knakamura13/videocr-PaddleOCR)
- [Kokoro-82M VOICES.md](https://huggingface.co/hexgrad/Kokoro-82M)
- IndexTTS 2.5 技术报告 (arXiv 2601.03888) / pyannote 2026 模型对比 (pyannote.ai)
