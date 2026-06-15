"""技术踩坑库 — 从踩坑记录中学习，避免重复犯错

自动加载 CLAUDE.md 中的踩坑记录和 memory 中的教训，
在相关场景出现时注入到 system prompt。
"""

import re
from pathlib import Path
from typing import Optional

# 内置踩坑记录（从 CLAUDE.md 和 memory 提取）
BUILTIN_LESSONS = [
    {
        "id": "node-global-path",
        "title": "npm 全局命令不在 PATH",
        "detail": "npm install -g pm2 成功后 pm2 报 command not found。根因：npm 全局装到 Node 目录内 bin/，该目录不在 PATH 中。",
        "fix": "command -v pm2 检测失败后通过 npm root -g 取路径手动建软链到 /usr/local/bin/",
        "triggers": ["npm install -g", "command not found", "全局安装"],
    },
    {
        "id": "mysql-service-name",
        "title": "Debian 上 MySQL 服务名可能是 mariadb",
        "detail": "Debian 上 MySQL 服务名可能是 mariadb 而不是 mysql，不能硬编码 systemctl start mysql",
        "fix": "先检测 systemctl list-units | grep -i mysql，找不到再用 mariadb",
        "triggers": ["mysql", "mariadb", "systemctl", "service"],
    },
    {
        "id": "jwt-secret-overwrite",
        "title": "部署脚本覆盖 JWT_SECRET 导致登录失效",
        "detail": "部署脚本中 .env 的 JWT_SECRET 每次部署都覆盖，导致所有登录态失效",
        "fix": "先读旧值，不存在才生成新值",
        "triggers": ["JWT_SECRET", ".env", "部署脚本", "环境变量"],
    },
    {
        "id": "nginx-first-deploy",
        "title": "首次部署 nginx reload 失败",
        "detail": "nginx -t && systemctl reload nginx 首次部署会失败，因为 nginx 没启动过",
        "fix": "需要 fallback 到 systemctl start nginx",
        "triggers": ["nginx", "reload", "首次部署"],
    },
    {
        "id": "node-tarball-path",
        "title": "tarball 部署 Node.js 后全局工具不在 PATH",
        "detail": "通过 tarball 部署 Node.js 后，npm install -g 的全局命令不在 PATH 中",
        "fix": "用 npm root -g 定位全局目录，手动建立软链到 /usr/local/bin/",
        "triggers": ["tarball", "node", "PATH", "全局"],
    },
    {
        "id": "command-patterns-avoid",
        "title": "shell 命令写法触发安全拦截",
        "detail": "Claude Code 有底层安全检测，特定写法会触发硬编码拦截，permissions.allow 白名单也屏蔽不了。包括：cd + 路径复合命令、powershell 多段复合命令",
        "fix": "避免 cd 后直接接命令。改用单独 cd 命令，或在 Bash 工具中直接使用完整路径",
        "triggers": ["cd", "permission", "安全拦截", "白名单", "blocked"],
    },
    {
        "id": "switch-project-check",
        "title": "切项目前检查 git status",
        "detail": "多项目切换时容易丢失未提交的修改。切项目前必须先 git status 确认当前项目没有未提交的修改",
        "fix": "每次切换项目前自动检查 git status，有未提交的先提交或 stash",
        "triggers": ["切换项目", "切换目录", "git status", "未提交"],
    },
    {
        "id": "three-strikes-review",
        "title": "三次不出即复盘",
        "detail": "同一个模块或问题连续 3 次尝试仍未解决时，必须暂停修复。先查踩坑记录是否有类似案例，分析 3 次失败模式，写出完整修复计划再执行",
        "fix": "连续 3 次失败 → 暂停 → 查踩坑记录 → 分析失败模式 → 写完整计划 → 经确认后执行 → 完成后追加到踩坑库",
        "triggers": ["三次", "三次不出", "3次", "复盘", "卡住", "卡壳", "解决不了",
                      "搞不定", "重试", "又失败", "又错", "重复失败", "多次尝试",
                      "还不行", "还是错", "问题重复", "一直报错", "死循环"],
    },
    {
        "id": "multi-device-workflow",
        "title": "新电脑 / 新会话启动检查流程",
        "detail": "祥哥可能在任意一台电脑上继续工作。每次开始前必须拉最新代码、安装依赖、验证能跑",
        "fix": "每次会话开始时执行: git pull → npm install → npm run dev。验证通过后再开始开发",
        "triggers": ["新电脑", "新会话", "切换设备", "第一次", "clone"],
    },
    {
        "id": "global-eslint-prettier",
        "title": "全局代码检查工具路径",
        "detail": "ESLint + Prettier 已全局安装，不依赖项目 node_modules。配置在 C:/Users/Administrator/.claude/quality/",
        "fix": "review 阶段用 npx eslint --config C:/Users/Administrator/.claude/quality/eslint.config.js <文件> 检查",
        "triggers": ["eslint", "prettier", "代码检查", "lint", "格式化"],
    },
]


class LessonBank:
    """踩坑知识库"""

    def __init__(self, lessons_dir: Optional[Path] = None):
        self.lessons = list(BUILTIN_LESSONS)
        if lessons_dir and lessons_dir.exists():
            self._load_from_dir(lessons_dir)

    def _load_from_dir(self, path: Path):
        """从目录加载自定义踩坑记录"""
        for f in sorted(path.glob("*.md")):
            content = f.read_text(encoding="utf-8")
            lesson = self._parse_lesson(content, f.stem)
            if lesson:
                self.lessons.append(lesson)

    def _parse_lesson(self, content: str, file_id: str) -> Optional[dict]:
        """解析 markdown 格式的踩坑记录"""
        title = ""
        detail = ""
        fix = ""
        triggers = [file_id]

        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("# ") or line.startswith("## "):
                title = line.lstrip("#").strip()
            if "根因" in line or "原因" in line:
                detail = line.strip()
            if "修复" in line or "解决" in line:
                fix = line.strip()

        if title:
            return {
                "id": file_id,
                "title": title,
                "detail": detail or content[:200],
                "fix": fix or "",
                "triggers": triggers,
            }
        return None

    def query(self, text: str) -> list[dict]:
        """根据输入文本查找相关踩坑记录（双向关键词匹配）"""
        text_lower = text.lower()
        # 把查询拆成关键词
        query_words = set(w.strip() for w in text_lower.replace("-", " ").replace("/", " ").split() if len(w.strip()) > 2)
        matches = []

        for lesson in self.lessons:
            score = 0
            all_triggers = " ".join(lesson.get("triggers", [])).lower()
            title = lesson["title"].lower()

            # 触发词匹配（双向）
            for trigger in lesson.get("triggers", []):
                t = trigger.lower()
                if t in text_lower:
                    score += 2
                # 查询词出现在触发词中也算
                for w in query_words:
                    if w in t:
                        score += 1

            # 查询词出现在标题中加分
            for w in query_words:
                if w in title:
                    score += 2
            if score > 0:
                matches.append((score, lesson))

        matches.sort(key=lambda x: -x[0])
        return [m[1] for m in matches[:3]]

    def get_system_prompt(self) -> str:
        """生成 system prompt 中的踩坑提示"""
        if not self.lessons:
            return ""

        lines = [
            "\n## 📝 技术踩坑备忘录（遇到过的问题，避免重复踩）",
        ]
        for l in self.lessons:
            lines.append(f"- **{l['title']}**: {l['detail']}")
            if l['fix']:
                lines.append(f"  修复: {l['fix']}")

        return "\n".join(lines)

    def format_for_llm(self, query: str) -> str:
        """为 LLM 格式化相关踩坑记录"""
        relevant = self.query(query)
        if not relevant:
            return ""

        lines = ["\n## 📝 相关踩坑记录（请留意）"]
        for l in relevant:
            lines.append(f"- {l['title']}")
            lines.append(f"  {l['detail']}")
            if l['fix']:
                lines.append(f"  建议: {l['fix']}")

        return "\n".join(lines)
