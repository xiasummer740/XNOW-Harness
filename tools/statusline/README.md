# deepseek-balance-statusline

> 🌐 English | [中文文档](README.zh-CN.md)

A [Claude Code](https://claude.ai) plugin that shows your DeepSeek account balance and cumulative spending in the status line when the active model is DeepSeek.

```ts
🐳 💰 Balance ¥6.72 | Spent ¥1.00 (Since 2026-05-31)
```

Only appears when a DeepSeek model is active. Non-DeepSeek models show nothing.

## Display Principles

**Non-intrusive & Clean**

1. No info for non-DeepSeek models.
2. No duplicate info: directory, Git branch, and time are terminal's job.
3. Show model name only when switching models (not on first launch, as Claude Code already does).

**Performance**

No overhead for non-DeepSeek models: lazy import for all operations (requests, computation, rendering, function imports). **Progressive disclosure**

## Install

Inside a Claude Code instance, run the following commands:

**Step 1: Add the marketplace**

```sh
claude plugin marketplace add legend80s/deepseek-balance-statusline
```

**Step 2: Install the plugin**

```sh
claude plugin install deepseek-balance-statusline
```

After that, launch `claude`:

```sh
claude
```

**Step 3: Configure the statusline**

```sh
/deepseek-balance-statusline:setup
```

> If stuck here, follow Manual Installation **Step 3: Configure the status line**

Done! Restart Claude Code to load the new statusLine config, then the balance will appear when you use a DeepSeek model.

---

## Manual Installation

If you prefer to set up manually (or the plugin install doesn't work for your environment):

**Step 1: Clone the repository**

```sh
git clone https://github.com/legend80s/deepseek-balance-statusline
cd deepseek-balance-statusline
```

**Step 2: Set the API key**

Add the following to your shell config file (`~/.bashrc`, `~/.bash_profile`, or `~/.zshrc`):

```sh
export DEEP_SEEK_API_KEY_FOR_BALANCE="sk-xxx"
```

Replace `sk-xxx` with your DeepSeek API key. Get one at <https://platform.deepseek.com/api_keys>.

Optionally set a custom API base URL:

```sh
export BASE_URL="https://api.deepseek.com"
```

Then reload your shell config:

```sh
source ~/.bashrc
```

**Step 3: Configure the status line**

Add the `statusLine` field to `~/.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "node \"/path/to/deepseek-balance-statusline/index.ts\""
  }
}
```

Replace `/path/to/` with the actual path to the cloned repository.

> **Windows + Git Bash users**: Use forward-slash paths, e.g. `/c/Users/yourname/projects/deepseek-balance-statusline/index.ts`.

**Step 4: Test it**

```sh
echo '{"model":{"display_name":"DeepSeek-V4-Flash[1m]"}}' | node index.ts
```

If the API key is set correctly, you should see the balance and spending output like this:

```ts
🐳 💰 Balance ¥6.27 | Spent ¥0.00 (Since 2026-05-31)
```

**Step 5: Restart Claude Code**

Restart Claude Code for the status line to take effect.

---

## What it does

When your active model contains "DeepSeek" in its name, the plugin fetches your account balance from the DeepSeek API and displays both the current balance and cumulative spending in the status line:

```ts
🐳 💰 Balance ¥6.72 | Spent ¥1.00 (Since 2026-05-31)
```

The `Spent` value tracks total consumption across sessions by persisting state to `~/.deepseek-balance/state.json`. It only goes up — recharges don't reset it.

The display updates every ~300ms with the latest balance. If the balance fetch fails (e.g. network error), nothing is shown to avoid clutter.

## How it works

```ts
Claude Code → stdin JSON → deepseek-balance-statusline → stdout → displayed in terminal
```

1. Claude Code sends a JSON status payload to the plugin via stdin every ~300ms
2. The plugin checks if `model.display_name` contains "deepseek" (case-insensitive)
3. If yes, it calls `GET https://api.deepseek.com/user/balance` with your API key
4. It reads `~/.deepseek-balance/state.json` to track cumulative spending across processes:
   - **First run**: records current balance as the baseline, writes `state.json`
   - **Subsequent runs**: computes `consumption = max(0, previousBalance - currentBalance)`, adds it to `cumulativeSpent`, then writes the updated state
   - **Recharge detected**: if `currentBalance > previousBalance`, consumption is 0 — spent never decreases
5. The result is written to stdout with `\r` (carriage return) to update in-place
6. If the model changes away from DeepSeek, the status line clears

> State file: `~/.deepseek-balance/state.json` — stores `{ cumulativeSpent, lastBalance, since }`. Safe to delete; a new baseline will be created on the next run.

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DEEP_SEEK_API_KEY_FOR_BALANCE` | Yes | — | DeepSeek API key with balance query permission |
| `BASE_URL` | No | `https://api.deepseek.com` | Custom API base URL (e.g. for proxy) |

## Requirements

- Claude Code
- **Node.js 22.18.0+** (only this version and higher can run TypeScript files directly).
- A DeepSeek API key from <https://platform.deepseek.com/api_keys>

## Debugging

Logs are written to `/tmp/claude-statusline-debug.log`:

```bash
tail -f /tmp/claude-statusline-debug.log
```

## Development

```bash
git clone https://github.com/legend80s/deepseek-balance-statusline
cd deepseek-balance-statusline
pnpm install

# Test with fixtures
cat test/fixtures/test-data-deepseek.json | node index.ts

# Test with actual balance
DEEP_SEEK_API_KEY_FOR_BALANCE=sk-xxx cat test/fixtures/test-data-deepseek.json | node index.ts

# Lint & format
pnpm biome check --write .
```

## License

MIT
