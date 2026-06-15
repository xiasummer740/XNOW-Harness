# Claude Code 技能清单（参考备份）

这是 Claude Code 原有的技能列表，XNOW-Harness 不直接支持这些技能，
但核心工作流程已内置在工作流模式中。

## 核心工作流（已内置在 XNOW-Harness）

| 技能 | XNOW-Harness 对应 |
|------|------------------|
| brainstorming | 工作流 💡 方案阶段 |
| writing-plans | 工作流 📋 计划阶段 |
| subagent-driven-dev | 工作流 ⚡ 执行阶段 + delegate 工具 |
| code-review | 工作流 🔍 审查阶段 |
| verification-before-completion | 工作流 ✅ 验证阶段 |
| systematic-debugging | `/skill debugging` 命令 |

## Claude Code 专属技能（XNOW-Harness 不适用）

这些技能依赖 Claude Code 的生态，XNOW-Harness 不兼容：

- firecrawl 全家桶（搜索/抓取/爬取）
- browser-use（浏览器自动化）
- deep-research（多源调研）
- thread-manager（会话线程管理）
- update-config（settings.json 配置）
- fewer-permission-prompts（权限弹窗）
- keybindings-help（快捷键）
- hookify（Hooks 配置）
- claude-api（Claude API 参考）

## Claude Code 已安装的插件

```
enabledPlugins:
  hookify@claude-plugins-official
  pr-review-toolkit@claude-plugins-official
  superpowers@superpowers-marketplace
  typescript-lsp@claude-plugins-official
  document-skills@anthropic-agent-skills
  skill-creator@claude-plugins-official
  example-skills@anthropic-agent-skills
  gopls-lsp@claude-plugins-official
```

## Claude Code 额外市场

```
superpowers-marketplace → obra/superpowers-marketplace
anthropic-agent-skills  → anthropics/skills
```

---

> 恢复方法：`gh repo clone` 相关仓库后，在 settings.json 中重新启用插件。
