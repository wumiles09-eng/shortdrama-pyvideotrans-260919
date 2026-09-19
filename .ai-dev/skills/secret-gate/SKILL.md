---
name: secret-gate
description: push 前密钥/敏感信息门禁扫描。任何 git commit/push 到 GitHub 前必须执行。
---

# 密钥门禁 (push 前强制)

本仓库将推送到公开 GitHub (wumiles09-eng/shortdrama-pyvideotrans-260919),泄漏 key = 立即失守。

## 扫描清单 (全部通过才可 push)

```bash
cd "/Users/mac/Documents/project/py videos"

# 1) 已知 key 特征 (从 Obsidian api.md 取 key 前 8 位拼 pattern, 形如 <前8位>[0-9a-f]{24}; 本文件不落真实前缀)
#    KPREFIX=$(python3 -c "print(open('$HOME/Documents/Obsidian Vault/project/api/api.md').read().split('key:')[1].strip()[:8])"
KPREFIX="<从api.md现场取>"
git grep -nIE "${KPREFIX}[0-9a-f]{24}" -- . ':!pyvideotrans/uv.lock' || echo PASS-key
# 也扫历史
git log --all -p | grep -c "${KPREFIX}[0-9a-f]" || echo PASS-history

# 2) 通用 secret 模式
git grep -nIE "(api[_-]?key|secret|token|password|Bearer)[\"' ]*[:=][\"' ]*[A-Za-z0-9_\-\.]{16,}" -- \
  ':!*.lock' ':!pyvideotrans' || echo PASS-generic

# 3) 本地配置文件绝不被追踪
git ls-files | grep -E "cfg\.json|params\.json|\.env|api\.md|secret" && echo FAIL-tracked || echo PASS-tracked
```

## .gitignore 必须包含

```
pyvideotrans/videotrans/cfg.json
pyvideotrans/videotrans/params.json
pyvideotrans/.venv/
pyvideotrans/output/
pyvideotrans/models/
pyvideotrans/hf-downloads/
pyvideotrans/_video_out/
drama-tools/.venv/
outputs/*.mp4
*.wav
.DS_Store
```

## 规则

1. pyvideotrans 是上游 fork — 上游自带 .gitignore 不覆盖我们仓库根; 根仓库单独 init, pyvideotrans 以嵌套仓库/子目录形式管理
2. 提交前跑清单, 任一 FAIL → 修复 (git rm --cached + rotate key 若已泄漏) 后重扫
3. 大文件 (模型/视频/音频) 不入库
