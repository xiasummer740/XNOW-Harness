# deepseek-balance

Claude Code status line plugin — displays DeepSeek account balance when active model is DeepSeek.

## Entrypoints

- `utils/balance.ts` — Core module: fetches balance from `https://api.deepseek.com/user/balance` via `GET`, auth via `Authorization: Bearer` header using `DEEP_SEEK_API_KEY_FOR_BALANCE` env var. Exports `getBalance()`.
- `index.ts` — CLI script (shebang `#!/usr/bin/env node`). Reads JSON from stdin, checks `model.display_name`, and if it contains "deepseek" (case-insensitive), dynamically imports `getBalance()` and writes balance to stdout with `\r` (carriage return for statusline update).

## Commands

```bash
# Install deps
pnpm install

# Run (pipe fixture data)
cat test/fixtures/test-data-deepseek.json | node index.ts

# Run with fixtures for balance output
DEEP_SEEK_API_KEY_FOR_BALANCE=sk-xxx cat test/fixtures/test-data-deepseek.json | node index.ts

# Lint & format (Biome, no semicolons, double quotes)
pnpm biome check --write .
```

## Config

- **Biome**: space indent, `semicolons: "asNeeded"`, `quoteStyle: "double"`, organize imports on save.
- **ENV**: `DEEP_SEEK_API_KEY_FOR_BALANCE` required; `BASE_URL` optional (defaults to `https://api.deepseek.com`).
- **ESM**: `"type": "module"` in package.json. All imports use `.ts` extension (node runtime with ts support).

## Debugging

Logger writes to `/tmp/claude-statusline-debug.log` — check there if the statusline isn't showing.

## Claude Code integration

`.claude/settings.local.json` registers this as a status line command. If `node` path to the script is wrong, `.claude/settings.local.json` needs updating.

## Test fixtures

- `test/fixtures/test-data-deepseek.json` — model with "DeepSeek" name, triggers balance fetch
- `test/fixtures/test-data.json` — non-DeepSeek model, skips balance fetch
