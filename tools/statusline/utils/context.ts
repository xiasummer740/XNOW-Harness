import { readFileSync, existsSync, globSync } from "node:fs"
import { join } from "node:path"
import { homedir } from "node:os"

const CONTEXT_WINDOW = 1000000 // DeepSeek V4 Flash context window (1M tokens)

interface ContextUsage {
  percent: number
  used: number
  total: number
}

/**
 * Get the current context usage by reading the session JSONL file.
 * Uses CLAUDE_CODE_SESSION_ID env var to locate the session file.
 * Fast: only parses usage fields, skips full content.
 */
export function getContextUsage(): ContextUsage {
  try {
    const sessionId = process.env.CLAUDE_CODE_SESSION_ID

    if (!sessionId) {
      return { percent: 0, used: 0, total: CONTEXT_WINDOW }
    }

    // Find the session file in the Claude projects directory
    const projectsDir = join(homedir(), ".claude", "projects")
    if (!existsSync(projectsDir)) {
      return { percent: 0, used: 0, total: CONTEXT_WINDOW }
    }

    // Search for the session file across all project dirs
    const sessionFile = findSessionFile(projectsDir, sessionId)
    if (!sessionFile || !existsSync(sessionFile)) {
      return { percent: 0, used: 0, total: CONTEXT_WINDOW }
    }

    const totalTokens = parseTokens(sessionFile)
    const percent = Math.min(Math.round((totalTokens / CONTEXT_WINDOW) * 100), 100)

    return { percent, used: totalTokens, total: CONTEXT_WINDOW }
  } catch {
    return { percent: 0, used: 0, total: CONTEXT_WINDOW }
  }
}

function findSessionFile(projectsDir: string, sessionId: string): string | null {
  try {
    // Search across all project subdirectories
    const pattern = join(projectsDir, "*", `${sessionId}.jsonl`)
    const files = globSync(pattern)
    return files.length > 0 ? files[0] : null
  } catch {
    return null
  }
}

function parseTokens(filePath: string): number {
  try {
    const content = readFileSync(filePath, "utf-8")
    let lastInput = 0
    let lastCacheRead = 0

    for (const line of content.split("\n")) {
      if (!line || !line.includes('"usage"')) continue
      try {
        const obj = JSON.parse(line)
        const msg = obj?.message
        if (!msg) continue
        const usage = msg.usage
        if (!usage || typeof usage !== "object") continue

        const inp = usage.input_tokens || 0
        const cacheRead = usage.cache_read_input_tokens || 0

        if (inp > 0) lastInput = inp
        if (cacheRead > 0) lastCacheRead = cacheRead
      } catch {
        // skip parse errors
      }
    }

    // Use the last message's total (input + cache_read) as the current context size
    return lastInput + lastCacheRead
  } catch {
    return 0
  }
}
