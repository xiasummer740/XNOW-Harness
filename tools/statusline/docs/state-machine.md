# State Machine: 花费追踪

## 概述

实现跨进程累计花费（`Spent`）的持久化方案。

每次 `node index.ts` 都是新进程，内存无法保留状态，所以将状态持久化到 `~/.deepseek-balance/state.json`。

## 文件位置

```
~/.deepseek-balance/state.json
```

## 数据结构

```json
{
  "cumulativeSpent": 28,
  "lastBalance": 100.00,
  "since": "2026-05-31"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `cumulativeSpent` | number | 累计总花费，只增不减 |
| `lastBalance` | number | 上一次的余额，用于增量计算本次消耗 |
| `since` | string | 首次记录的日期（ISO date），永不变 |

## 核心流程

### 每次运行伪代码

```
1. readState() → { cumulativeSpent, lastBalance, since }
   若文件不存在/损坏 → 首次运行，state = { 0, currentBalance, today }
2. 调 API → currentBalance
3. consumption = max(0, lastBalance - currentBalance)
   充值时 currentBalance > lastBalance → consumption = 0
4. cumulativeSpent += consumption   ← 只增不减
5. writeState({ cumulativeSpent, currentBalance, since })
6. render: Spent ¥cumulativeSpent (Since since)
```

### 流程图

```
                  ┌─────────────┐
                  │  readState  │
                  └──────┬──────┘
                         │
              ┌──────────┴──────────┐
              │                     │
          存在/合法              不存在/损坏
              │                     │
              │              ┌──────┴──────┐
              │              │  首次运行    │
              │              │ state =     │
              │              │ { 0, bal,   │
              │              │   today }   │
              │              └──────┬──────┘
              └──────────┬──────────┘
                         │
                  ┌──────┴──────┐
                  │  API 请求   │
                  │  currentBal │
                  └──────┬──────┘
                         │
                  ┌──────┴──────┐
                  │ consumption │
                  │ = max(0,    │
                  │ lastBal -   │
                  │ currentBal) │
                  └──────┬──────┘
                         │
                  ┌──────┴──────┐
                  │ cumulative  │
                  │ += consump  │
                  └──────┬──────┘
                         │
                  ┌──────┴──────┐
                  │ writeState  │
                  └──────┬──────┘
                         │
                  ┌──────┴──────┐
                  │   render    │
                  │Spent ¥xx.xx │
                  │(Since date) │
                  └─────────────┘
```

## 场景模拟

### 场景1：首次运行

状态文件不存在。

```
当前余额: 100.00
→ 写入 { cumulativeSpent: 0, lastBalance: 100.00, since: "2026-05-31" }
→ Spent ¥0.00 (Since 2026-05-31)
```

### 场景2：正常消耗

```
累计: 0   上次: 100   当前: 72
consumption = max(0, 100 - 72) = 28
累计 = 0 + 28 = 28
→ 写入 { cumulativeSpent: 28, lastBalance: 72,  since: "2026-05-31" }
→ Spent ¥28.00 (Since 2026-05-31)
```

### 场景3：继续消耗

```
累计: 28   上次: 72   当前: 50
consumption = max(0, 72 - 50) = 22
累计 = 28 + 22 = 50
→ 写入 { cumulativeSpent: 50, lastBalance: 50,  since: "2026-05-31" }
→ Spent ¥50.00 (Since 2026-05-31)
```

### 场景4：充值（花费不应减少）

```
累计: 50   上次: 50   当前: 200
consumption = max(0, 50 - 200) = 0    ← 充值检测，不增加
累计 = 50 + 0 = 50                     ← 花费不变！
→ 写入 { cumulativeSpent: 50, lastBalance: 200, since: "2026-05-31" }
→ Spent ¥50.00 (Since 2026-05-31)     ← 充值后花费不会变少 ✓
```

### 场景5：充值后继续消耗

```
累计: 50   上次: 200   当前: 150
consumption = max(0, 200 - 150) = 50
累计 = 50 + 50 = 100
→ 写入 { cumulativeSpent: 100, lastBalance: 150, since: "2026-05-31" }
→ Spent ¥100.00 (Since 2026-05-31)
```

### 场景6：多次充值 + 长期使用

| 事件 | lastBalance | currentBalance | consumption | cumulativeSpent | 充值变化？ |
|------|-------------|----------------|-------------|-----------------|-----------|
| 首次 | - | 100 | - | **0** | - |
| 消耗 30 | 100 | 70 | 30 | **30** | 否 |
| 消耗 10 | 70 | 60 | 10 | **40** | 否 |
| 充值 +50 | 60 | 110 | 0 | **40** | ✓ 不变 |
| 消耗 20 | 110 | 90 | 20 | **60** | 否 |
| 消耗 40 | 90 | 50 | 40 | **100** | 否 |
| 充值 +100 | 50 | 150 | 0 | **100** | ✓ 不变 |
| 消耗 30 | 150 | 120 | 30 | **130** | 否 |
| 消耗 70 | 120 | 50 | 70 | **200** | 否 |

monotonic: `0 → 30 → 40 → 40(充值) → 60 → 100 → 100(充值) → 130 → 200` ✓

## 边界处理

| 场景 | 行为 |
|------|------|
| 文件不存在 | 视为首次运行，新建 state |
| JSON 解析失败（手动编辑/损坏） | 捕获异常，视为首次运行 |
| currentBalance > lastBalance（充值） | consumption = 0，不增加花费 |
| currentBalance == lastBalance | consumption = 0，完全不变 |
| currentBalance < 0 | 按 API 返回实际值计算即可 |
| 并发读写 | 每次独立进程，Node 串行无竞态 |
| 手动删除 state.json | 视为全新开始，spent 归零 |
| 重装系统 | 同上 |
| 很久不打开，期间多次充值 | 下次运行时 lastBalance 滞后，一次消费可能偏大，但 cumulativeSpent 不会大于实际（因为消耗额被充值部分对冲了）。精确性取决于 statusline 轮询频率。 |

## 渲染格式

```
🐳 💰 Balance ¥6.72 | Spent ¥1.00 (Since 2026-05-31)
```

- `Spent`：固定颜色（`colors.dim`）
- `Balance`：按金额变色（绿/黄/红）
