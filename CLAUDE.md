# XNOW-Harness — Claude Code 项目配置

## 分支规范

- 所有项目统一使用 `main` 作为默认分支
- 禁止创建或使用 `master` 分支
- 新仓库 init 后立即设 `git branch -m main`
- 存量 `master` 分支逐步迁移到 `main` 后删除

## 核心命令

```bash
xnow balance        # 查 DeepSeek 余额
xnow status         # 项目状态
xnow sync "msg"     # 提交 + 推送
xnow release patch  # 发布版本
xnow help           # 帮助
```

## 说明

XNOW-Harness 是 Claude Code 辅助工具箱，所有代码改完后自动同步到 GitHub。
