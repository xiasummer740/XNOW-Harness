#!/usr/bin/env python3
"""XNOW-Harness 新电脑引导脚本

在新电脑上运行此脚本，自动恢复所有开发环境配置。
依赖: Python 3.10+, Git, Node.js 18+
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

GITHUB_USER = "xiasummer740"
REPO_NAME = "XNOW-Harness"


def step(msg): print(f"\n  → {msg}")
def ok(msg):   print(f"  ✓ {msg}")
def warn(msg): print(f"  ⚠ {msg}")
def err(msg):  print(f"  ✗ {msg}"); return False


def main():
    print("""
╔══════════════════════════════════════╗
║  XNOW · 新电脑引导                   ║
║  一个脚本恢复全部开发环境             ║
╚══════════════════════════════════════╝
""")

    # ─── 1. 环境检查 ───
    step("检查基础环境...")
    checks = [
        ("Python", sys.version.split()[0] if hasattr(sys, "version") else "?", lambda: sys.version_info >= (3, 10)),
        ("Git", _check_cmd("git --version"), lambda: True),
        ("Node.js", _check_cmd("node --version"), lambda: True),
        ("npm", _check_cmd("npm --version"), lambda: True),
    ]

    all_pass = True
    for name, ver, check in checks:
        if ver is None:
            warn(f"{name}: 未安装")
            all_pass = False
        elif check():
            ok(f"{name}: {ver}")
        else:
            warn(f"{name}: {ver} (版本可能过低)")

    if not all_pass:
        print("\n  请安装缺失的依赖后再运行")
        return

    # ─── 2. 克隆项目 ───
    target = Path.cwd() / REPO_NAME
    if target.exists():
        ok(f"XNOW-Harness 已存在: {target}")
        step("拉取最新代码...")
        subprocess.run(["git", "pull"], cwd=target, capture_output=True)
    else:
        step(f"克隆 XNOW-Harness...")
        result = subprocess.run(
            ["git", "clone", f"https://github.com/{GITHUB_USER}/{REPO_NAME}.git"],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            err(f"克隆失败: {result.stderr}")
            return
        ok("XNOW-Harness 已克隆")

    # ─── 3. 安装依赖 ───
    step("安装 Python 依赖...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(target / "requirements.txt")],
        capture_output=True,
    )
    ok("依赖已安装")

    # ─── 4. API Key 检测 ───
    step("检查 API Key...")
    api_key = os.environ.get("DEEP_SEEK_API_KEY_FOR_BALANCE") or os.environ.get("DEEPSEEK_API_KEY") or ""
    if api_key:
        ok("API Key 已配置")
    else:
        warn("未检测到 API Key")
        print("     XNOW-Harness 会自动读取 CC Switch 设置的密钥")
        print("     如果你用 CC Switch 管理密钥，请先启动 CC Switch")

    # ─── 5. Claude Code 配置提醒 (可选) ───
    step("Claude Code 配置参考")
    claude_dir = Path.home() / ".claude"
    if claude_dir.exists():
        ok("Claude Code 配置目录已存在")
    else:
        warn("未检测到 Claude Code 配置")
        print("     如果你使用 Claude Code，配置模板在: tools/claude-settings.template.json")

    # ─── 6. 验证 ───
    step("验证安装...")
    result = subprocess.run(
        [sys.executable, "-c", "from xnow_harness import __version__; print(__version__)"],
        capture_output=True, text=True, cwd=target,
    )
    if result.returncode == 0:
        ok(f"XNOW-Harness v{result.stdout.strip()} 就绪")
    else:
        err(f"验证失败: {result.stderr}")

    print(f"""
────────────────────────────────────────────
✅ 完成！现在可以启动:

  cd {REPO_NAME}
  python -m xnow_harness sync "feat: 试试xnow命令"

需要 Claude Code 配置？参考:
  tools/claude-settings.template.json

疑问？看 README.md
────────────────────────────────────────────
""")


def _check_cmd(cmd: str) -> str | None:
    """运行命令并返回输出版本字符串"""
    try:
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return result.stdout.strip().split("\n")[0]
    except Exception:
        pass
    return None


if __name__ == "__main__":
    main()
