"""DeepSeek 余额查询

从 DeepSeek API 查询账户余额和用量信息。
"""

import os
import json
from datetime import datetime
from typing import Optional

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    import urllib.request


def get_balance(api_key: str = "") -> Optional[dict]:
    """查询 DeepSeek 账户余额"""
    if not api_key:
        # 兼容多个环境变量名
        api_key = (
            os.environ.get("DEEP_SEEK_API_KEY_FOR_BALANCE")
            or os.environ.get("DEEPSEEK_API_KEY")
            or ""
        )

    if not api_key:
        return None

    url = "https://api.deepseek.com/user/balance"

    if HAS_HTTPX:
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url, headers={"Authorization": f"Bearer {api_key}"})
                if resp.status_code == 200:
                    data = resp.json()
                    infos = data.get("balance_infos", [])
                    if infos:
                        info = infos[0]
                        total = float(info.get("total_balance", "0"))
                        granted = float(info.get("granted_balance", "0"))
                        topped = float(info.get("topped_up_balance", "0"))
                        return {"total": total, "granted": granted, "topped": topped}
        except Exception:
            return None
    else:
        try:
            req = urllib.request.Request(
                url,
                headers={"Authorization": f"Bearer {api_key}"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                infos = data.get("balance_infos", [])
                if infos:
                    info = infos[0]
                    return {
                        "total": float(info.get("total_balance", "0")),
                        "granted": float(info.get("granted_balance", "0")),
                        "topped": float(info.get("topped_up_balance", "0")),
                    }
        except Exception:
            return None

    return None


def format_balance(balance_info: Optional[dict]) -> str:
    """格式化余额为显示文本"""
    if not balance_info:
        return "💰 -- (未配置 API Key)"

    total = balance_info.get("total", 0)
    topped = balance_info.get("topped", 0)

    # 判断颜色级别
    if total < 1:
        icon = "🔴"
    elif total < 6:
        icon = "🟡"
    else:
        icon = "💰"

    return f"{icon} ¥{total:.2f} (已充值 ¥{topped:.2f})"


def format_status_line(balance_info: Optional[dict], model: str = "") -> str:
    """格式化为状态行文本"""
    balance_str = format_balance(balance_info)
    model_str = f" | 🐳 {model}" if model else ""
    return f"{balance_str}{model_str}"


# ─── 用量追踪（与 statusline 工具共享状态） ───

STATE_DIR = os.path.join(os.path.expanduser("~"), ".deepseek-balance")
STATE_FILE = os.path.join(STATE_DIR, "state.json")


def _read_state() -> Optional[dict]:
    """读取用量状态"""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None


def _write_state(state: dict):
    """写入用量状态"""
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass


def get_usage_summary(api_key: str = "") -> Optional[dict]:
    """获取完整用量摘要（含余额、消耗、起始日期）"""
    balance = get_balance(api_key)
    if not balance:
        return None

    current_balance = balance["total"]
    state = _read_state()
    now = datetime.now().strftime("%Y-%m-%d")

    if not state:
        state = {
            "cumulativeSpent": 0,
            "lastBalance": current_balance,
            "since": now,
        }
        _write_state(state)
        spent = 0
        since = now
    else:
        consumption = max(0, state["lastBalance"] - current_balance)
        state["cumulativeSpent"] += consumption
        state["lastBalance"] = current_balance
        _write_state(state)
        spent = state["cumulativeSpent"]
        since = state.get("since", now)

    balance["spent"] = spent
    balance["since"] = since
    return balance


def _is_gbk() -> bool:
    """检测当前终端是否为 GBK 编码（Windows 中文）"""
    try:
        import sys
        return sys.stdout.encoding and sys.stdout.encoding.lower() in ("gbk", "gb2312", "cp936")
    except Exception:
        return False


def format_full_status(balance: Optional[dict], model: str = "") -> str:
    """格式化为完整状态信息（含余额、消耗、模型）"""
    ascii_mode = _is_gbk()

    if not balance:
        return "[Balance: query failed]" if ascii_mode else "💰 余额查询失败"

    total = balance.get("total", 0)
    spent = balance.get("spent", 0)
    since = balance.get("since", "?")

    if total < 1:
        icon = "🔴"
    elif total < 6:
        icon = "🟡"
    else:
        icon = "💰"

    parts = [f"{icon} ¥{total:.2f}"]
    if spent > 0:
        parts.append(f"💸 ¥{spent:.2f} (Since {since})")
    if model:
        parts.append(f"🐳 {model}")

    return " | ".join(parts)
