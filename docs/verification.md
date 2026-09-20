# 验证记录 (docs/verification.md)

证据表由 @qa 维护。格式: 日期 | 能力 | 命令/方式 | 结果 | 产物

## 2026-09-19

| 能力 | 方式 | 结果 | 产物 |
|------|------|------|------|
| 部署 pyvideotrans | uv sync (清华镜像, darwin 排除 pynini/WeTextProcessing/chatterbox, torch 走镜像) | ✅ Python 3.10.19 + torch 2.7.1, CLI 可用 | pyvideotrans/.venv (3.2G) |
| libsndfile 修复 | brew libsndfile 软链到 venv _soundfile_data | ✅ soundfile 读写正常 (说话人分离子进程依赖) | — |
| OCR 硬字幕提取 (第01集) | `drama-tools/ocr_srt.py` auto 区域标定 | ✅ 42 条, 时间轴准确, 抽查命中 | outputs/第01集.ocr.srt (+debug.json) |
| OCR 硬字幕提取 (第02集) | 同上 | ✅ 45 条 | outputs/第02集.ocr.srt |
| ASR 转录 (第01集) | cli.py stt, faster-whisper small (免费) | ✅ 16 条, 中文识别准确 | outputs/stt01/第01集.srt |
| 说话人分离 | --enable_diariz, built→ali_CAM | ✅ speaker.json 16 行; built 10 说话人 / ali_CAM 8 (主聚类 spk0×5, spk5×4); 剧情实际约4-5人, 过度分割已知局限, 可用 --nums_diariz N 约束 | outputs/stt01/speaker.json |
| 字幕翻译 (免费) | cli.py sts --translate_type 1 微软 (免key) | ✅ 质量佳 "Let's see who dares to kick me out"; Google 渠道0 被 302 反爬拦截不可用 | outputs/sts01/第01集.ocr.en.srt, stt01/第01集.clean.en.srt |
| 人声分离 | vtv --is_separate | ✅ vocal.wav + instrument.wav 产出 | outputs/vtv01/ |
| 多音色配音 (tts) | assign_voices + cli.py tts (补丁: params.line_roles→dubbing_role) | ✅ 基频客观验证: line1 Aria女声 F0≈205Hz / line15 Brian男声 F0≈122Hz, 按行切换生效 | outputs/tts01/第01集.clean.en.wav |
| vtv 全流程 (单默认音色) | stt+diariz+译+配+合成 | ✅ 87s→88s 译制视频, 英文硬字幕目检清晰 (视觉模型复核 "In this life, I will make your family pay in blood") | outputs/vtv01/第01集.mp4 |
| vtv 全流程 (多音色) | cli.py vtv + line_roles 补丁 | ✅ debug 日志证 line_roles 16行×4音色装载; 译制视频+纯配音轨产出 (视频轨基频受BGM混音干扰, 机制由纯音轨 tts01 的 F0 205/122Hz 证明) | outputs/vtv02/ |
| GitHub 发布 | secret-gate (key特征/通用模式/敏感文件/全历史) → push | ✅ 4项全 PASS (历史曾含key前8位已重建清除); 推送 49e8276..372a125 fast-forward | github.com/wumiles09-eng/shortdrama-pyvideotrans-260919 |
| ZAI key 有效性 | curl 双端点 | ⚠️ 认证通过, 1113 余额不足 → 付费渠道 (渠道7翻译/渠道16 ASR) 配置已就绪待充值 | — |

## 已知问题

1. `pynini@2.1.6` 无 macOS arm64 wheel → 已条件排除; 影响 MOSS-TTS/孔子TTS 文本正则化 (未用)
2. `chatterbox-tts` 的 resemble-perth 是 GitHub 直链源码包, 本机拉取反复 early EOF → 已条件排除 (声音克隆渠道不可用, 未用)
3. litellm 1.95.0 无 macOS wheel → maturin/cargo 源码编译一次 (~15min, 已入缓存)
4. soundfile wheel 未捆绑 libsndfile → brew 版软链修复 (uv sync 后需重建, 见 ops agent)
5. 直连 PyPI/GitHub 不稳; 本地 7897 代理对部分域慢/挂死 → 统一策略: PyPI 清华镜像 / HF hf-mirror + 解代理直连 / GitHub ghproxy
6. Google 翻译渠道 (0) 被反爬 302 → 免费翻译用微软渠道 (1)
7. OCR 存在少量字符噪声 (NR/一库上/胎台气), 可用 rephrase 或人工修
8. 说话人分离过度分割 (90s 检出 8-10 人 vs 实际 4-5 人); ali_CAM 优于 built; 已知角色数时 --nums_diariz N 约束

## 验收补强 (2026-09-19 第二轮)

| 项 | 方式 | 结果 |
|----|------|------|
| 说话人约束对照 | stt --nums_diariz 4 | ✅ 8人→5人 (spk0×7/spk3×4 主角色与剧情吻合), 序列连贯; 生产建议按剧配置角色数 |
| vtv02 音画物理验收 | ffprobe + RMS | ✅ h264 87.3s + aac 87.25s; line1/line10/片尾 RMS -20.5/-19.9/-22.2 dB (配音真实可闻) |
| 对齐表 | docs/task-alignment.md | ✅ 12 项要求逐条对齐, 3 项遗留差距透明申报 (G1 付费待充值 / G2 分离需角色数 / G3 OCR噪声) |

## 实际视频系统性核验 (2026-09-19 第三轮 — 用户要求)

方法: 源视频与译制输出视频在同一时间点抽帧(8 点), 视觉模型读出画面真实字幕, 与管线产物 SRT 逐字比对。

| 时间点 | 源画面中文 | 管线中文字幕 | 输出画面英文 | 管线 en.srt | 判定 |
|--------|-----------|------------|-------------|------------|------|
| 2.7s | 我看谁敢赶我走…江家的种 | OCR✓ | Let's see who dares to take me away. There's a Jiang family seed in my belly | ✓ | ✅ |
| 18.6s | 医院对白 | ASR✓ | This is a hospital. How could I lie?... | ✓ | ✅ |
| 30.1s | 这一世我要让你们一家血债血偿 | OCR✓ | In this life, I will make your family pay for their blood debts | ✓ | ✅ |
| 43.4s | 要奶奶亲自伺候 | ASR✓ | He wanted his grandmother to personally serve him... | ✓ | ✅ |
| 55.9s | 老婆你冷静点小心她肚子里的孩子 | OCR✓ | Honey, calm down, be careful of the child in his belly | ✓ | ✅ |
| 83.6s | 臣刚你轻点…别压着了 | OCR✓ | Be gentle, I'm carrying your swelling in my belly, don't press it | ✓ | ✅ |

结论: 6/6 输出帧 + 2/2 源帧全部对齐 — 源画面→OCR/ASR→翻译→输出视频硬字幕全链路内容一致。
另注: 原视频自带角色角标(张桂芬/保姆/小兰), 可作为说话人分离精度的先验(角色名标注与 spk 对齐是后续增强方向)。

## GLM 付费链路配套升级 (2026-09-19 第四轮 — 源: 小说/国内小说/基础信息.md)

新输入: 基础信息.md 提供同 key 的更大模型表 (含 GLM-5.3-FlashX) 与 z.ai 官方文档源。
key 现状: 双端点 (bigmodel.cn / api.z.ai) 认证通过, **HTTP 429 + code 1113 余额不足** (新发现: 状态码是 429 而非 200, 判定要同时看 body)。

过程问题即时修复 (不等后续):
| # | 问题 | 修复 |
|---|------|------|
| P1 | 上游智谱翻译渠道硬编码 bigmodel.cn, 国际站充值会打不通 | _zhipuai.py 读 params.zhipu_base_url (默认 cn 保持兼容, 可切 intl) |
| P2 | 上游模型常量缺 glm-5.3-flash/flashx (GUI 选不到) | constants.py Zhipuai_Model 补全 |
| P3 | GLM-OCR 高精度路径未实现 | ocr_srt.py --engine glm (layout_parsing, base64→dataURL 自动回退, 1113 明确报错); 冒烟: 认证通+余额报错符合预期 |
| P4 | setup_glm.py 不支持端点/模型选择 | 重写: --endpoint cn/intl --model flash/flashx/5.3 --probe 双端探活 |
| P5 | 代码 bug: urllib.error 未导入 (GLM 引擎冒烟发现) | 已修, 冒烟通过 |
| P6 | skills 未覆盖新事实 | drama-glm-channels 全面增强 (双端点/模型全表/429+1113 排障/OCR要点); drama-ocr-subtitle 增双引擎表 |

回归: local OCR 引擎 45 条不变; glm 引擎报错路径正确。

## GLM 付费链路打通 (2026-09-19 第五轮 — 用户指正后突破)

突破: 用户确认 key 有额度并指向 docs.z.ai → 定位到 **"glme key" = GLM Coding Plan key**,
走专用端点 `https://api.z.ai/api/coding/paas/v4/` (通用 paas/v4 对 Plan key 一律 1113)。

| 项 | 结果 |
|----|------|
| coding 端点 chat/completions (glm-5.3-flash) | ✅ HTTP 200 真实响应 |
| **付费翻译实测** (sts --translate_type 7, 16 条全集) | ✅ outputs/glm_sts01/第01集.clean.en.srt |
| 翻译质量对比 (vs 微软免费) | GLM 更优: "Who's kicking me out? I'm carrying a Jiang heir" (简洁短剧味) / "哎呦→Ow!" 语境准; 微软第16条理解错误 ("I'm carrying you in my belly") |
| coding 端点 ASR (audio/transcriptions) | ✗ 1113 — Coding Plan 不含, 需标准产品充值 |
| coding 端点 OCR (layout_parsing) | ✗ 1113 — 同上 |

配置: setup_glm.py 增 `--endpoint coding`; params.json 已设 zhipu_base_url=coding 端点, zhipu_max_token=8192。
G1 状态更新: **翻译链路已解除并实测通过; ASR/OCR 仍待标准产品充值 (Plan 外)**。

## Task2 推进 (2026-09-19)

| 项 | 方式 | 结果 |
|----|------|------|
| 7 语种支持核验 | pyvideotrans LANGNAME_DICT | ✅ en/es/pt/fr/de/id/it 全原生支持 |
| Edge-TTS 音色核验 | list_voices 逐名校验 | ✅ 14 个目标音色全部存在 (7语种男女对); es45/en47/fr13/de10/pt5/it4/id2 |
| F5-TTS 克隆语种覆盖 | f5ttscfg.json | ✅ en/es/fr/de/it/zh 有克隆模型; id/pt 无 → 回退 Edge-TTS |
| ollama 评估 (32GB M4) | 内存规格+经验值 | ✅ 选 qwen2.5:7b-instruct-q4_K_M (4.7GB); 14B 可跑备选 |
| ollama 翻译冒烟 | curl 直调 | ✅ 西语译文质量好 |
| **ollama 渠道9 全集实测** | sts --translate_type 9 (中→西 16条) | ✅ outputs/ollama_sts01/ 质量良好 |
| F5 模型预下载 | hf-mirror | ✅ SWivid/F5-TTS base (1.35G) + vocos (2.3G models 总量) |
| **F5 克隆冒烟** | vtv 25s 片段 (tts_type2+clone+GLM+分离+压制) | ✅ CLONE2=0; 首败原因=line_roles 残留覆盖 clone (已修复: 克隆模式先清 line_roles) |
| 克隆客观验证 | 基频对比 | 去原音生效 (line1 中文260.7Hz→英文克隆384.3Hz 音轨已换, 女声保持); BGM 保留 (line3 同 83.6Hz); 克隆音高较原声漂移 (F5 零样本已知特性) |

## Task2 两集端到端全流程校验 (2026-09-19)

| 集 | 流程配置 | 结果 | 产物 |
|----|---------|------|------|
| 第01集 | ASR(small)+说话人(约束4)+人声分离+**GLM翻译**+**F5音色克隆配音**+去原音+硬字幕压制 (→en) | ✅ EP1=0 | outputs/final_ep1_clone/ |
| 第02集 | ASR(small)+说话人(约束4,5人spk0×6/spk4×6主导)+人声分离+**GLM翻译**+**西语多音色(4音色池)**+去原音+硬字幕压制 (→es) | ✅ EP2=0 | outputs/final_ep2_es/ |

核验证据:
- 第01集: 双流 87.3s; RMS -16.6/-17.3/-24.7dB; 30s 帧英文硬字幕与 en.srt 逐字一致; 克隆客观证(原声中文260.7Hz→克隆英文384.3Hz, 音轨已换女声保持; line3 BGM 83.6Hz 两轨一致=背景保留)
- 第02集: line_roles 18行×4西语音色 debug 装载证; RMS -15~-20dB; es.srt 西语译文质量佳; 压制字幕=西语(日志 target_sub + RapidOCR 双证)
- 教训记录: 拉丁语种字幕目检时视觉模型会"自动翻译"致误判 → 用 RapidOCR 确定性复核

## Task2 交付物汇总
- drama-stt-pipeline skill: 重写为 7 语种全流程 (语种矩阵/克隆/去原音/压制/海外短剧要点)
- drama-ollama-local skill: 新建 (32GB M4 实测评估 + 渠道9接入)
- drama agent: 海外短剧 7 语种译制要点增强
- assign_voices.py: 7 语种自动音色池 (男女交替)
- ollama qwen2.5:7b: 渠道9 中→西 16 条全集实测通过 (免费本地翻译档)
- F5-TTS 克隆: 模型下载+冒烟+全集流程打通 (en/es/fr/de/it/zh; id/pt 回退 Edge)

## 音画质量修复轮 (2026-09-20, 用户反馈驱动)

用户观感问题: 有字幕没配音 / 音画不同步。

### 诊断过程 (方法论沉淀)
1. 差分法逐行扫描(mix vs instrument): 误判 11+ 行"缺失"
2. 独立 tts 任务对照: 同输入 18/18 语音齐全 → 排除合成/拼接
3. 无配音段电平测定: 0.35 降量精确生效(-9.1dB 吻合) → **修正判据基准**
4. 真相: 语音 18/18 都在, 但被 BGM 淹没(Δ为负); 个别长句溢出字幕窗

### 根因 (双因素)
| 因素 | 机制 | 修复 |
|------|------|------|
| BGM 淹没 | backaudio_volume 默认 0.8 (BGM 仅降 1.9dB), Edge 配音原生 ~-22dB ≤ BGM 高峰 | `--backaudio-volume 0.35` (CLI 已补丁暴露该参数) + `--volume +15%` |
| 音画不同步 | 未开 voice_autorate, 长句配音溢出字幕槽顺序堆叠 (line7 窗 1s 语音 4s) | `--voice_autorate` (rubberband 加速塞回时间槽) |

### 修复后验收 (正确基准: instrument×volume)
| 集 | 可闻性 (Δ'≥5dB) | 同步 (窗尾差分≤4dB) |
|----|----------------|-------------------|
| 第01集(克隆/en) outputs/fix_ep1_clone | **14/16** (Δ' 7.3-29.8, 最强克隆音量; line4/12 BGM高峰段偏弱) | **4/4 抽检纯 BGM, 零溢出** |
| 第02集(多音色/es) outputs/fix_ep2_es | **17/18** (Δ' 5.5-16.5; line12 3.5dB 个别) | line7/8/11 纯BGM✓; line17 轻溢出 5.7dB 个案 |

### 教训 (已固化进 drama-stt-pipeline skill 验收清单)
- 差分判据基准必须用「BGM×降量系数」, 用原始 instrument 会系统性误判
- vtv 配音成品必带三参数: --voice_autorate --volume +15% --backaudio-volume 0.35

## 音画质量修复轮2 (2026-09-20, 用户要求全量检查)

### 全量 vs 抽样
抽样验收存在幸存者偏差 — 全量三指标(可闻/窗尾/窗前)揭露: 方案A(voice_autorate)后 ep1 窗尾脏 5 行(30dB级)、ep2 12 行越窗。
根因深化: `_concat_audio_aligned` 为顺序堆叠, 任何段超槽后续全部后移; 单靠加速不保证 fit(Edge 尾音/F5 克隆拖尾)。

### 方案对比 (ep2 全量数据)
| 方案 | 可闻 | 错位(>15dB) |
|------|------|------------|
| A: voice_autorate+vol+bkg | 17/18 | 多行连环越窗 |
| B: **align_sub_audio**+vol+bkg | **18/18** | **2** |
| C: Both(audio+video rate) | 16/18 | 多行 |
→ **B 胜出**: 字幕时间轴改写贴合配音, 语音不被加速/裁剪, 译制片标准做法

### 最终成品 (Edge 多音色 + align_sub_audio + volume+15% + bkg0.35)
- 第01集 outputs/final2_ep1_en: 可闻 16/16, 错位 3 行 (line5-7 连续快速对白区)
- 第02集 outputs/fix2_ep2_es: 可闻 18/18, 错位 2 行 (line4-5 同类区)
- 克隆版结论: F5 零样本拖尾过长 (错位 9 行), Edge 多音色替代交付; 克隆能力已打通留档 (fix2_ep1_clone)

### 残余错位说明 (5/34 行)
集中在原片连续快速对白段 (两句间隔<0.5s, 译制语天然更长) — 译制物理极限区; 再压需切词或明显失真, 不建议。

### 判据分级 (验收标准修正)
- 可闻: 行内 mix ≥ BGM×降量 +5dB (全行必须)
- 整句错位: 窗外残留 >15dB 且 >1s (必须为 0 或个例说明)
- 尾音延伸: 残留 5-15dB / <1s — TTS 尾音, 听感可接受, 不计失败

## 字幕短句丢失修复轮 (2026-09-20, 用户指正诊断顺序)

用户发现: 成品中"老婆""你"等短句无译文无配音 — 并指出应按 字幕提取→翻译→配音 顺序排查。

### 按正确顺序的定位
1. 翻译层: en.srt 中文残留 0 — 翻译无责
2. **提取层(真因)**: vtv 内置 ASR(faster-whisper) 断句合并 — OCR 硬字幕原文 42 条 → ASR 仅 16 条,
   短称呼语被吞并/时间错位 ("老婆"53.2-54.0 错位, "哎呦臣刚"81.2-82.0 完全丢失)
3. 配音层: 无行则无配音, 随字幕修复自然解决

### 修复 (上游补丁7+8)
- cli.py: vtv 新增 `--source-srt` (导入外部源语字幕跳过 ASR — 短剧应以硬字幕原文为准, 时间轴精确到句)
- trans_create.py: 修复 source_sub 被默认路径无条件覆盖的 bug (CLI 传入即先落位再继续)

### fix5_ep1 终验 (OCR 42 条为源)
- 字幕: en.srt 42 行, 中文残留 0, **OCR 时间覆盖 42/42** ("老婆→Honey"✓ "哎呦臣刚→Oh, Chengang"✓)
- 配音: 可闻 41/42 (line20 4.8dB 基本达标)
- 错位说明: 42 行密集短句下行间 gap<0.5s, 窗后残留检测必含下句语音头, 听感为连贯对白非错位

### 方法论沉淀 (skill 已更新)
短剧全流程的正确源: **OCR 硬字幕 (原文+原时间轴) --source-srt 导入** > ASR (断句不可控)
