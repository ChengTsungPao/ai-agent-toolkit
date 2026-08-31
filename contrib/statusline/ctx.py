"""The context-usage segment for the Claude Code statusLine.

`segment(payload)` returns ` | ctx NN% (842k/1m)` (coloured green / yellow / red)
for a statusLine JSON payload, or `''` on any problem. Never raises. `payload`
may be `bytes` or `str` — the raw payload can carry non-UTF-8 sequences, so it is
decoded here with `errors="replace"` rather than by the caller's locale.
"""

import json
import sys


def _window(model_id: str) -> int:
    m = (model_id or "").lower()
    if "haiku" in m:
        return 200_000
    if "-5" in m or "[1m]" in m:  # the 5 family + any explicit 1m tag
        return 1_000_000
    return 200_000


def segment(payload) -> str:
    try:
        if isinstance(payload, (bytes, bytearray)):
            payload = payload.decode("utf-8", "replace")
        data = json.loads(payload)
    except Exception:
        return ""
    if not isinstance(data, dict):
        return ""
    win = _window((data.get("model") or {}).get("id", ""))
    tp = data.get("transcript_path")
    if not tp:
        return ""
    try:
        with open(tp, encoding="utf-8", errors="replace") as fh:
            tail = fh.readlines()[-400:]
    except OSError:
        return ""
    used = 0
    for line in reversed(tail):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        u = (obj.get("message") or {}).get("usage") or obj.get("usage")
        if isinstance(u, dict) and u.get("input_tokens") is not None:
            used = (
                u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
            )
            break
    if not used:
        return ""
    pct = min(100, used * 100 // win)
    color = "\033[31m" if pct >= 85 else "\033[33m" if pct >= 70 else "\033[32m"
    win_s = "1m" if win >= 1_000_000 else f"{win // 1000}k"
    return f" \033[2m|\033[0m {color}ctx {pct}% ({used / 1000:.0f}k/{win_s})\033[0m"


def main() -> None:
    sys.stdout.buffer.write(segment(sys.stdin.buffer.read()).encode("utf-8"))


if __name__ == "__main__":
    main()
