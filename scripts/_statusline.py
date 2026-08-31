"""`setup.py statusline` — install / remove the Claude Code context-usage segment.

Claude Code specific and self-contained; the runtime scripts it installs live in
`contrib/statusline/` (`wrapper.py` + `ctx.py`). Kept out of setup.py because it
touches a different config surface (`~/.claude/settings.json`) than everything
else and belongs conceptually with `contrib/`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from _common import REPO, dim, green

STATUSLINE_DIR = Path.home() / ".claude" / "ai-dev-env-statusline"
_CLAUDE_SETTINGS = Path.home() / ".claude" / "settings.json"


def _load_claude_settings() -> dict:
    if not _CLAUDE_SETTINGS.exists():
        return {}
    try:
        return json.loads(_CLAUDE_SETTINGS.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_claude_settings(d: dict) -> None:
    _CLAUDE_SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    _CLAUDE_SETTINGS.write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8")


def _statusline_python() -> str:
    """A stable interpreter prefix for wrapper.py — quoted, ready to prepend.

    Prefers `uv` (the one guaranteed prerequisite, at an absolute path) so the
    baked command doesn't depend on a transient venv or PATH ordering. Falls
    back to a *validated* system Python — Windows' `WindowsApps\\python3.exe` is
    a Store stub that resolves on PATH but is not a working interpreter."""
    uv = shutil.which("uv")
    if uv:
        return f'"{uv}" run --python 3.12 --no-project'
    for c in ("python3", "python"):
        p = shutil.which(c)
        if not p:
            continue
        try:
            r = subprocess.run([p, "--version"], capture_output=True, text=True, timeout=5)
        except (OSError, subprocess.SubprocessError):
            continue
        if r.returncode == 0 and (r.stdout + r.stderr).startswith("Python "):
            return f'"{p}"'
    return "python"


def _statusline_command() -> str:
    return f'{_statusline_python()} "{STATUSLINE_DIR / "wrapper.py"}"'


def cmd_statusline(args) -> int:
    settings = _load_claude_settings()
    prev_file = STATUSLINE_DIR / "statusline-prev.txt"

    if args.off:
        prev = prev_file.read_text(encoding="utf-8").strip() if prev_file.exists() else ""
        if prev:
            settings["statusLine"] = {"type": "command", "command": prev}
            print(dim(f"restored previous statusLine: {prev[:60]}…"))
        else:
            settings.pop("statusLine", None)
            print(dim("removed statusLine"))
        _save_claude_settings(settings)
        shutil.rmtree(STATUSLINE_DIR, ignore_errors=True)
        print(green("statusline off"))
        return 0

    src = REPO / "contrib" / "statusline"
    STATUSLINE_DIR.mkdir(parents=True, exist_ok=True)
    for name in ("wrapper.py", "ctx.py"):
        dst = STATUSLINE_DIR / name
        shutil.copy2(src / name, dst)
        try:
            dst.chmod(0o755)
        except OSError:
            pass
    # a stale statusline.sh from an older install would never be run again
    (STATUSLINE_DIR / "statusline.sh").unlink(missing_ok=True)

    cur = (settings.get("statusLine") or {}).get("command", "")
    if "ai-dev-env-statusline" not in cur:
        prev_file.write_text(cur, encoding="utf-8")  # empty if there was none
        if cur:
            print(dim(f"chaining to existing statusLine ({len(cur)} chars saved)"))
    elif not prev_file.exists():
        prev_file.write_text("", encoding="utf-8")

    our_cmd = _statusline_command()
    settings["statusLine"] = {"type": "command", "command": our_cmd}
    _save_claude_settings(settings)
    print(green(f"  statusline → {STATUSLINE_DIR}"))
    print(green(f"  {_CLAUDE_SETTINGS} statusLine → {our_cmd}"))
    print(dim("  shows ' | ctx NN%' at the bottom next turn (restart the session if not)"))
    print(dim("  if a host (Orca) rewrites settings.json, re-run: setup.py statusline"))
    return 0
