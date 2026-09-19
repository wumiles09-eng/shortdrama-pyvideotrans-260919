# AI Dev Team — 短剧翻译系统 (py videos)

本目录是本项目的 aidevteam 工作区:角色、技能、状态与提案。裁剪自 `~/Documents/project/auto trans/ai-dev-team` 方法论模板,按本项目特征精简。

## 项目特征 (决定团队配置)

- **领域**: 短剧(竖屏)视频翻译 — OCR 硬字幕提取、ASR 转录、字幕翻译、说话人分离、多音色配音
- **栈**: Python 3.10 × 2 个 uv 环境 (pyvideotrans 主系统 / drama-tools OCR 工具)、FFmpeg、ONNX 模型
- **外部依赖**: HuggingFace/ModelScope 模型下载 (需镜像)、ZAI GLM 付费 API (余额敏感)、GitHub (网络不稳)
- **安全红线**: API key 绝不入库; push 前密钥门禁强制执行
- **产物**: SRT/ASS 字幕、配音音轨、合成视频、验证记录

## 角色 (agents/)

| 角色 | 文件 | 职责 |
|------|------|------|
| @tl | agents/tl.md | 任务裁决、计划编排、验收 |
| @dev | agents/dev.md | 管线开发、上游 fork 维护、CLI 封装 |
| @qa | agents/qa.md | 端到端验证、字幕质量抽查、产物完整性 |
| @ops | agents/ops.md | 环境/镜像/模型下载、密钥管理、GitHub 门禁 |
| @drama | agents/drama.md | 短剧领域专家: 台词断句、译制腔、角色音色匹配 |

## 技能 (skills/)

| 技能 | 入口 | 用途 |
|------|------|------|
| drama-ocr-subtitle | skills/drama-ocr-subtitle/SKILL.md | 硬字幕 OCR 提取调参 (区域标定/相似度/去水印) |
| drama-stt-pipeline | skills/drama-stt-pipeline/SKILL.md | ASR+说话人分离+多音色配音全流程 |
| drama-glm-channels | skills/drama-glm-channels/SKILL.md | 智谱 GLM 渠道配置与排障 (余额/端点) |
| secret-gate | skills/secret-gate/SKILL.md | push 前密钥扫描门禁 |

安装到全局可调用: `ln -s "$PWD/.ai-dev/skills/<name>" ~/.agents/skills/<name>` (见 skills/README)

## 状态 (state/)

- `state/work-queue.md` — 当前任务队列与验收状态

## 工作流

1. 任务进入 `state/work-queue.md`
2. @tl 拆解 → @dev/@ops 执行 → @qa 验证 (证据落 `docs/verification.md`)
3. 变更走提案: 重大改动先写 `proposals/` (暂空,按需创建)
