---
description: Configure deepseek-balance-statusline as your statusline
allowed-tools: Bash, Read, Edit, AskUserQuestion
---

# deepseek-balance-statusline Setup

## Step 1: Detect Platform, Shell, and Runtime

Detect the platform:

**macOS/Linux**:

1. Get plugin path (sorted by dotted version):
   ```bash
   ls -d "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/plugins/cache/*/deepseek-balance-statusline/*/ 2>/dev/null | awk -F/ '{ print $(NF-1) "\t" $(0) }' | grep -E '^[0-9]+\.[0-9]+\.[0-9]+[[:space:]]' | sort -t. -k1,1n -k2,2n -k3,3n | tail -1 | cut -f2-
   ```
   If empty, the plugin is not installed. Ask the user to run `/plugin install deepseek-balance-statusline` first.

2. Check Node.js runtime:
   ```bash
   command -v node 2>/dev/null
   ```
   If empty, ask the user to install Node.js 22.18.0+ from https://nodejs.org/ (only this version and higher can run TypeScript files directly).

3. Determine source file:
   ```bash
   ls "${plugin_dir}"
   ```
   Look for `index.ts` in the plugin dir.

4. Detect shell config file:
   ```bash
   echo "$SHELL"
   ```
   - `/bin/zsh` → `~/.zshrc`
   - `/bin/bash` → `~/.bashrc` (Linux) or `~/.bash_profile` (macOS)

## Step 2: Check Current Configuration

Check if `DEEP_SEEK_API_KEY_FOR_BALANCE` is already set:

```bash
grep -q 'export DEEP_SEEK_API_KEY_FOR_BALANCE=' ~/.zshrc 2>/dev/null && echo "FOUND" || echo "NOT_FOUND"
```

If `FOUND`, ask the user if they want to update it or skip.

## Step 3: Ask for DeepSeek API Key

Use `AskUserQuestion`:
- header: "DeepSeek API Key"
- question: "Enter your DeepSeek API key (sk-...). You can get one at https://platform.deepseek.com/api_keys"
- free text input (required)

If the user doesn't have a key, direct them to https://platform.deepseek.com/api_keys and re-prompt.

## Step 4: Write Environment Variable

**If DEEP_SEEK_API_KEY_FOR_BALANCE was NOT found in shell config:**

Append to the detected shell config file (e.g. `~/.zshrc`):

```bash
echo '\n# DeepSeek balance statusline\nexport DEEP_SEEK_API_KEY_FOR_BALANCE="sk-xxx"' >> ~/.zshrc
```

Replace `sk-xxx` with the user's actual key. Use single quotes around the echo string to prevent shell expansion of `$`.

**If it was found and user wants to update:**

Replace the existing line:
```bash
sed -i '' 's|export DEEP_SEEK_API_KEY_FOR_BALANCE=.*|export DEEP_SEEK_API_KEY_FOR_BALANCE="sk-xxx"|' ~/.zshrc
```

Use the appropriate shell config path detected in Step 1.

**macOS note**: `sed -i ''` (empty extension) is required because BSD sed behaves differently from GNU sed. On Linux, use `sed -i` without the empty string argument.

## Step 5: Optional BASE_URL

Ask the user (optional):
- header: "Custom BASE_URL"
- question: "Custom API base URL? (default: https://api.deepseek.com, press Enter to skip)"
- free text (optional)

If provided, write to shell config:
```bash
echo '\nexport BASE_URL="https://custom-url.com"' >> ~/.zshrc
```

## Step 6: Write StatusLine Configuration

Read the existing settings file:

**macOS/Linux**:
```bash
cat "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/settings.json" 2>/dev/null || echo "NOT_FOUND"
```

**If file doesn't exist or has no statusLine**, construct the command.

The command should use `node` with the plugin's source file. The plugin directory was detected in Step 1 as `plugin_dir`. The source file is `index.ts`.

Generated command format:
```
node "${plugin_dir}index.ts"
```

Merge statusLine into settings:

```json
{
  "statusLine": {
    "type": "command",
    "command": "node \"${plugin_dir}index.ts\""
  }
}
```

Use the Read tool to load the existing file, merge, and write back. Preserve all existing settings.

## Step 7: Verify & Finish

1. **Test the command**:
   ```bash
   echo '{"model":{"display_name":"DeepSeek-V4-Flash"}}' | node "${plugin_dir}index.ts" 2>&1
   ```
   Expected output: nothing (no API key in this test environment) or a balance string.

2. **Ask the user to restart Claude Code** — the statusLine requires a full restart.

3. Use AskUserQuestion:
   - question: "Setup complete! After restarting Claude Code, switch to a DeepSeek model and the balance should appear in your status line. Is everything working?"
   - options: "Yes, it's working" / "No, something's wrong"

4. **If no**: Debug systematically:
   - Verify settings file was written correctly
   - Check the plugin path exists
   - Test the command manually with `2>&1` to capture errors
   - Check `/tmp/claude-statusline-debug.log` for errors
