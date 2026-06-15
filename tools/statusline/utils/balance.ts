import { log } from "./logger.ts"

const {
  BASE_URL = "https://api.deepseek.com",
  DEEP_SEEK_API_KEY_FOR_BALANCE: API_KEY,
} = process.env

// console.log("BASE_URL:", BASE_URL)
// console.log("API_KEY:", API_KEY)

let lastFetchTime = 0
// CC's every call of statusline API is a new node.js process: `node xx.ts`
// Thus this cache strategy only work in a single Node.js process
// when a new status API call lastFetchTime cachedPromise is always reset
// TODO:
// use file as multiple process cache and use sync file reading to avoid multiple values read
// but call to deepseek api to get balance is not a big thing so the cache solution is not urgent
let cachedPromise: Promise<BalanceInfo> | null = null
const DEBOUNCE_MS = 10_000

export async function getBalance() {
  const now = Date.now()
  // log(
  //   "cachedPromise:",
  //   JSON.stringify({
  //     cachedPromise: typeof cachedPromise,
  //     now,
  //     lastFetchTime,
  //     gap: now - lastFetchTime,
  //   }),
  // )
  if (cachedPromise && now - lastFetchTime < DEBOUNCE_MS) {
    return cachedPromise
  }

  lastFetchTime = now
  // log("set lastFetchTime to", now)

  cachedPromise = getBalanceCore({ signal: AbortSignal.timeout(3000) })
    .then((balance) => balance.balance_infos[0])
    .catch((error) => {
      // 清除缓存的 Promise，允许重试
      cachedPromise = null
      throw error
    })

  return cachedPromise
}

/**
 * https://github.com/esengine/DeepSeek-Reasonix/blob/fdea3bb8/src/client.ts#L48-L58
 * @param opts
 * @returns
 */
async function getBalanceCore(
  opts: { signal?: AbortSignal } = {},
): Promise<UserBalance> {
  const url = `${BASE_URL}/user/balance`
  log(`fetching ${url}`)

  try {
    const resp = await fetch(url, {
      method: "GET",
      headers: { Authorization: `Bearer ${API_KEY}` },
      signal: opts.signal,
    })
    if (!resp.ok) {
      throw new Error(
        `getBalance failed: HTTP ${resp.status} ${resp.statusText}.\nDEEP_SEEK_API_KEY_FOR_BALANCE env missing (${API_KEY}). Reload terminal after added.`,
        { cause: resp },
      )
    }
    const data = (await resp.json()) as UserBalance
    // console.log("data:", data)
    if (!data || !Array.isArray(data.balance_infos)) {
      throw new TypeError("balance_infos no Array")
    }
    return data
  } catch (err) {
    // console.error("err:", err)
    throw err
  }
}

if (import.meta.main) {
  const balance = await getBalanceCore()
  console.log("balance:", balance?.balance_infos)
}

interface BalanceInfo {
  /** 货币类型（"CNY" 或 "USD"） */
  currency: "CNY" | "USD"
  /** 总余额 */
  total_balance: string
  /** 赠送余额 */
  granted_balance?: string
  /** 充值余额 */
  topped_up_balance?: string
}

interface UserBalance {
  is_available: boolean
  balance_infos: BalanceInfo[]
}
