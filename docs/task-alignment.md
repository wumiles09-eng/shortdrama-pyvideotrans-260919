# Task 1 对齐验收表 (2026-09-19)

任务源: `~/Documents/Obsidian Vault/project/auto transe/翻译系统2/task py.md`
流程: 读取任务 → 理解分解 → 完整计划 → 执行 → 检查验收 → 对齐(本表)

## 逐条对齐

| 任务要求 | 交付 | 证据 | 判定 |
|---------|------|------|------|
| 1.1 下载并本地部署 pyvideotrans,适配为短剧翻译系统 | pyvideotrans 4.12 (49e8276) vendored + 4 项 macOS 补丁 + drama-tools 适配层 | pyvideotrans/.venv (torch 2.7.1, Python 3.10.19); README「上游改动」 | ✅ |
| 1.2.2-a 字幕识别(OCR)→字幕提取→落地 .srt | drama-tools/ocr_srt.py (RapidOCR 免费, auto 字幕带标定) | 第01集 42 条 / 第02集 45 条 (outputs/*.ocr.srt), 抽查命中, 时间轴准确 | ✅ |
| 1.2.2-b 字幕翻译 | 免费: 微软渠道(免key); 付费: 智谱 glm-5.3-flash 渠道7 已配置 | outputs/sts01/*.en.srt 质量佳; setup_glm.py 就绪 | ✅ (付费待余额, 见差距G1) |
| 1.2.2-c 多角色识别 | faster-whisper + ali_CAM 说话人分离 | speaker.json; 无约束 8 人 → **约束 nums_diariz=4 后 5 人**, 主说话人 spk0×7/spk3×4 与剧情吻合 (outputs/stt01_n4/) | ✅ |
| 1.2.2-d 音色识别、音色分离 | 人声/背景分离 (vtv --is_separate) + 说话人声纹区分 (diarization) | outputs/vtv01/{vocal,instrument}.wav | ✅ |
| 1.2.2-e 按角色多音色配音 | assign_voices + Edge-TTS + cli.py 多角色补丁 (line_roles) | 纯配音轨基频 205Hz(女)/122Hz(男) 按行切换; vtv02 debug 日志 16行×4音色装载 | ✅ |
| 1.2.3 实验短剧验证 | 第01集全流程 (OCR/ASR/分离/翻译/配音/vtv), 第02集 OCR | outputs/ 全产物; vtv 译制视频 87.3s h264+aac, 三时段 RMS -20~-22dB 配音可闻, 英文硬字幕目检清晰 | ✅ |
| 1.2.4 配置 aidevteam agents & skills | .ai-dev/ 5 角色 (tl/dev/qa/ops/drama) + 4 skills, 软链 ~/.agents/skills 可调用 | .ai-dev/ 目录; 软链列表 | ✅ |
| 1.2.5 模型先用免费开源,再用付费 | 免费链路 7 项全验证通过; 付费双端点探活+配置就绪 | docs/verification.md 证据表 | ✅/⚠️ 见 G1 |
| 1.3 项目目录 = py videos | 全部工作在该目录, git 仓已建 | 本仓库 | ✅ |
| 1.4 付费模型参考 api.md (glm-5.3-flash 翻译 / glm-asr 识别) | key 从 api.md 读取 (不硬编码); 翻译渠道7 + ASR 渠道16 接线确认 | curl 探活: 认证有效; setup_glm.py | ⚠️ G1 |
| 1.5.1 GitHub wumiles09-eng/shortdrama-pyvideotrans-260919 | 已推送 49e8276..6017c95 (fast-forward, 上游历史保留) | gh/GitHub 可查 | ✅ |
| 1.5.2 绝不放 key 上库, push 前严格门禁 | secret-gate 4 项扫描 (key特征/通用模式/敏感文件/全历史); 发现历史 key 前8位残留 → 重建历史清除后再推 | 本表下方门禁记录 | ✅ |

## 遗留差距 (透明申报)

| # | 差距 | 原因 | 解除条件 |
|---|------|------|---------|
| G1(部分解除) | ~~翻译未实测~~ 已通: glme key=Coding Plan → coding 端点, 16 条全集实测质量优于免费; ASR/OCR 不在 Plan 内仍 1113 | 标准产品 (bigmodel.cn/z.ai paas) 充值后: ASR `--recogn_type 16`、OCR `--engine glm` 即用 |
| G2 | 说话人分离需人工给角色数提示效果最佳 | 90s 强情绪短剧对无约束聚类不友好 (通用局限) | 已缓解: nums_diariz 约束后 5 人与剧情吻合; 建议生产流程中按剧配置角色数 |
| G3 | OCR 字符级噪声 (NR/一库上/胎台气 等少量) | 竖屏小字 + 艺术字体, RapidOCR 固有误差 | 可接 `--rephrase 1` (LLM 断句纠错, 需翻译渠道 key) 或人工抽查; 付费 GLM-OCR 可作高精度对照 (待 G1) |

## 验收门禁记录 (push 前)

- 工作区 key 特征: 0 处 ✅
- 全历史 key 特征: 0 处 (发现残留后已重建历史 + reflog expire + gc) ✅
- 通用 secret 模式: 无命中 ✅
- cfg.json/params.json/.env 追踪检查: 未追踪 (仅上游 voicejson/f5ttscfg.json 白名单) ✅
- 推送方式: fast-forward (49e8276..6017c95), 未 force, 上游历史完整 ✅

---

# Task 2 对齐验收表 (2026-09-19)

任务源: task py.md 第2节。

| 任务要求 | 交付 | 证据 | 判定 |
|---------|------|------|------|
| 2.1 完整流程: 字幕识别→提取→角色/音色识别→音色分离→音色克隆→去除原音→字幕翻译→译文配音(按角色)→字幕压制 | 全链路打通并两集实测 | docs/verification.md「Task2 两集端到端」; 第01集克隆全流程 EP1=0, 第02集西语多音色全流程 EP2=0 | ✅ |
| 2.1.1 skill 增强, 适合海外短剧, 中/英原文→英西葡法德印尼意 7 语种 | drama-stt-pipeline 重写(7语种矩阵+海外短剧译制要点), drama agent 增强(称谓/文化词/句长), assign_voices 7语种音色池 | .ai-dev/skills/, agents/drama.md; 14个Edge音色逐名验实; pyvideotrans 7语种原生支持核验 | ✅ |
| 2.2 免费模型借助本地 ollama, 按内存实际评估 (查 HF/GitHub) | 32GB M4 评估: qwen2.5:7b-instruct-q4_K_M (4.7GB) 首选, 14B 备选; ASR/分离/TTS 不迁 ollama 的理由; 渠道9接入+中→西16条全集实测 | .ai-dev/skills/drama-ollama-local; outputs/ollama_sts01/ | ✅ |
| 2.3 两视频完成整流程校验 | 第01集(克隆/en) + 第02集(多音色/es), 物理指标+目检+OCR+debug日志多证 | outputs/final_ep1_clone/, outputs/final_ep2_es/ | ✅ |

遗留 (继承 task1):
- G1-剩余: GLM-ASR/GLM-OCR 需标准产品充值 (Coding Plan 只含 chat); F5 克隆 id/pt 无模型→Edge 回退 (skill 已写明)
- 克隆音高漂移 (F5 零样本特性): 质量中等, 追求高保真可后续接 CosyVoice/GPT-SoVITS
