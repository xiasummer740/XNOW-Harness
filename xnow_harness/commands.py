"""XNOW 内置命令 — /sync /release /status /init /workflow

这些命令在交互循环中直接解析，不需要 LLM 参与。
"""

import subprocess
import sys
import json
import os
from pathlib import Path
from typing import Optional
from .utils.display import console, show_step, show_ok, show_warn, show_error, show_info

GITHUB_USER = "xiasummer740"


def handle_command(cmd: str, args: list[str]) -> Optional[bool]:
    """处理内置命令。返回 True 表示继续循环，False 表示退出，None 表示不是命令。"""
    cmd = cmd.lower()

    handlers = {
        "sync": cmd_sync,
        "commit": cmd_sync,
        "push": cmd_sync,
        "status": cmd_status,
        "init": cmd_init,
        "release": cmd_release,
        "tag": cmd_release,
        "help": cmd_help,
    }

    handler = handlers.get(cmd)
    if handler is None:
        return None

    result = handler(args)
    return result if result is not None else True


def cmd_sync(args: list[str]) -> bool:
    """xnow sync — 提交 + 推送"""
    msg = " ".join(args) if args else ""
    show_step("同步代码到 GitHub...")

    # git add
    subprocess.run(["git", "add", "-A"], capture_output=True)
    show_ok("已暂存所有变更")

    # git commit
    if not msg:
        msg = _auto_commit_message()
    result = subprocess.run(["git", "commit", "-m", msg], capture_output=True, text=True)
    if result.returncode != 0:
        if "nothing to commit" in result.stderr or "nothing to commit" in result.stdout:
            show_warn("没有需要提交的变更")
            return True
        show_error(f"提交失败: {result.stderr[:200]}")
        return True

    show_ok(f"提交: {msg}")

    # git push
    branch = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True
    ).stdout.strip()

    push = subprocess.run(["git", "push", "origin", branch], capture_output=True, text=True)
    if push.returncode == 0:
        show_ok(f"已推送到 origin/{branch}")
    else:
        show_warn(f"推送失败，尝试设置上游...")
        subprocess.run(["git", "push", "-u", "origin", branch])

    return True


def cmd_status(args: list[str]) -> bool:
    """xnow status — 项目状态"""
    show_step("检查项目状态...")

    # Git 信息
    is_repo = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        capture_output=True
    ).returncode == 0

    if is_repo:
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True
        ).stdout.strip()

        # 是否干净
        dirty = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True
        ).stdout.strip()

        # 最新 tag
        tag = subprocess.run(
            ["git", "tag", "--sort=-creatordate", "--list"],
            capture_output=True, text=True
        ).stdout.strip().split("\n")[0] if is_repo else ""

        show_ok(f"Git 仓库: 就绪")
        show_info(f"分支: {branch}")
        if tag:
            show_info(f"最新 tag: {tag}")
        if dirty:
            show_warn(f"未提交的变更:")
            for line in dirty.split("\n")[:10]:
                console.print(f"    [dim]{line}[/dim]")
        else:
            show_ok("工作区干净")
    else:
        show_warn("未检测到 Git 仓库")

    # 项目基本信息
    project_name = Path.cwd().name
    show_info(f"项目: {project_name}")

    # gh release 检查
    try:
        release = subprocess.run(
            ["gh", "release", "list", "--limit", "1"],
            capture_output=True, text=True
        )
        if release.returncode == 0 and release.stdout.strip():
            show_ok("GitHub Release: 存在")
        else:
            show_info("GitHub Release: 暂无")
    except FileNotFoundError:
        show_info("GitHub Release: 跳过（未安装 gh CLI）")

    return True


def cmd_init(args: list[str]) -> bool:
    """xnow init — 初始化项目并推送到 GitHub"""
    project_name = Path.cwd().name

    # 检查是否已经是 git 仓库
    is_repo = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        capture_output=True
    ).returncode == 0

    if is_repo:
        show_warn("已经是 Git 仓库，跳过 init")
        return True

    show_step(f"初始化项目: {project_name}")

    # git init
    subprocess.run(["git", "init"], capture_output=True)
    show_ok("Git 仓库已初始化")

    # .gitignore
    if not Path(".gitignore").exists():
        gitignore = """node_modules/
dist/
build/
.next/
.env
.env.local
*.log
.DS_Store
__pycache__/
*.pyc
"""
        Path(".gitignore").write_text(gitignore)
        show_ok(".gitignore 已生成")

    # README
    if not Path("README.md").exists():
        readme = f"# {project_name}\n\n> XNOW 项目\n"
        Path("README.md").write_text(readme)
        show_ok("README.md 已生成")

    # 检查 GitHub 是否已有同名仓库
    show_step("检查 GitHub 上是否存在同名仓库...")
    existing = ""
    try:
        result = subprocess.run(
            ["gh", "repo", "list", GITHUB_USER, "--json", "name", "--jq",
             f'.[] | select(.name == "{project_name}").name'],
            capture_output=True, text=True
        )
        existing = result.stdout.strip()
    except FileNotFoundError:
        show_warn("gh CLI 未安装，请先安装 GitHub CLI")
        return True

    if existing:
        show_warn(f"GitHub 上已存在同名仓库, 执行更新...")
        subprocess.run(["git", "add", "-A"])
        subprocess.run(["git", "commit", "-m", "init: 项目初始化"], capture_output=True)
        subprocess.run(["git", "branch", "-M", "main"], capture_output=True)
        subprocess.run(
            ["git", "remote", "add", "origin", f"https://github.com/{GITHUB_USER}/{project_name}.git"],
            capture_output=True
        )
        subprocess.run(["git", "push", "-u", "origin", "main"], capture_output=True)
        show_ok(f"已推送到现有仓库: {GITHUB_USER}/{project_name}")
    else:
        show_step(f"创建 GitHub 仓库: {GITHUB_USER}/{project_name}")
        result = subprocess.run(
            ["gh", "repo", "create", f"{GITHUB_USER}/{project_name}",
             "--private", "--source=.", "--remote=origin", "--push"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            show_ok(f"仓库已创建: https://github.com/{GITHUB_USER}/{project_name}")
        else:
            show_warn(f"创建失败: {result.stderr[:200]}")

    return True


def cmd_release(args: list[str]) -> bool:
    """xnow release <patch|minor|major> — 打 tag + Release"""
    bump_type = args[0] if args else "patch"
    if bump_type not in ("patch", "minor", "major"):
        show_error("版本类型必须是 patch / minor / major")
        return True

    # 读取当前版本
    current = _get_current_version()
    new_version = _bump_version(current, bump_type)
    tag = f"v{new_version}"

    show_step(f"发布版本: {tag} ({bump_type})")

    # 更新 package.json
    if Path("package.json").exists():
        import re
        content = Path("package.json").read_text(encoding="utf-8")
        content = re.sub(r'"version":\s*"[^"]*"', f'"version": "{new_version}"', content)
        Path("package.json").write_text(content, encoding="utf-8")
        show_ok(f"package.json 版本更新: {new_version}")

    # 提交版本变更
    subprocess.run(["git", "add", "-A"], capture_output=True)
    subprocess.run(["git", "commit", "-m", f"chore: bump version to {tag}"], capture_output=True)
    subprocess.run(["git", "push"], capture_output=True)

    # 打 tag
    subprocess.run(["git", "tag", tag])
    subprocess.run(["git", "push", "origin", tag])
    show_ok(f"Tag 已推送: {tag}")

    # 生成 Release Notes
    notes = _generate_release_notes(new_version)
    notes_file = Path(".xnow_release_notes.md")
    notes_file.write_text(notes, encoding="utf-8")

    # gh release create
    result = None
    try:
        result = subprocess.run(
            ["gh", "release", "create", tag, "--title", tag, "--notes-file", str(notes_file)],
            capture_output=True, text=True,
        )
    except FileNotFoundError:
        show_warn("gh CLI 未安装，跳过 Release 创建")

    if notes_file.exists():
        notes_file.unlink()

    if result and result.returncode == 0:
        project = Path.cwd().name
        show_ok(f"Release 已发布: https://github.com/{GITHUB_USER}/{project}/releases/tag/{tag}")
    else:
        show_error(f"Release 创建失败: {result.stderr[:200] if result else 'gh CLI 未安装'}")

    return True


def cmd_help(args: list[str]) -> bool:
    """显示帮助"""
    console.print("""
[bold cyan]XNOW 内置命令[/bold cyan]

[bold]/sync [提交信息][/bold]     提交代码并推送到 GitHub
[bold]/status[/bold]               查看项目 git / 版本状态
[bold]/init[/bold]                 初始化项目 → GitHub 仓库
[bold]/release <type>[/bold]       发布版本 (patch/minor/major)
[bold]/help[/bold]                 显示此帮助
""")
    return True


# ═══ 辅助函数 ═══

def _auto_commit_message() -> str:
    """根据变更自动生成提交信息"""
    diff = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True, text=True
    ).stdout.strip().split("\n")

    if not diff or diff == [""]:
        return "chore: 代码同步"

    # 根据文件名猜类型
    for f in diff:
        f = f.lower()
        if any(x in f for x in ("fix", "bug", "hotfix", "error", "issue")):
            return f"fix: 修复 {Path(f).stem}"
        if any(x in f for x in ("feat", "feature", "add", "new")):
            return f"feat: 添加 {Path(f).stem}"
        if any(x in f for x in ("doc", "readme", "md")):
            return f"docs: 更新文档"

    if len(diff) <= 3:
        return f"feat: {Path(diff[0]).stem}"

    return f"chore: 更新 {len(diff)} 个文件"


def _get_current_version() -> str:
    """读取当前版本号"""
    # 从 git tag
    tag = subprocess.run(
        ["git", "tag", "--sort=-creatordate", "--list"],
        capture_output=True, text=True
    ).stdout.strip().split("\n")

    for t in tag:
        t = t.strip()
        if t.startswith("v"):
            return t[1:]

    # 从 package.json
    if Path("package.json").exists():
        import re
        m = re.search(r'"version":\s*"([^"]+)"', Path("package.json").read_text())
        if m:
            return m.group(1)

    return "0.1.0"


def _bump_version(ver: str, bump_type: str) -> str:
    """版本递增"""
    parts = ver.split(".")
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

    if bump_type == "major":
        major += 1; minor = 0; patch = 0
    elif bump_type == "minor":
        minor += 1; patch = 0
    else:
        patch += 1

    return f"{major}.{minor}.{patch}"


def _generate_release_notes(version: str) -> str:
    """从 git log 生成 Release Notes"""
    # 获取最近 tag 之后的 commit
    last_tag = subprocess.run(
        ["git", "tag", "--sort=-creatordate", "--list"],
        capture_output=True, text=True
    ).stdout.strip().split("\n")

    if last_tag and last_tag[0]:
        log = subprocess.run(
            ["git", "log", f"{last_tag[0]}..HEAD", "--oneline", "--format=%s"],
            capture_output=True, text=True
        ).stdout
    else:
        log = subprocess.run(
            ["git", "log", "--oneline", "--format=%s"],
            capture_output=True, text=True
        ).stdout

    features, fixes, chores = [], [], []
    for line in log.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("feat"):
            features.append(line)
        elif line.startswith("fix"):
            fixes.append(line)
        else:
            chores.append(line)

    notes = [f"## v{version}\n"]
    if features:
        notes.append("### ✨ 新功能")
        notes.extend(f"- {f}" for f in features)
        notes.append("")
    if fixes:
        notes.append("### 🐛 修复")
        notes.extend(f"- {f}" for f in fixes)
        notes.append("")
    if chores:
        notes.append("### 🔧 其他")
        notes.extend(f"- {c}" for c in chores)
        notes.append("")

    return "\n".join(notes)
