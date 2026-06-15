import { colors } from "./console.ts"

export function render({
  model,
  currentBalance,
  currency,
  spent,
  since,
  showModel,
  cwd,
  contextPercent = 0,
  contextTokens = 0,
  contextTotal = 1000000,
}: {
  model: string
  currentBalance: string
  currency: string
  spent: number
  since: string
  showModel: boolean
  cwd?: string
  contextPercent?: number
  contextTokens?: number
  contextTotal?: number
}): string {
  const color = resolveColorByLevel(Number(currentBalance))
  const symbol = currency === "CNY" ? "¥" : currency === "USD" ? "$" : ""
  const modelTag = showModel ? ` | 🐳 ${model}` : ""
  const barStr = renderProgressBar(contextPercent, contextTokens, contextTotal)
  const line1 = `💰 ${color}${symbol}${currentBalance}${colors.reset} | 💸 ${colors.cyan}${symbol}${spent.toFixed(2)}${colors.reset} (Since ${since})${modelTag} ${barStr}`
  const line2 = cwd ? `\n${colors.dim}📂 ${cwd}${colors.reset} ${colors.bold}${colors.green}XNOW-Harness已启用${colors.reset}` : ""
  return `${line1}${line2}`
}

function renderProgressBar(percent: number, usedTokens: number, totalTokens: number): string {
  const barLen = 10
  const filled = Math.round((percent / 100) * barLen)
  const clampedFilled = Math.min(filled, barLen)

  let barColor: string
  if (percent >= 90) { barColor = colors.red }
  else if (percent >= 70) { barColor = colors.yellow }
  else if (percent >= 40) { barColor = colors.cyan }
  else { barColor = colors.green }

  const fmtTokens = formatTokens(usedTokens)
  const fmtTotal = formatTokens(totalTokens)
  const full = "█".repeat(clampedFilled)
  const empty = "░".repeat(barLen - clampedFilled)

  return `${barColor}${full}${colors.dim}${empty}${colors.reset} ${barColor}${percent}%${colors.reset} (${fmtTokens}/${fmtTotal})`
}

function formatTokens(tokens: number): string {
  if (tokens >= 1000000) { return `${(tokens / 1000000).toFixed(1)}M` }
  if (tokens >= 1000) { return `${Math.round(tokens / 1000)}k` }
  return String(tokens)
}

function resolveColorByLevel(total_balance: number): string {
  switch (true) {
    case total_balance < 1: { return colors.red }
    case total_balance < 6: { return colors.yellow }
    default: { return colors.green }
  }
}
