"""XNOW 内置命令 — /sync /verify /release /sync-env /status /init /workflow

这些命令在交互循环中直接解析，不需要 LLM 参与。
"""

import subprocess
import sys
import json
import os
import sqlite3
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
        "verify": cmd_verify,
        "status": cmd_status,
        "init": cmd_init,
        "release": cmd_release,
        "tag": cmd_release,
        "sync-env": cmd_sync_env,
        "deploy": cmd_deploy,
        "migrate": cmd_migrate,
        "workflow": cmd_workflow,
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


def _diagnose_error(step: str, output: str) -> None:
    """诊断常见验证错误并给出修复建议"""
    output_lower = output.lower()
    suggestions: list[str] = []

    if step == "build":
        if "module not found" in output_lower or "cannot find module" in output_lower:
            suggestions.append("缺少依赖，试试: npm install")
        elif "syntaxerror" in output_lower:
            suggestions.append("语法错误，检查报错位置附近的代码")
        elif "ts2307" in output_lower or "cannot find name" in output_lower:
            suggestions.append("TypeScript 类型错误，检查导入路径和类型定义")
        elif "eslint" in output_lower or "prettier" in output_lower:
            suggestions.append("代码格式问题，试试: npx eslint --fix .")
        elif "enoent" in output_lower or "not found" in output_lower:
            suggestions.append("命令不存在，检查 tasks.json 的 build 命令是否正确")
    elif step == "lint":
        if "prettier" in output_lower:
            suggestions.append("格式问题，试试: npx prettier --write .")
        else:
            suggestions.append("按报错修改代码，或试试: npx eslint --fix .")
    elif step == "test":
        if "assertionerror" in output_lower or "failed" in output_lower:
            suggestions.append("测试用例失败，检查断言和期望值")
        elif "timeout" in output_lower:
            suggestions.append("测试超时，可能依赖的服务未启动")
    elif step == "health":
        if "connection refused" in output_lower or "could not connect" in output_lower:
            suggestions.append("服务未启动，先启动服务再验证")
        elif "404" in output_lower or "not found" in output_lower:
            suggestions.append("健康检查路径不对，检查 health 命令的 URL")
    elif step == "e2e":
        if "timeout" in output_lower:
            suggestions.append("E2E 测试超时，检查测试环境是否就绪")

    if suggestions:
        for s in suggestions:
            show_info(f"💡 {s}")


def cmd_verify(args: list[str]) -> bool:
    """xnow verify — 运行 .claude/tasks.json 全栈验证流程

    验证步骤（按顺序，配了就跑，空字段跳过）:
      build  → 编译检查（180s 超时）
      lint   → 代码质量检查（60s）
      test   → 单元/集成测试（300s）
      health → 服务健康检查（15s，如 curl 接口）
      e2e    → 端到端测试（300s）
    """
    tasks_file = Path(".claude/tasks.json")
    if not tasks_file.exists():
        show_error(".claude/tasks.json 不存在，先 xnow init 初始化项目")
        return True

    try:
        tasks = json.loads(tasks_file.read_text())
    except json.JSONDecodeError:
        show_error(".claude/tasks.json 格式错误，请检查 JSON 语法")
        return True

    # 按顺序配超时，空字段跳过
    step_config: list[tuple[str, int]] = [
        ("build", 180),
        ("lint", 60),
        ("test", 300),
        ("health", 15),
        ("e2e", 300),
    ]
    results: dict[str, int] = {"pass": 0, "fail": 0, "skip": 0}

    for step, timeout in step_config:
        cmd = tasks.get(step, "").strip()
        if not cmd:
            results["skip"] += 1
            continue

        show_step(f"▶ {step}: {cmd}")
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            show_error(f"❌ {step}: 超时 (> {timeout}s)")
            results["fail"] += 1
            continue

        if result.returncode == 0:
            show_ok(f"✅ {step}: 通过")
            results["pass"] += 1
        else:
            show_error(f"❌ {step}: 失败 (exit {result.returncode})")
            output = (result.stdout or "") + (result.stderr or "")
            for line in output.strip().split("\n")[-10:]:
                console.print(f"  [dim]{line}[/dim]")
            # 诊断常见错误
            _diagnose_error(step, output)
            results["fail"] += 1

    total = len(step_config)
    console.print()
    if results["fail"] == 0:
        show_ok(f"\U0001f389 验证全部通过 ({results['pass']}/{total} 通过，{results['skip']} 跳过)")
        return True
    else:
        show_error(f"❌ 验证失败 ({results['fail']}/{total} 个步骤失败)")
        show_info("💡 修复流程: 修代码 → xnow verify → 通过")
        return False


def cmd_migrate(args: list[str]) -> bool:
    """xnow migrate — 数据库迁移管理（SQLite 自动检测）

    子命令:
      create <name>   → 创建迁移文件对（.up.sql / .down.sql）
      up              → 执行所有待迁移
      down            → 回滚最近一次迁移
      status          → 查看迁移状态
    """
    import datetime

    sub = args[0] if args else "status"
    migrations_dir = Path("migrations")
    db_path = _find_sqlite_db()

    if sub == "create":
        name = "_".join(args[1:]) if len(args) > 1 else "unnamed"
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = f"{ts}_{name}"

        migrations_dir.mkdir(exist_ok=True)

        up_file = migrations_dir / f"{prefix}.up.sql"
        down_file = migrations_dir / f"{prefix}.down.sql"

        if up_file.exists():
            show_warn(f"迁移文件已存在: {up_file}")
            return True

        up_file.write_text(f"-- {name}: up\n\n")
        down_file.write_text(f"-- {name}: down\n\n")
        show_ok(f"创建迁移: {prefix}")
        show_info(f"  {up_file}")
        show_info(f"  {down_file}")

    elif sub == "up":
        if db_path is None:
            show_error("未找到 SQLite 数据库（找 server/data.db 或 *.db）")
            return True

        # 创建 migrations 跟踪表
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                name TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.commit()

        # 读所有迁移文件
        if not migrations_dir.exists():
            show_warn("migrations/ 目录不存在")
            return True

        files = sorted(migrations_dir.glob("*.up.sql"))
        pending = []
        for f in files:
            name = f.stem.replace(".up", "")
            exists = conn.execute(
                "SELECT 1 FROM _migrations WHERE name = ?", (name,)
            ).fetchone()
            if not exists:
                pending.append(f)

        if not pending:
            show_ok("没有待迁移")
            return True

        show_step(f"执行 {len(pending)} 个待迁移...")
        for f in pending:
            name = f.stem.replace(".up", "")
            sql = f.read_text()
            if not sql.strip():
                show_warn(f"  ⏭  {name}: 空的 SQL 文件，跳过")
                continue
            try:
                conn.executescript(sql)
                conn.execute(
                    "INSERT INTO _migrations (name) VALUES (?)", (name,)
                )
                conn.commit()
                show_ok(f"  ✅ {name}")
            except sqlite3.DatabaseError as e:
                show_error(f"  ❌ {name}: {e}")
                conn.rollback()
                return True

        show_ok("迁移完成")

    elif sub == "down":
        if db_path is None:
            show_error("未找到 SQLite 数据库")
            return True

        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                name TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.commit()

        # 找最近一次迁移
        last = conn.execute(
            "SELECT name FROM _migrations ORDER BY applied_at DESC LIMIT 1"
        ).fetchone()

        if not last:
            show_warn("没有可回滚的迁移")
            return True

        name = last[0]
        down_file = migrations_dir / f"{name}.down.sql"

        if not down_file.exists():
            show_error(f"找不到回滚文件: {down_file}")
            return True

        sql = down_file.read_text()
        if not sql.strip():
            show_warn(f"  ⏭  {name}: 空的回滚 SQL，跳过")
            return True

        show_step(f"回滚: {name}")
        try:
            conn.executescript(sql)
            conn.execute("DELETE FROM _migrations WHERE name = ?", (name,))
            conn.commit()
            show_ok(f"  ✅ {name} 已回滚")
        except sqlite3.DatabaseError as e:
            show_error(f"  ❌ {name}: {e}")
            conn.rollback()
            return True

    else:  # status
        show_step("迁移状态")

        if db_path:
            conn = sqlite3.connect(str(db_path))
            applied = set()
            try:
                for row in conn.execute(
                    "SELECT name FROM _migrations ORDER BY applied_at"
                ):
                    applied.add(row[0])
            except sqlite3.DatabaseError:
                pass  # 表不存在 = 没有已应用的迁移
        else:
            applied = set()

        all_files = sorted(
            f.stem.replace(".up", "").replace(".down", "")
            for f in migrations_dir.glob("*.sql")
        ) if migrations_dir.exists() else []

        seen = set()
        for name in sorted(all_files):
            if name in seen:
                continue
            seen.add(name)
            status = "✅" if name in applied else "⏳"
            console.print(f"  {status} {name}")

        total = len(seen)
        applied_count = len(applied)
        show_info(f"已迁移: {applied_count}  /  待迁移: {total - applied_count}")

    return True


def _find_sqlite_db() -> Optional[Path]:
    """自动检测 SQLite 数据库文件"""
    for pattern in ["server/data.db", "data.db", "prisma/dev.db"]:
        p = Path(pattern)
        if p.exists():
            return p
    # 兜底：找第一个 .db 文件
    for f in sorted(Path.cwd().rglob("*.db")):
        if "node_modules" not in f.parts and ".git" not in f.parts:
            return f
    return None


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

    # .claude/ 地基 — tasks.json + todo.md
    claude_dir = Path(".claude")
    claude_dir.mkdir(exist_ok=True)

    tasks_file = claude_dir / "tasks.json"
    if not tasks_file.exists():
        tasks_file.write_text(json.dumps({
            "build": "npm run build",
            "lint": "",
            "test": "npm test",
            "health": "",
            "e2e": ""
        }, indent=2) + "\n")
        show_ok(".claude/tasks.json 已生成")

    todo_file = claude_dir / "todo.md"
    if not todo_file.exists():
        todo_file.write_text("# 技术债务清单\n\n> 当前无待处理债务\n")
        show_ok(".claude/todo.md 已生成")

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


def cmd_deploy(args: list[str]) -> bool:
    """xnow deploy — 部署前置检查清单

    部署是 🟢 操作（必须祥哥确认），此命令做前置检查:
      1. Git 工作区干净
      2. xnow verify（至少 build 通过）
      3. 打印部署清单
    """
    from datetime import datetime

    show_step("部署前置检查")

    # 1. Git 状态
    is_repo = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        capture_output=True
    ).returncode == 0

    if is_repo:
        dirty = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True
        ).stdout.strip()
        if dirty:
            show_warn("⚠️  工作区有未提交的修改，建议先 xnow sync")
        else:
            show_ok("✅ Git 工作区干净")

    # 2. 运行验证（强制 build 步骤）
    show_step("运行构建验证...")
    tasks_file = Path(".claude/tasks.json")
    if tasks_file.exists():
        try:
            tasks = json.loads(tasks_file.read_text())
            build_cmd = tasks.get("build", "").strip()
            if build_cmd:
                result = subprocess.run(build_cmd, shell=True, capture_output=True, text=True, timeout=180)
                if result.returncode == 0:
                    show_ok("✅ 构建通过")
                else:
                    show_error("❌ 构建失败，请修复后再部署")
                    for line in (result.stderr or "").strip().split("\n")[-5:]:
                        console.print(f"  [dim]{line}[/dim]")
                    return True
            else:
                show_warn("⚠️  未配置 build 命令，跳过")
        except (json.JSONDecodeError, subprocess.TimeoutExpired):
            show_warn("⚠️  tasks.json 读取失败，跳过验证")
    else:
        show_warn("⚠️  无 tasks.json，跳过验证")

    # 3. 打印部署指南
    console.print("""
[bold cyan]📋 部署清单[/bold cyan]

[bold]1. 构建[/bold]
   → npm run build  (或对应命令)

[bold]2. 数据库迁移[/bold]（如有 schema 变更）
   → xnow migrate status  (检查待迁移)
   → xnow migrate up      (执行迁移)

[bold]3. 传输/部署[/bold]
   → 根据目标平台执行（VPS / Electron 打包 / Docker 等）

[bold]4. 启动服务[/bold]
   → 停止旧进程 → 启动新进程
   → 检查启动日志无异常

[bold]5. 部署后验证[/bold]
   → 手动访问确认功能正常
   → 或配置 health 后跑 xnow verify

[bold]6. 回滚预案[/bold]
   → 部署失败 → xnow rollback <上一版本>
   → 或切回旧版本 / 旧容器

[dim]⚠️  部署是 🟢 操作，必须祥哥确认后再执行[/dim]
""")
    show_info("检查完成，确认无误后执行部署")
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

    # 前端重构建（如果有 client 子项目）
    client_pkg = Path("client") / "package.json"
    if client_pkg.exists():
        show_step("重建前端（确保版本号同步到构建产物）...")
        result = subprocess.run(["npm", "run", "build"], capture_output=True, text=True, timeout=120, cwd="client")
        if result.returncode == 0:
            show_ok("前端重建完成")
        else:
            show_warn(f"前端重建失败: {result.stderr[:100]}，建议手动重建")

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


def cmd_sync_env(args: list[str]) -> bool:
    """xnow sync-env — 同步 ~/.claude/ 配置到 xiangge-env 并推送 GitHub"""
    show_step("同步配置到 xiangge-env...")

    env_dir = _find_xiangge_env()
    if env_dir is None:
        show_error("找不到 xiangge-env 目录，请确保已克隆到本地")
        show_info("克隆命令: git clone https://github.com/xiasummer740/xiangge-env.git")
        return True

    show_ok(f"找到 xiangge-env: {env_dir}")

    import shutil
    from datetime import datetime

    home = Path.home()
    claude_dir = home / ".claude"
    errors: list[str] = []

    # 1. 同步 CLAUDE.md
    src = claude_dir / "CLAUDE.md"
    dst = env_dir / "CLAUDE.md"
    if src.exists():
        shutil.copy2(str(src), str(dst))
        show_ok("CLAUDE.md 已同步")
    else:
        show_warn("~/.claude/CLAUDE.md 不存在，跳过")

    # 1b. 同步 CLAUDE.rules.md + CLAUDE.reference.md
    for f in ["CLAUDE.rules.md", "CLAUDE.reference.md"]:
        src_f = claude_dir / f
        dst_f = env_dir / f
        if src_f.exists():
            shutil.copy2(str(src_f), str(dst_f))
            show_ok(f"{f} 已同步")
        else:
            show_warn(f"~/.claude/{f} 不存在，跳过")

    # 2. 同步 quality 工具
    src_q = claude_dir / "quality"
    dst_q = env_dir / "quality"
    if src_q.exists():
        if dst_q.exists():
            shutil.rmtree(str(dst_q))
        shutil.copytree(str(src_q), str(dst_q))
        show_ok("quality/ 已同步")
    else:
        show_warn("~/.claude/quality/ 不存在，跳过")

    # 3. 同步 skills
    src_s = claude_dir / "skills" / "my-profile"
    dst_s = env_dir / "skills" / "my-profile"
    if src_s.exists():
        if dst_s.exists():
            shutil.rmtree(str(dst_s))
        shutil.copytree(str(src_s), str(dst_s))
        show_ok("skills/my-profile/ 已同步")
    else:
        show_warn("~/.claude/skills/my-profile/ 不存在，跳过")

    # 4. 同步权限白名单
    local_settings = None
    for p in [
        Path.cwd() / ".claude" / "settings.local.json",
        Path.cwd().parent / ".claude" / "settings.local.json",
    ]:
        if p.exists():
            local_settings = p
            break
    if local_settings:
        try:
            with open(str(local_settings), "r", encoding="utf-8") as f:
                data = json.load(f)
            allowed = data.get("permissions", {}).get("allow", [])
            with open(str(env_dir / "permissions" / "allowlist.json"), "w", encoding="utf-8") as f:
                json.dump(allowed, f, ensure_ascii=False, indent=2)
            show_ok(f"权限白名单已同步 ({len(allowed)} 条)")
        except Exception as e:
            errors.append(f"权限同步失败: {e}")
    else:
        show_warn("未找到 settings.local.json，跳过权限同步")

    # 5. 同步记忆文件
    workspace_hash = _detect_workspace_hash(env_dir)
    mem_src = home / ".claude" / "projects" / workspace_hash / "memory"
    mem_dst = env_dir / "memory"
    if mem_src.exists():
        if mem_dst.exists():
            shutil.rmtree(str(mem_dst))
        shutil.copytree(str(mem_src), str(mem_dst))
        mem_count = len(list(mem_src.glob("*.md")))
        show_ok(f"memory/ 已同步 ({mem_count} 个文件)")
    else:
        show_warn("memory/ 目录不存在，跳过")

    # 6. 同步 hooks 脚本
    src_hooks = claude_dir / "hooks"
    dst_hooks = env_dir / "hooks"
    if src_hooks.exists():
        for f in src_hooks.iterdir():
            if f.name == "reminder-filter.sh":
                shutil.copy2(str(f), str(dst_hooks / f.name))
                show_ok(f"hooks/{f.name} 已同步")
        show_ok("hooks/ 已同步")
    else:
        show_warn("~/.claude/hooks/ 不存在，跳过")

    # 7. Git 提交推送
    show_step("提交并推送到 GitHub...")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    subprocess.run(["git", "add", "-A"], capture_output=True, cwd=str(env_dir))
    result = subprocess.run(
        ["git", "commit", "-m", f"chore: 同步配置 ({timestamp})"],
        capture_output=True, text=True, cwd=str(env_dir)
    )
    if result.returncode != 0:
        if "nothing to commit" in (result.stdout or "") or "nothing to commit" in (result.stderr or ""):
            show_warn("没有需要同步的变更")
        else:
            show_error(f"提交失败: {result.stderr[:200]}")
            return True
    else:
        show_ok("已提交变更")

    push = subprocess.run(["git", "push"], capture_output=True, text=True, cwd=str(env_dir))
    if push.returncode == 0:
        show_ok("已推送到 GitHub")
    else:
        show_warn(f"推送失败: {push.stderr[:200]}，请手动推送")
        show_info(f"  cd {env_dir} && git push")

    if errors:
        for e in errors:
            show_warn(e)

    show_ok("sync-env 完成")
    return True


def _find_xiangge_env() -> Optional[Path]:
    """自动找到 xiangge-env 目录"""
    env_dir = os.environ.get("XIANGGE_ENV_DIR")
    if env_dir:
        p = Path(env_dir)
        if p.exists() and (p / "CLAUDE.md").exists():
            return p.resolve()

    # 从 pip 安装路径反推
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "xnow-harness"],
            capture_output=True, text=True
        )
        for line in result.stdout.splitlines():
            if line.startswith("Location:"):
                loc = Path(line.split(":", 1)[1].strip())
                for candidate in [loc.parent, loc, loc.parent.parent]:
                    if (candidate / "CLAUDE.md").exists() and (candidate / "XNOW-Harness").exists():
                        return candidate.resolve()
    except Exception:
        pass

    # 当前目录向上搜索（找 CLAUDE.md 同级）
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        if (parent / "XNOW-Harness" / "setup.py").exists():
            # 先找同级的 xiangge-env 目录
            sibling = parent / "xiangge-env"
            if sibling.exists() and (sibling / "CLAUDE.md").exists():
                return sibling
            # 再找 CLAUDE.md 在 parent 下
            if (parent / "CLAUDE.md").exists():
                return parent

    # 常见用户目录
    for p in [
        Path.home() / "xiangge-env",
        Path.home() / "projects" / "xiangge-env",
    ]:
        if p.exists():
            return p

    return None


def _detect_workspace_hash(env_dir: Path) -> str:
    """从 xiangge-env 目录反推工作区 hash"""
    workspace_root = env_dir.parent
    return str(workspace_root).replace(":", "-").replace("\\", "-")


def cmd_workflow(args: list[str]) -> bool:
    """xnow workflow — 查看工作流状态和指南"""
    show_step("XNOW 高手工作流")

    console.print("""
[bold cyan]一、当前状态[/bold cyan]""")

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

        dirty = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True
        ).stdout.strip()

        tag = subprocess.run(
            ["git", "tag", "--sort=-creatordate", "--list"],
            capture_output=True, text=True
        ).stdout.strip().split("\n")[0] if is_repo else ""

        console.print(f"  📂 分支: [bold]{branch}[/bold]")
        if tag:
            console.print(f"  🏷️  最新 tag: [bold]{tag}[/bold]")
        if dirty:
            file_count = len(dirty.split("\n"))
            console.print(f"  ✏️  未提交: [yellow]{file_count}[/yellow] 个文件（记得 sync）")
        else:
            console.print(f"  ✅ 工作区: [green]干净[/green]")
    else:
        console.print("  ⚠️  未检测到 Git 仓库")

    # 项目 CLAUDE.md
    has_project_claude = False
    for p in [".claude/PROJECT_SUMMARY.md", "CLAUDE.md"]:
        if Path(p).exists():
            has_project_claude = True
            break

    if has_project_claude:
        console.print(f"  📋 项目文档: [green]存在[/green] ✓")
    else:
        console.print(f"  📋 项目文档: [yellow]未检测到[/yellow] — 建议创建 CLAUDE.md")

    console.print("""
[bold cyan]二、建议的下一步[/bold cyan]""")

    if dirty:
        console.print("  → [bold yellow]先提交当前改动[/bold yellow]: xnow sync \"提交信息\"")
    elif has_project_claude:
        console.print("  → [bold green]一切就绪[/bold green]，可以开新对话继续开发")
    else:
        console.print("  → [bold]创建项目 CLAUDE.md[/bold]，方便新对话秒懂项目")

    console.print("""
[bold cyan]三、工作流速查[/bold cyan]

  [bold]日常开发[/bold]
    Claude Code 写代码 → [bold]xnow sync[/bold] → 开新对话继续

  [bold]什么时候开新对话？[/bold]
    • 当前功能点做完了 ✅
    • 聊了 15~20 轮了
    • AI 开始"忘记"前面的内容

  [bold]详细指南[/bold]
    → 见 docs/expert-workflow.md

  [bold]可用命令[/bold]
    xnow sync \"msg\"     提交 + 推送
    xnow verify           运行验证流程
    xnow sync-env         同步配置到 xiangge-env
    xnow status           项目状态
    xnow init             初始化项目
    xnow migrate up/down  数据库迁移
    xnow release patch    发布版本
    xnow balance          查 DeepSeek 余额
    xnow workflow         本指南
""")
    return True


def cmd_help(args: list[str]) -> bool:
    """显示帮助"""
    console.print("""
[bold cyan]XNOW 内置命令[/bold cyan]

[bold]/sync [提交信息][/bold]     提交代码并推送到 GitHub
[bold]/verify[/bold]               运行 .claude/tasks.json 验证流程
[bold]/sync-env[/bold]             同步 ~/.claude/ 配置到 xiangge-env 并推送
[bold]/status[/bold]               查看项目 git / 版本状态
[bold]/deploy[/bold]               部署前置检查（🟢 须确认后执行）
[bold]/init[/bold]                 初始化项目 → GitHub 仓库
[bold]/migrate <sub>[/bold]        数据库迁移管理（create/up/down/status）
[bold]/release <type>[/bold]       发布版本 (patch/minor/major)
[bold]/workflow[/bold]             查看工作流状态和指南
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
