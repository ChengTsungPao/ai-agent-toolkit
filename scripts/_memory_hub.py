"""Personal Memory Hub support for `setup.py wire`: find the hub, and register its lifecycle hooks.

The hub is a separate repo (https://github.com/ChengTsungPao/personal-memory-hub). This module only
detects it and writes the harness config that points at its scripts; what a hook *does* lives in the
hub repo. See docs/memory-hub.md.

Config files are edited, never replaced: other hooks and settings are kept, a file that cannot be
parsed is left alone, and the previous content is saved next to it as `<file>.bak`.
"""

from __future__ import annotations

import json
import os
import shutil
import urllib.error
import urllib.request
from pathlib import Path

from _common import agy_home, codex_home, dim, green, yellow

HUB_ENV = (  # env the `memorycore` MCP entry carries, in this order
    "TDAI_ENDPOINT",
    "TDAI_KNOWLEDGE_ENDPOINT",
    "TDAI_SERVICE_ID",
    "TDAI_TEAM_ID",
    "TDAI_USER_ID",
    "TDAI_ADMIN_KEY_FILE",
    "TDAI_STATE_DIR",
    "TDAI_TIMEOUT_MS",
)
HOOK_SCRIPTS = ("memory-recall.mjs", "memory-capture.mjs")
EVENTS = ("SessionStart", "Stop")
NO_HUB = (Path("."), "node")  # stand-in hub for "remove": only the harness matters then


class ConfigError(Exception):
    """A harness config file exists but cannot be read as JSON."""


# ── finding the hub ─────────────────────────────────────────────────────────


def hub_server() -> tuple[Path, str] | None:
    """The hub's MCP server and node, when MemoryCore answers its health check; else None."""
    root = Path(os.environ.get("PERSONAL_MEMORY_HUB_DIR", Path.home() / "personal-memory-hub"))
    server = root / "agents" / "claude-code" / "mcp" / "server.mjs"
    node = shutil.which("node")
    if not server.is_file() or not node:
        return None
    endpoint = os.environ.get("TDAI_ENDPOINT", "http://127.0.0.1:8420").rstrip("/")
    try:
        with urllib.request.urlopen(f"{endpoint}/health", timeout=2) as response:
            if response.status != 200:
                return None
    except (OSError, urllib.error.URLError):
        return None
    return server, node


def fallback_env() -> dict:
    """The `memorycore` MCP env already registered in Claude Code, so wiring another harness keeps it."""
    path = Path.home() / ".claude.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return dict(data.get("mcpServers", {}).get("memorycore", {}).get("env", {}))
    except (OSError, ValueError, AttributeError):
        return {}


def memorycore_entry(hub: tuple[Path, str], existing_env: dict | None = None) -> dict:
    """The `memorycore` MCP entry: the environment wins, then the env already registered."""
    server, node = hub
    known = {**fallback_env(), **(existing_env or {})}
    env = {k: str(v) for k in HUB_ENV if (v := os.environ.get(k) or known.get(k))}
    entry = {"command": node, "args": [str(server)]}
    if env:
        entry["env"] = env
    return entry


# ── hook registration ───────────────────────────────────────────────────────


def _hub_root(hub: tuple[Path, str]) -> Path:
    return hub[0].parents[3]  # <root>/agents/claude-code/mcp/server.mjs


def _scripts(harness: str, hub: tuple[Path, str]) -> tuple[Path, Path]:
    """(recall, capture) scripts in the hub repo for a harness. Codex has no recall script of its own."""
    agents = _hub_root(hub) / "agents"
    if harness == "antigravity":
        return (
            agents / "antigravity" / "hooks" / "memory-recall.mjs",
            agents / "antigravity" / "hooks" / "memory-capture.mjs",
        )
    recall = agents / "claude-code" / "hooks" / "memory-recall.mjs"
    capture = agents / ("codex" if harness == "codex" else "claude-code") / "hooks" / "memory-capture.mjs"
    return recall, capture


def hooks_file(harness: str) -> Path | None:
    return {
        "claude-code": Path.home() / ".claude" / "settings.json",
        "codex": codex_home() / "hooks.json",
        "antigravity": agy_home() / "hooks.json",
    }.get(harness)


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig").strip() or "{}")
    except (OSError, ValueError) as e:
        raise ConfigError(f"{path} cannot be read as JSON ({e}); left unchanged") from e
    if not isinstance(value, dict):
        raise ConfigError(f"{path} is not a JSON object; left unchanged")
    return value


def _write_json(path: Path, before: dict, after: dict) -> bool:
    """Write `after` if it differs from `before`: keep the old file as .bak, replace atomically."""
    if after == before:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        shutil.copy2(path, path.with_name(path.name + ".bak"))
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(after, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return True


def _is_ours(entry) -> bool:
    return any(script in str(entry) for script in HOOK_SCRIPTS)


def _without_ours(cfg: dict, harness: str) -> dict:
    """A copy of cfg with the Memory Hub hooks taken out and everything else kept."""
    cfg = json.loads(json.dumps(cfg))
    if harness == "antigravity":
        cfg.pop("memory-hub", None)
        hooks = cfg.get("hooks")
        if isinstance(hooks, dict):
            hooks.pop("memory-hub", None)
            if not hooks:
                cfg.pop("hooks")
        return cfg
    hooks = cfg.get("hooks")
    if isinstance(hooks, dict):
        for event in EVENTS:
            if event in hooks:
                kept = [e for e in hooks[event] if not _is_ours(e)]
                if kept:
                    hooks[event] = kept
                else:
                    del hooks[event]
        if not hooks:
            cfg.pop("hooks")
    return cfg


def _command(path: Path) -> str:
    node = shutil.which("node") or "node"
    return f'{node} "{path}"'


def wire_hooks(harness: str, hub: tuple[Path, str], action: str = "install") -> int:
    """Register (or remove) the hub's SessionStart and Stop hooks for a harness. 0 = ok or nothing to do."""
    path = hooks_file(harness)
    if path is None:
        return 0
    try:
        before = _read_json(path)
        after = _without_ours(before, harness)
        if action == "install":
            recall, capture = _scripts(harness, hub)
            missing = [p for p in (recall, capture) if not p.is_file()]
            if missing:
                print(
                    yellow(
                        f"  Memory Hub hooks not installed for {harness}: {missing[0]} does not exist "
                        "(update the personal-memory-hub repo)"
                    )
                )
                return 1
            if harness == "antigravity":
                after["memory-hub"] = {
                    "SessionStart": [{"type": "command", "command": _command(recall), "timeout": 10}],
                    "Stop": [{"type": "command", "command": _command(capture), "timeout": 45}],
                }
            else:
                hooks = after.setdefault("hooks", {})
                hooks.setdefault("SessionStart", []).append(
                    {"matcher": "", "hooks": [{"type": "command", "command": _command(recall), "timeout": 10}]}
                )
                hooks.setdefault("Stop", []).append(
                    {"matcher": "", "hooks": [{"type": "command", "command": _command(capture), "timeout": 45}]}
                )
        changed = _write_json(path, before, after)
    except ConfigError as e:
        print(yellow(f"  Memory Hub hooks skipped: {e}"))
        return 1
    if action == "install":
        print(green(f"  Memory Hub hooks installed: {path}"))
    elif changed:
        print(dim(f"  Memory Hub hooks removed: {path}"))
    return 0
