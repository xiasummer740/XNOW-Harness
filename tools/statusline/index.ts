#!/usr/bin/env node

import plugin from "./.claude-plugin/plugin.json" with { type: "json" }
import { colors } from "./utils/console.ts"
import { log } from "./utils/logger.ts"

log(`BEGIN`)
log(`${plugin.name}@${plugin.version}`)

let input = ""

process.stdin.on("data", (chunk) => {
  input += chunk
})

process.stdin.on("end", async () => {
  try {
    const data = JSON.parse(input)
    const model: string | undefined = data.model?.display_name
    log(`model: ${model}`)

    // biome-ignore lint/complexity/useOptionalChain: verbose but intent more obvious
    if (model && model.toLowerCase().includes("deepseek")) {
      log(`DeepSeek 💰 ¥ LOADING`)
      // Lazy loading for zero performance impact on non-deep-seek models.
      const { render } = await import("./utils/render.ts")
      const { getBalance } = await import("./utils/balance.ts")
      const { readState, writeState } = await import("./utils/state.ts")
      const { getContextUsage } = await import("./utils/context.ts")

      const balanceInfo = await getBalance()
      const currentBalance = Number(balanceInfo.total_balance)

      let spent: number
      let since: string

      const state = readState()
      if (!state) {
        since = new Date().toISOString().slice(0, 10)
        writeState({
          cumulativeSpent: 0,
          lastBalance: currentBalance,
          _lastBalance: currentBalance,
          since,
          lastModel: model,
        })
        spent = 0
      } else {
        const consumption = Math.max(0, state.lastBalance - currentBalance)
        state.cumulativeSpent += consumption
        state._lastBalance = state.lastBalance
        state.lastBalance = currentBalance
        writeState(state)
        spent = state.cumulativeSpent
        since = state.since
      }

      const modelChanged = !!state?.lastModel && model !== state.lastModel
      if (modelChanged || (state && !state.lastModel)) {
        state.lastModel = model
        writeState(state)
      }

      const context = getContextUsage()

      // 项目路径: 显示完整路径
      const projectDir = process.cwd()

      process.stdout.write(
        render({
          model,
          currentBalance: balanceInfo.total_balance,
          currency: balanceInfo.currency,
          spent,
          since,
          showModel: true,
          cwd: projectDir,
          contextPercent: context.percent,
          contextTokens: context.used,
          contextTotal: context.total,
        }),
      )
    } else {
      // console.log("no DeepSeek")
    }
  } catch (err) {
    // console.log(err)
    // @ts-expect-error
    const msg = `deepseek-statusLine ${err.name} ${err.message}`
    console.log(`\n${colors.red}${msg}${colors.reset}`)
    // @ts-expect-error
    log(`${msg}→stack:${err.stack}`)
  }

  log("END\n")
})
