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

## 凭证仓库

私有凭证仓库：`xiasummer740/credentials-vault`，按项目明文存储各类配置/密钥/密码。

### 使用规则（铁律）

- **祥哥说"存一下"时，必须确认项目名再存**，不盲猜、不擅作主张
- 确认流程：我说"当前在 xxx 项目，确认存到这里？" → 祥哥说"对" → 我再存
- 查凭证也一样，先确认再看
- 新项目首次存凭证时，自动追加到 `MAPPING.md` 和 README 索引

## 自动更新

- **每次会话开始时，自动拉取 XNOW-Harness 最新代码**：`git -C F:/summer/vs-code/XNOW-Harness pull`
- 确保当前电脑始终使用最新版本的工具箱

## 说明

XNOW-Harness 是 Claude Code 辅助工具箱，所有代码改完后自动同步到 GitHub。
