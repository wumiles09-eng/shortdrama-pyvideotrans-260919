# @dev — 管线开发

## 职责

1. drama-tools 开发 (ocr_srt.py / assign_voices.py / 后续管线脚本)
2. pyvideotrans CLI 封装与排障; 改动上游必须最小化并记录到根 README「上游改动」
3. 新能力优先评估上游内置: diarization/line_roles/[spN] 标签机制等已有实现不重造

## 上游关键机制速查 (读码结论)

- `cli.py --task stt|tts|sts|vtv` — 无界面全流程
- `--enable_diariz --nums_diariz N` — 说话人分离 → speaker.json
- 字幕行内 `[spXXX n]` 前缀会被 `_stage_prepare` 自动提取为 speaker.json (无界面多角色的另一入口)
- 配音按行取音色: `_stage_dubbing` 读 `params.json` 的 `line_roles{行号:音色}`, 缺省 voice_role
- 翻译渠道 7=智谱(glm-5.3-flash 可填 zhipu_model); ASR 渠道 16=GLM-ASR-2512
- cfg.json/AppSettings 存渠道 key 之外的设置; params.json/AppParams 存 key 与运行参数

## 代码规范

- Python 3.10+; drama-tools 用自身 venv (`uv run`), 不 import pyvideotrans
- 每个工具 `--help` 自文档; stderr 打日志, stdout 只出产物路径
- 行为变更配最小自测 (如 ocr_srt 的 debug json 回放断言)
