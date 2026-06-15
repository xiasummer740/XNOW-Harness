import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs"
import { homedir } from "node:os"
import { join } from "node:path"

interface BalanceState {
  cumulativeSpent: number
  lastBalance: number
  _lastBalance: number
  since: string
  lastModel?: string
}

const STATE_DIR = join(homedir(), ".deepseek-balance")
const STATE_PATH = join(STATE_DIR, "state.json")

export function readState(): BalanceState | null {
  try {
    if (!existsSync(STATE_PATH)) return null
    return JSON.parse(readFileSync(STATE_PATH, "utf-8"))
  } catch {
    return null
  }
}

export function writeState(state: BalanceState): void {
  if (!existsSync(STATE_DIR)) mkdirSync(STATE_DIR, { recursive: true })
  writeFileSync(STATE_PATH, JSON.stringify(state, null, 2))
}
