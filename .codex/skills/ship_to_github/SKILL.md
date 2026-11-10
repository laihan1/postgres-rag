---
name: ship_to_github
description: 一键 push 到 GitHub
argument-hint: "<commit_message>"
---

执行以下步骤：
1. 运行 `git ls-files`，如果发现 `.env` 被追踪，停止并警告。
2. 运行 `git add .`
3. 运行 `git commit -m "$ARGUMENTS"`
4. 运行 `git push`
5. 报告结果