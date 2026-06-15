"""XNOW Harness 终端显示（Windows GBK 兼容）"""

from rich.console import Console
from rich.text import Text
from rich.prompt import Confirm

console = Console()

XNOW_LOGO = """
+------------------------------+
| XNOW-Harness                 |
| Claude Code                  |
+------------------------------+
"""


def show_banner():
    banner = Text(XNOW_LOGO)
    banner.stylize("bold cyan")
    console.print(banner)


def show_info(msg: str):
    console.print(f"  i  {msg}", style="dim white")


def show_step(msg: str):
    console.print(f"  -> {msg}", style="cyan")


def show_ok(msg: str):
    console.print(f"  OK {msg}", style="green")


def show_warn(msg: str):
    console.print(f"  !! {msg}", style="yellow")


def show_error(msg: str):
    console.print(f"  XX {msg}", style="bold red")


def ask_confirm(msg: str, default: bool = True) -> bool:
    return Confirm.ask(f"  [?] {msg}", default=default)
