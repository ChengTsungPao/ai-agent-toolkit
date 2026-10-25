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

from _common import REPO, REPO_NAME, dim, green

STATUSLINE_TAG = f"{REPO_NAME}-statusline"
STATUSLINE_DIR = Path.home() / ".claude" / STATUSLINE_TAG
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
    """An interpreter prefix for wrapper.py — a bare command name, ready to prepend.

    Must NOT be an absolute quoted path. Claude Code on Windows runs the
    statusLine through `cmd.exe /c "<command>"`; when `<command>` both starts and
    ends with a quote, cmd strips that outer pair, and a leading `"C:\\...exe"`
    then becomes unbalanced → `The filename, directory name, or volume label
    syntax is incorrect`, exit 1, no output. A bare name (like the `bash` the
    previous implementation used) is resolved from PATH and sidesteps this.

    Prefers `uv` (the repo's one prerequisite); falls back to a *validated*
    system Python — Windows' `WindowsApps\\python3.exe` is a PATH stub that is
    not a working interpreter."""
    if shutil.which("uv"):
        return "uv run --python 3.12 --no-project"
    for c in ("python3", "python"):
        if not shutil.which(c):
            continue
        try:
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            r = subprocess.run([c, "--version"], capture_output=True, text=True, timeout=5, creationflags=flags)
        except (OSError, subprocess.SubprocessError):
            continue
        if r.returncode == 0 and (r.stdout + r.stderr).startswith("Python "):
            return c
    return "python"


def _statusline_command() -> str:
    # wrapper.py is quoted (may contain spaces) but is never the leading token,
    # so cmd.exe's outer-quote stripping can't unbalance it.
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
    if STATUSLINE_TAG not in cur:
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
