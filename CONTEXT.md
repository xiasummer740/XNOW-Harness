# XNOW-Harness — 领域语言与架构上下文

> Claude Code 辅助工具箱。提供 `xnow` CLI 命令用于项目初始化、代码同步、版本发布、余额查询等。

---

## 核心概念

### 命令 / Command
`xnow` CLI 的子命令，如 `sync`、`release`、`status`、`init`、`balance`。
_Avoid_: 操作、功能

### 同步 / Sync
将本地代码提交并推送到 GitHub。分为项目同步（`xnow sync`）和环境同步（`xnow sync-env`）。
- **项目同步**：提交当前项目代码到对应 GitHub 仓库
- **环境同步**：同步 `~/.claude/` 配置到 xiangge-env 仓库

### 版本发布 / Release
通过 `xnow release <patch|minor|major>` 自动打 tag 并创建 GitHub Release。
_Avoid_: 发版、部署

### xiagnge-env
存储 Claude 配置（CLAUDE.md、skills、quality、permissions）的私有仓库，多设备共享。
_Avoid_: 环境仓库、配置库

### 权限 / Permission
settings.json 中的白名单条目，控制 Claude 可执行的工具和命令。

---

## 架构决策 (ADRs)

### ADR-001: Python CLI + Git 操作
**决策：** 使用 Python 实现 CLI，通过 subprocess 调用 git 命令。
**原因：** 跨平台兼容，不需要 Node.js 环境即可运行。

### ADR-002: xiangge-env 独立仓库
**决策：** Claude 配置单独存放在 xiangge-env 仓库，不混入项目代码。
**原因：** 配置变更独立于项目开发，多设备同步更灵活。

---

## 目录结构

```
xnow_harness/       # 核心模块
scripts/            # 辅助脚本
config/             # 配置模板
tools/              # 工具函数
docs/               # 文档
```
