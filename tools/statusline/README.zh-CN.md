# deepseek-balance-statusline

> 🌐 [English](README.md) | 中文文档

[Claude Code](https://claude.ai) 状态栏插件，当当前激活模型为 DeepSeek 时，在状态栏中显示你的 DeepSeek 账户余额和累计花费。

```ts
💰 ¥6.72 | 💸 ¥1.00 (Since 2026-05-31) | 🐳 DeepSeek-V4-Pro[1m]
```

仅在 DeepSeek 模型激活时显示，非 DeepSeek 模型不会显示。

## 展示原则

信息干净 & 不打扰原则：

1. 非 DeepSeek 模型不展示任何信息。
1. 已有信息不重复展示：项目所在目录不展示、git 分支不展示、时间不展示，这些是 Terminal 或其他工具应该展示的。
2. 只在恰当时机展示模型名：
  - 首次打开 Claude Code 不展示，因为 Claude Code 会展示。
  - 切换模型方展示

性能原则

- 非 DeepSeek 模型性能应该无损：所有操作包括请求、计算、渲染、甚至函数的导入都是 Lazy import。**渐进式披露**

## 安装

在 Claude Code 实例中运行以下命令：

**第一步：添加市场源**

```sh
claude plugin marketplace add legend80s/deepseek-balance-statusline
```

**第二步：安装插件**

```sh
claude plugin install deepseek-balance-statusline
```

之后启动 `claude`：

```sh
claude
```

**第三步：配置状态栏**

```sh
/deepseek-balance-statusline:setup
```

> 如果卡在这一步，可参考手动安装”第三步：配置状态栏“

完成！重启 Claude Code 加载新的状态栏配置，之后使用 DeepSeek 模型时余额就会显示。

---

## 手动安装

如果希望手动配置（或插件安装在你的环境中不适用）：

**第一步：克隆仓库**

```sh
git clone https://github.com/legend80s/deepseek-balance-statusline
cd deepseek-balance-statusline
```

**第二步：设置 API 密钥**

将以下内容添加到 shell 配置文件中（`~/.bashrc`、`~/.bash_profile` 或 `~/.zshrc`）：

```sh
export DEEP_SEEK_API_KEY_FOR_BALANCE="sk-xxx"
```

将 `sk-xxx` 替换为你的 DeepSeek API 密钥。可在 https://platform.deepseek.com/api_keys 获取。

可选的自定义 API 地址：

```sh
export BASE_URL="https://api.deepseek.com"
```

然后重新加载 shell 配置：

```sh
source ~/.bashrc
```

**第三步：配置状态栏**

将 `statusLine` 字段添加到 `~/.claude/settings.json`：

```json
{
  "statusLine": {
    "type": "command",
    "command": "node \"/path/to/deepseek-balance-statusline/index.ts\""
  }
}
```

将 `/path/to/` 替换为克隆仓库的实际路径。

> **Windows + Git Bash 用户**：使用正斜杠路径，例如 `/c/Users/yourname/projects/deepseek-balance-statusline/index.ts`。

**第四步：测试**

```sh
echo '{"model":{"display_name":"DeepSeek-V4-Flash"}}' | node index.ts
```

如果 API 密钥设置正确，你应该会看到类似以下的余额和花费输出：

```ts
🐳 💰 Balance ¥6.27 | Spent ¥0.00 (Since 2026-05-31)
```

**第五步：重启 Claude Code**

重启 Claude Code 使状态栏生效。

---

## 功能说明

当当前激活的模型名称包含 "DeepSeek" 时，插件会从 DeepSeek API 获取你的账户余额，并显示当前余额和累计花费：

```
🐳 💰 Balance ¥6.72 | Spent ¥1.00 (Since 2026-05-31)
```

`Spent` 通过持久化到 `~/.deepseek-balance/state.json` 实现跨进程累计，只增不减，充值也不会重置。

显示内容大约每 300ms 更新一次。如果余额获取失败（例如网络错误），则不会显示任何内容，避免干扰。

## 工作原理

```
Claude Code → stdin JSON → deepseek-balance-statusline → stdout → 显示在终端
```

1. Claude Code 每 ~300ms 通过 stdin 向插件发送一个 JSON 状态负载
2. 插件检查 `model.display_name` 是否包含 "deepseek"（不区分大小写）
3. 如果是，则使用你的 API 密钥调用 `GET https://api.deepseek.com/user/balance`
4. 读取 `~/.deepseek-balance/state.json` 追踪跨进程的累计花费：
   - **首次运行**：记录当前余额作为基线，写入 `state.json`
   - **后续运行**：计算 `consumption = max(0, previousBalance - currentBalance)`，累加到 `cumulativeSpent`，然后写回
   - **充值检测**：若 `currentBalance > previousBalance`，consumption 为 0，花费不会减少
5. 结果以 `\r`（回车符）写入 stdout，实现原地更新
6. 如果模型切换为非 DeepSeek，状态栏会清除

> 状态文件：`~/.deepseek-balance/state.json` — 存储 `{ cumulativeSpent, lastBalance, since }`。可安全删除，下次运行会自动创建新的基线。

## 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `DEEP_SEEK_API_KEY_FOR_BALANCE` | 是 | — | 具有余额查询权限的 DeepSeek API 密钥 |
| `BASE_URL` | 否 | `https://api.deepseek.com` | 自定义 API 地址（例如用于代理） |

## 环境要求

- Claude Code
- Node.js 22.18.0+ 因为只有这个版本及以上才能直接运行 TypeScript 文件
- DeepSeek API 密钥，获取地址：https://platform.deepseek.com/api_keys

## 调试

日志写入 `/tmp/claude-statusline-debug.log`：

```bash
tail -f /tmp/claude-statusline-debug.log
```

## 开发

```bash
git clone https://github.com/legend80s/deepseek-balance-statusline
cd deepseek-balance-statusline
pnpm install

# 使用测试数据测试
cat test/fixtures/test-data-deepseek.json | node index.ts

# 使用实际余额测试
DEEP_SEEK_API_KEY_FOR_BALANCE=sk-xxx cat test/fixtures/test-data-deepseek.json | node index.ts

# 代码检查与格式化
pnpm biome check --write .
```

## 许可证

MIT
