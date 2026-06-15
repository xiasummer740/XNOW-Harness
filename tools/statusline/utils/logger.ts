import fs from "node:fs/promises"
import os from "node:os"
import { join } from "node:path"

const LOG_FILE = join(os.tmpdir(), "claude-statusline-debug.log")

// Leverage CC's every call of statusline API is a new node.js process `node xx.ts`
let isFirstCall = true

export function log(...messages: (string | number)[]): Promise<void> {
  const msg = messages.join(" ")
  const line = `${new Date().toISOString()} - ${msg}\n`

  // Only save the latest batch of logs to avoid accumulative logs to make log file bigger and bigger
  if (isFirstCall) {
    isFirstCall = false
    return fs.writeFile(LOG_FILE, line)
  }
  return fs.appendFile(LOG_FILE, line)
}

if (import.meta.main) {
  console.log(LOG_FILE)
}
