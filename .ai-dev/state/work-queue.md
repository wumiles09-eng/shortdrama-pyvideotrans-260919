# 工作队列

| # | 任务 | 负责 | 状态 | 验收 |
|---|------|------|------|------|
| T1 | 部署 pyvideotrans (uv, macOS patch×4 + libsndfile) | @ops | ✅ 2026-09-19 | torch 2.7.1 导入 OK, CLI 正常 |
| T2 | OCR 硬字幕提取→SRT | @dev | ✅ 2026-09-19 | 第01集 42 条/第02集 45 条, 抽查通过 |
| T3 | ASR 转录 (faster-whisper 免费) | @dev | ✅ 2026-09-19 | 16 条, 中文准确 |
| T4 | 说话人分离 (ali_CAM) | @dev | ✅ 2026-09-19 | speaker.json; 过度分割已记录 (8 vs 实际~5) |
| T5 | 字幕翻译 (微软免费) | @dev | ✅ 2026-09-19 | 抽查质量佳; Google 被反爬不可用已记录 |
| T6 | 智谱 glm-5.3-flash 翻译接入 | @ops | ✅ 配置就绪 ⏳ 余额 | key 有效, 1113 待充值; drama-tools/setup_glm.py 一键配置 |
| T7 | 人声分离 + 多音色配音 (Edge-TTS) | @dev | ✅ 2026-09-19 | vocal/instrument.wav; 基频 205/122Hz 证多音色 |
| T8 | GLM-ASR-2512 识别接入 | @ops | ✅ 配置就绪 ⏳ 余额 | 渠道16, 同 zhipu_key |
| T9 | aidevteam 配置 | @tl | ✅ 2026-09-19 | 5 agents + 4 skills 软链可调 |
| T10 | vtv 全流程多音色终验 | @dev | ⏳ vtv02 运行中 | 译制视频多音色听感 |
| T11 | git 终提 + 密钥门禁 + GitHub 推送 | @ops | ⏳ | secret-gate 全 PASS |
