# XNOW-Harness

> Claude Code 辅助工具箱 — 一个人顶全部角色

## 定位

XNOW-Harness **不是替代 Claude Code**，而是站在 Claude Code 旁边，帮你做这些事：

| 场景 | 用什么 |
|------|--------|
| 日常写代码 | **Claude Code**（主力） |
| 同步代码到 GitHub | `xnow sync` |
| 发布版本 | `xnow release patch` |
| 初始化仓库 | `xnow init` |
| 查看项目状态 | `xnow status` |
| 查余额 | `xnow balance` |
| 换电脑恢复环境 | `python scripts/bootstrap.py` |

## 工作流

```
VS Code（编辑器）
  + Claude Code（AI 编程主力）
  + XNOW-Harness（辅助工具箱）
       ├── xnow sync     提交+推送
       ├── xnow release  打 tag + GitHub Release
       ├── xnow init     新建仓库
       ├── xnow status   项目状态
       └── xnow balance  DeepSeek 余额
```

## 高手工作流

> 把 AI 当成"流动的超级结对编程队友" — 每次对话只做一件事，靠文档衔接上下文

核心三条：

### 1️⃣ 项目级 CLAUDE.md

每个项目给 AI 一份"身份证"，开新对话一秒入戏：

```
project-root/
├── .claude/PROJECT_SUMMARY.md    ← 技术栈/目录/进度/决策记录
└── CLAUDE.md                     ← 也可以放项目根目录
```

### 2️⃣ 单任务单对话

```
❌ 一个对话里：修 Bug + 加功能 + 重构 → AI 上下文爆炸
✅ 一个对话只做一件事 → 做完 xnow sync → 开新对话
```

### 3️⃣ 主动管理上下文

- 聊了 15~20 轮 → 考虑开新对话
- AI 开始"忘记"前面内容 → 停，开新的
- 开新对话前把项目 CLAUDE.md 带上

> 📖 完整指南 → `docs/expert-workflow.md`
> 💡 快捷查看 → `xnow workflow`

## 安装

```bash
# 1. 克隆
git clone https://github.com/xiasummer740/XNOW-Harness.git
cd XNOW-Harness

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 API Key
# 方法一：环境变量
set DEEPSEEK_API_KEY=sk-your-key

# 方法二：配置文件
cp config/config.default.yaml config/config.yaml
# 编辑 config/config.yaml 填写 API Key
```

## 使用

```bash
# 进入你的项目目录
cd your-project

# 启动 XNOW-Harness
python -m xnow_harness

# 或直接运行
python -m xnow_harness.main
```

### 交互示例

```
╔══════════════════════════════════════╗
║  ░ X N O W ░  Harness               ║
║  一个人顶全部角色                     ║
╚══════════════════════════════════════╝

  ℹ  模型: deepseek-v4-pro
  ℹ  工作目录: my-app
  ℹ  已加载项目上下文 (1245 chars)
  ✓  Git 仓库: 就绪

  [?] 你 > 帮我创建一个用户登录页面

  ┌────────────────────────────────────────┐
  │  我来帮你创建一个登录页面...             │
  │                                        │
  │  → 读取 src/pages/login.tsx...          │
  │  → 分析现有项目结构...                   │
  └────────────────────────────────────────┘
```

## 新电脑恢复指南

换电脑或重装后，三步恢复全部环境:

```bash
# 1. 安装基础依赖
# 确保已安装: Python 3.10+, Git, Node.js 18+

# 2. 运行引导脚本
python scripts/bootstrap.py

# 3. 确保 API Key 可用（CC Switch 会自动处理）
# 启动 CC Switch → API Key 自动生效

# 4. 启动 XNOW-Harness
cd XNOW-Harness
python -m xnow_harness
```

### Claude Code 恢复（可选）

如果你也使用 Claude Code，参考 `tools/claude-settings.template.json`
复制到 `~/.claude/settings.json` 后调整。

### 底部状态栏恢复

所有配置文件都已打包在此仓库中，无需额外安装。

## 项目结构

```
XNOW-Harness/
├── xnow_harness/
│   ├── __init__.py       # 版本信息
│   ├── __main__.py       # python -m 入口
│   ├── main.py           # CLI 入口: sync/release/init/status/balance
│   ├── commands.py       # 命令实现
│   ├── lessons.py        # 技术踩坑库（10条）
│   └── utils/
│       ├── config.py     # 配置管理
│       ├── display.py    # 终端显示
│       └── balance.py    # DeepSeek 余额查询
├── scripts/
│   └── bootstrap.py      # 新电脑引导脚本
├── tools/
│   ├── claude-settings.template.json  # Claude Code 配置模板
│   ├── claude-skills-reference.md     # 技能清单备份
│   └── statusline/       # 底部状态栏工具源码
├── config/
│   └── config.default.yaml
├── requirements.txt
└── README.md
```

## 配置

编辑 `config/config.yaml` 或项目根目录的 `.xnow.yaml`

```yaml
model:
  primary:
    name: deepseek-v4-pro
    temperature: 0.0

tools:
  shell_timeout: 120

repo:
  map_enabled: true
  max_tokens: 4096

display:
  theme: xnow-dark
  language: zh
```

## 开发计划

- [x] 核心 Agent Loop
- [x] 文件读写工具
- [x] Shell 执行
- [x] Git 集成
- [x] Repo Map
- [ ] 多轮对话上下文管理优化
- [ ] lint 检查集成
- [ ] 子代理模式（规划/执行分离）
- [ ] MCP 协议支持

---

**XNOW** — 一个人顶全部角色
