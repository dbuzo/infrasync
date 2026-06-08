"""
utils.py — Hashing, formatting, and color helpers.
"""

import hashlib
from datetime import datetime, timezone


def sha256(content: str) -> str:
    """Compute SHA-256 hash of a string."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def now_iso() -> str:
    """Current UTC time as ISO string."""
    return datetime.now(timezone.utc).isoformat()


# ANSI colors for terminal output
class Colors:
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    CYAN = "\033[36m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def color_action(symbol: str, text: str) -> str:
    """Colorize plan output by action type."""
    if symbol == "+":
        return f"{Colors.GREEN}  {symbol} {text}{Colors.RESET}"
    elif symbol == "~":
        return f"{Colors.YELLOW}  {symbol} {text}{Colors.RESET}"
    elif symbol == "-":
        return f"{Colors.RED}  {symbol} {text}{Colors.RESET}"
    else:
        return f"    {text}"
