import readline from "node:readline"

// 清除当前行并回到开头
export function clearLine() {
  readline.cursorTo(process.stdout, 0)
  readline.clearLine(process.stdout, 0)
}

export const colors = {
  reset: "\x1b[0m",
  red: "\x1b[31m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  blue: "\x1b[34m",
  magenta: "\x1b[35m",
  cyan: "\x1b[36m",
  white: "\x1b[37m",

  // 亮色
  brightRed: "\x1b[91m",
  brightGreen: "\x1b[92m",
  brightYellow: "\x1b[93m",
  brightBlue: "\x1b[94m",

  // 背景色
  bgRed: "\x1b[41m",
  bgGreen: "\x1b[42m",
  bgYellow: "\x1b[43m",

  // 样式
  bold: "\x1b[1m",
  dim: "\x1b[2m",
}
