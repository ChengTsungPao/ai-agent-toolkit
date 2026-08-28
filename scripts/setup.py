#!/usr/bin/env python3
"""ai-dev-env orchestrator.

Cross-platform (Windows / macOS / Linux). Requires Python 3.11+ — the bootstrap
scripts always invoke it as `uv run --python 3.12`, so `tomllib` is available.

Subcommands
-----------
report            (default) show every managed tool: installed?, purpose, usage
install [tools]   install missing tools; asks "confirm each" vs "install all"
wire <harness>    register the skill + MCP servers into a harness
doctor            run each tool's verify command and report pass/fail

Nothing here is destructive. `install` always prints a plan and asks first.
"""
from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "manifest.toml"
SKILL_DIR = REPO / "skills" / "ai-dev-env"

OS = {"Windows": "windows", "Darwin": "macos", "Linux": "linux"}.get(platform.system(), "linux")
IS_WINDOWS = OS == "windows"


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


# ── manifest ────────────────────────────────────────────────────────────────
def load_tools() -> list[dict]:
    with MANIFEST.open("rb") as fh:
        return tomllib.load(fh)["tool"]


def install_cmd(tool: dict) -> str | None:
    ins = tool.get("install", {})
    return ins.get(OS) or ins.get("default")


def post_install_cmd(tool: dict) -> str | None:
    p = tool.get("post_install", {})
    return p.get(OS) or p.get("default")


def is_installed(tool: dict) -> bool:
    verify = tool.get("verify")
    if not verify:
        return shutil.which(tool["id"]) is not None
    exe = verify.split()[0]
    if shutil.which(exe) is None:
        return False
    try:
        return subprocess.run(verify, shell=True, capture_output=True, timeout=30).returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def version_of(tool: dict) -> str:
    verify = tool.get("verify")
    if not verify:
        return ""
    try:
        r = subprocess.run(verify, shell=True, capture_output=True, text=True, timeout=30)
        return (r.stdout or r.stderr).strip().splitlines()[0][:60] if r.returncode == 0 else ""
    except (subprocess.TimeoutExpired, OSError, IndexError):
        return ""


def run(cmd: str, **kw) -> int:
    print(dim(f"  $ {cmd}"))
    return subprocess.run(cmd, shell=True, **kw).returncode


# ── report ─────────────────────────────────────────────────────────────────
def cmd_report(_args) -> int:
    tools = load_tools()
    print(bold(f"\nai-dev-env  ·  {platform.system()}  ·  repo: {REPO}\n"))
    for t in tools:
        ok = is_installed(t)
        mark = green("● installed") if ok else red("○ missing")
        ver = version_of(t) if ok else ""
        print(f"{bold(t['name']):<28} {mark}  {dim(ver)}")
        print(f"  {t['purpose']}")
        usage = t.get("usage", {}).get("short")
        if usage:
            print(f"  {dim('use:')} {usage}")
        doc = t.get("docs", "")
        if doc and not doc.startswith("http"):
            print(f"  {dim('docs:')} {REPO / doc}")
        print()
    missing = [t["id"] for t in tools if not is_installed(t)]
    if missing:
        print(yellow(f"missing: {', '.join(missing)}   →   python scripts/setup.py install"))
    else:
        print(green("all managed tools installed"))
    print(dim("\nharness wiring:  python scripts/setup.py wire <claude-code|codex|cursor|gemini-cli|generic>"))
    return 0


# ── install ────────────────────────────────────────────────────────────────
def _persist_env(key: str, value: str) -> None:
    """Best-effort persist an env var for future shells."""
    os.environ[key] = value
    if IS_WINDOWS:
        subprocess.run(f'setx {key} "{value}"', shell=True, capture_output=True)
        return
    marker = f"# ai-dev-env: {key}"
    line = f'export {key}="{value}"  {marker}\n'
    for rc in ("~/.zprofile", "~/.bash_profile", "~/.profile"):
        p = Path(rc).expanduser()
        try:
            existing = p.read_text() if p.exists() else ""
            if marker not in existing:
                p.write_text(existing + ("" if existing.endswith("\n") or not existing else "\n") + line)
        except OSError:
            pass


def cmd_install(args) -> int:
    tools = load_tools()
    wanted = args.tools or [t["id"] for t in tools]
    todo = [t for t in tools if t["id"] in wanted and not is_installed(t)]
    already = [t["id"] for t in tools if t["id"] in wanted and is_installed(t)]

    if already:
        print(dim(f"already installed: {', '.join(already)}"))
    if not todo:
        print(green("nothing to install."))
        return 0

    print(bold("\nplanned installs:"))
    for t in todo:
        print(f"  • {bold(t['name'])} — {install_cmd(t) or '(no install command!)'}")
        if t.get("env"):
            print(dim(f"      env: {', '.join(f'{k}={v}' for k, v in t['env'].items())}"))
    print()

    mode = args.mode
    if not mode:
        ans = input("install [a]ll, confirm [e]ach, or [c]ancel? ").strip().lower()
        mode = {"a": "all", "all": "all", "e": "each", "c": "cancel"}.get(ans, "cancel")
    if mode == "cancel":
        print("cancelled.")
        return 1

    rc = 0
    for t in todo:
        if mode == "each":
            if input(f"install {t['name']}? [y/N] ").strip().lower() not in ("y", "yes"):
                print(dim("  skipped"))
                continue
        cmd = install_cmd(t)
        if not cmd:
            print(red(f"  no install command for {t['id']} on {OS}"))
            rc = 1
            continue
        if run(cmd) != 0:
            print(red(f"  install failed: {t['id']}"))
            rc = 1
            continue
        for k, v in t.get("env", {}).items():
            _persist_env(k, v)
        post = post_install_cmd(t)
        if post:
            run(post, capture_output=True)
    print()
    print(green("done.") if rc == 0 else red("finished with errors."))
    if rc == 0:
        print(dim("next: python scripts/setup.py wire <harness>"))
    return rc


# ── wire ───────────────────────────────────────────────────────────────────
def _mcp_tools(tools) -> list[dict]:
    return [t for t in tools if t.get("mcp")]


def _copy_skill(dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SKILL_DIR / "SKILL.md", dest / "SKILL.md")
    print(green(f"  skill  → {dest / 'SKILL.md'}"))


def wire_claude_code(tools) -> int:
    if shutil.which("claude") is None:
        print(red("  `claude` CLI not found — is Claude Code installed?"))
        return 1
    _copy_skill(Path.home() / ".claude" / "skills" / "ai-dev-env")
    for t in _mcp_tools(tools):
        m = t["mcp"]
        env = " ".join(f"-e {k}={v}" for k, v in t.get("env", {}).items())
        args = " ".join(m.get("args", []))
        run(f'claude mcp add --scope user {env} {t["id"]} -- {m["command"]} {args}'.replace("  ", " "))
    print(dim("  (graphify registers its own skill: run `graphify install --platform claude`)"))
    return 0


def wire_codex(tools) -> int:
    if shutil.which("codex") is None:
        print(red("  `codex` CLI not found."))
        return 1
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    _copy_skill(codex_home / "skills" / "ai-dev-env")
    for t in _mcp_tools(tools):
        m = t["mcp"]
        args = " ".join(m.get("args", []))
        env = " ".join(f"--env {k}={v}" for k, v in t.get("env", {}).items())
        # `codex mcp add <name> [--env K=V] -- <cmd> <args>`
        if run(f'codex mcp add {env} {t["id"]} -- {shutil.which(m["command"]) or m["command"]} {args}') != 0:
            print(yellow(f"  `codex mcp add` failed for {t['id']} — add manually to {codex_home}/config.toml"))
    print(dim("  graphify: run `graphify install --platform codex`"))
    return 0


def wire_cursor(tools) -> int:
    home = Path.home()
    mcp_json = home / ".cursor" / "mcp.json"
    _print_mcp_json(tools, mcp_json)
    print(dim(f"  add project rule: .cursor/rules/ai-dev-env.mdc  (copy from {SKILL_DIR / 'SKILL.md'})"))
    print(dim("  graphify: run `graphify install --platform cursor`"))
    return 0


def wire_gemini(tools) -> int:
    settings = Path.home() / ".gemini" / "settings.json"
    _print_mcp_json(tools, settings, key="mcpServers")
    print(dim("  add context: ~/.gemini/GEMINI.md  (point it at the skill)"))
    print(dim("  graphify: run `graphify install --platform gemini`"))
    return 0


def _print_mcp_json(tools, path: Path, key: str = "mcpServers") -> None:
    import json

    block = {
        t["id"]: {"command": t["mcp"]["command"], "args": t["mcp"].get("args", []), **({"env": t["env"]} if t.get("env") else {})}
        for t in _mcp_tools(tools)
    }
    print(bold(f"\n  merge into {path} :\n"))
    print(json.dumps({key: block}, indent=2))
    print()


def wire_generic(tools) -> int:
    _print_mcp_json(tools, Path("<your-client-mcp-config>"))
    print(f"  skill body to load as context/rules: {SKILL_DIR / 'SKILL.md'}")
    return 0


WIRERS = {
    "claude-code": wire_claude_code,
    "codex": wire_codex,
    "cursor": wire_cursor,
    "gemini-cli": wire_gemini,
    "generic": wire_generic,
}


def cmd_wire(args) -> int:
    fn = WIRERS.get(args.harness)
    if not fn:
        print(red(f"unknown harness '{args.harness}'. choices: {', '.join(WIRERS)}"))
        return 2
    print(bold(f"\nwiring ai-dev-env into {args.harness}\n"))
    return fn(load_tools())


# ── doctor ─────────────────────────────────────────────────────────────────
def cmd_doctor(_args) -> int:
    rc = 0
    for t in load_tools():
        ok = is_installed(t)
        print(f"{green('PASS') if ok else red('FAIL')}  {t['name']:<24} {dim(t.get('verify',''))}")
        rc |= 0 if ok else 1
    return rc


# ── main ───────────────────────────────────────────────────────────────────
def main() -> int:
    p = argparse.ArgumentParser(prog="setup.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("report", help="show managed tools (default)").set_defaults(fn=cmd_report)

    pi = sub.add_parser("install", help="install missing tools")
    pi.add_argument("tools", nargs="*", help="tool ids (default: all)")
    g = pi.add_mutually_exclusive_group()
    g.add_argument("--all", dest="mode", action="store_const", const="all", help="install everything, no per-item prompt")
    g.add_argument("--each", dest="mode", action="store_const", const="each", help="confirm each tool")
    pi.set_defaults(fn=cmd_install, mode=None)

    pw = sub.add_parser("wire", help="register skill + MCP into a harness")
    pw.add_argument("harness", choices=list(WIRERS))
    pw.set_defaults(fn=cmd_wire)

    sub.add_parser("doctor", help="verify each tool").set_defaults(fn=cmd_doctor)

    args = p.parse_args()
    if not getattr(args, "fn", None):
        return cmd_report(args)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
