"""Shared kernel for setup.py and its sibling modules — constants, ANSI, run().

stdlib-only, Python 3.11+. Kept deliberately tiny: this is the one thing every
sibling module (`_statusline.py`, and any future `contrib` extraction) may
import, so `setup.py` stays the single orchestrator without a circular import.
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REPO_NAME = REPO.name
ENV_HOME = f"{REPO_NAME.upper().replace('-', '_')}_HOME"
CONFIG_DISPLAY = f"~/.{REPO_NAME}/config.toml"
MANIFEST = REPO / "manifest.toml"
SKILLS_DIR = REPO / "skills"
CONFIG = Path(os.environ.get(ENV_HOME) or Path.home() / f".{REPO_NAME}") / "config.toml"

OS = {"Windows": "windows", "Darwin": "macos", "Linux": "linux"}.get(platform.system(), "linux")
IS_WINDOWS = OS == "windows"
WIN_FLAGS = {"creationflags": subprocess.CREATE_NO_WINDOW} if IS_WINDOWS else {}  # no console pop-ups

if IS_WINDOWS:
    os.system("")  # enable ANSI escape processing in the Windows console
# The output uses box-drawing / bullet glyphs; force UTF-8 so it survives a
# non-UTF-8 Windows console or a redirected pipe (cp1252 would raise).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


# ── ansi ────────────────────────────────────────────────────────────────────
def _c(code: str, s: str) -> str:
    if os.environ.get("NO_COLOR") or not sys.stdout.isatty():
        return s
    return f"\033[{code}m{s}\033[0m"


bold = lambda s: _c("1", s)
green = lambda s: _c("32", s)
red = lambda s: _c("31", s)
yellow = lambda s: _c("33", s)
dim = lambda s: _c("2", s)


def run(cmd: str, display: str | None = None, **kw) -> int:
    print(dim(f"  $ {display if display is not None else cmd}"))
    if sys.platform == "win32" and "creationflags" not in kw:
        kw["creationflags"] = subprocess.CREATE_NO_WINDOW
    return subprocess.run(cmd, shell=True, **kw).returncode


CODEX_HOME_ENV = f"{ENV_HOME.removesuffix('_HOME')}_CODEX_HOME"  # AI_AGENT_TOOLKIT_CODEX_HOME


def codex_home() -> Path:
    """The Codex config folder to wire: ~/.codex, or the folder named in $AI_AGENT_TOOLKIT_CODEX_HOME.

    The shell's own CODEX_HOME is deliberately not used: terminals and launchers set it per session to
    point Codex at a private copy of its config, and wiring that copy never reaches the real one."""
    override = os.environ.get(CODEX_HOME_ENV)
    return Path(override) if override else Path.home() / ".codex"


def use_codex_home() -> Path:
    """Export codex_home() so the `codex` commands we run (mcp add/remove) act on the same folder."""
    path = codex_home()
    os.environ["CODEX_HOME"] = str(path)
    return path


def agy_home() -> Path:
    """Antigravity's global customization root (skills/, mcp_config.json, AGENTS.md)."""
    return Path(os.environ.get("AGY_CONFIG_HOME", Path.home() / ".gemini" / "config"))
