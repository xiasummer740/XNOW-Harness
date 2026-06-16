"""XNOW-Harness — 配合 Claude Code 的辅助工具箱"""

import sys
import argparse
from .utils.display import show_info, show_error
from . import commands


def main():
    parser = argparse.ArgumentParser(
        description="XNOW-Harness — Claude Code 辅助工具箱",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  xnow sync "feat: 添加登录"     提交代码并推送
  xnow release patch             发布小版本
  xnow status                    查看项目状态
  xnow init                      初始化 GitHub 仓库
  xnow balance                   查看 DeepSeek 余额
  xnow workflow                  工作流状态和指南
        """,
    )
    parser.add_argument("command", nargs="?", default="help",
                        help="sync / release / status / init / balance")
    parser.add_argument("args", nargs="*", help="命令参数")

    args = parser.parse_args()

    if args.command == "help":
        parser.print_help()
        return

    if args.command == "balance":
        import sys
        from .utils.balance import get_usage_summary, format_full_status
        b = get_usage_summary()
        if b:
            text = format_full_status(b)
            sys.stdout.buffer.write((text + "\n").encode("utf-8"))
        else:
            show_error("余额查询失败（检查 API Key）")
        return

    # 委托给 commands 模块
    result = commands.handle_command(args.command, list(args.args))
    if result is None:
        show_error(f"未知命令: {args.command}")
        sys.exit(1)
