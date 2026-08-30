#!/usr/bin/env python3
"""ai-dev-env orchestrator.

Cross-platform (Windows / macOS / Linux). Requires Python 3.11+ — the bootstrap
scripts always invoke it as `uv run --python 3.12`, so `tomllib` is available.

Subcommands
-----------
report            (default) show every managed tool: installed?, purpose, usage
install [tools]   install missing tools; asks "confirm each" vs "install all"
config            create/show ~/.ai-dev-env/config.toml (fill in tokens here)
wire <harness>    install bundled skills + MCP + guidelines + plugins into a harness
guidelines        (re)install the always-on agent guidelines
skills            (re)install the bundled skills/ into Claude Code + Codex
plugins           (re)install external plugin ecosystems (e.g. superpowers)
doctor            run each tool's verify command and report pass/fail

Secrets (Notion token, …) go in ~/.ai-dev-env/config.toml — a file you own,
outside the repo clone. `wire` reads it and passes the values to each MCP server.
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
SKILLS_DIR = REPO / "skills"
CONFIG = Path(os.environ.get("AI_DEV_ENV_HOME") or Path.home() / ".ai-dev-env") / "config.toml"

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
def load_manifest() -> dict:
    with MANIFEST.open("rb") as fh:
        return tomllib.load(fh)


def load_tools() -> list[dict]:
    return load_manifest()["tool"]


def load_plugins() -> list[dict]:
    return load_manifest().get("plugin", [])


# ── local config (~/.ai-dev-env/config.toml) ───────────────────────────────
def env_required(t: dict) -> dict[str, str]:
    """{ENV_KEY: description} a tool's MCP server needs. Tolerates the old list form."""
    er = t.get("mcp", {}).get("env_required", {})
    return er if isinstance(er, dict) else {k: "" for k in er}


def all_required_env() -> dict[str, str]:
    out: dict[str, str] = {}
    for t in load_tools():
        out.update(env_required(t))
    return out


def load_config() -> dict:
    if not CONFIG.exists():
        return {}
    with CONFIG.open("rb") as fh:
        return tomllib.load(fh)


def config_env() -> dict[str, str]:
    """Filled-in [env] values from config.toml (blank entries dropped)."""
    return {k: v for k, v in load_config().get("env", {}).items() if isinstance(v, str) and v.strip()}


def resolved_env(keys) -> dict[str, str]:
    """Value for each key from config.toml first, then the process environment."""
    cfg = config_env()
    out = {}
    for k in keys:
        v = cfg.get(k) or os.environ.get(k)
        if v:
            out[k] = v
    return out


def missing_env(t: dict) -> list[str]:
    have = resolved_env(env_required(t))
    return [k for k in env_required(t) if k not in have]


def write_config_template() -> str:
    """Ensure config.toml has every required key, keeping existing values.
    Returns 'created', 'updated', or 'unchanged'."""
    was = CONFIG.exists()
    existing = load_config().get("env", {})
    req = all_required_env()
    lines = [
        "# ai-dev-env local config — this machine only, NOT in git.",
        "# Fill in the values below, then re-run:  setup.py wire <harness>",
        "",
        "[env]",
    ]
    for key, desc in req.items():
        if desc:
            for chunk in _wrap(desc, 74):
                lines.append(f"# {chunk}")
        val = existing.get(key, "")
        lines.append(f'{key} = "{val}"')
        lines.append("")
    text = "\n".join(lines).rstrip() + "\n"
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    if was and CONFIG.read_text(encoding="utf-8") == text:
        return "unchanged"
    CONFIG.write_text(text, encoding="utf-8")
    return "created" if not was else "updated"


def _wrap(s: str, width: int) -> list[str]:
    words, line, out = s.split(), "", []
    for w in words:
        if line and len(line) + 1 + len(w) > width:
            out.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        out.append(line)
    return out


GUIDE_BEGIN = "<!-- BEGIN ai-dev-env-guidelines -->"
GUIDE_END = "<!-- END ai-dev-env-guidelines -->"


def guidelines_text() -> str:
    rel = load_manifest().get("guidelines", {}).get("canonical", "guidelines/AGENTS.md")
    text = (REPO / rel).read_text(encoding="utf-8").lstrip()
    # drop the repo-maintenance HTML comment header, if present
    if text.startswith("<!--") and "-->" in text:
        text = text[text.index("-->") + 3 :].lstrip()
    return text


def upsert_block(path: Path, body: str) -> str:
    """Insert or replace a marker-delimited block in a text file. Returns action."""
    block = f"{GUIDE_BEGIN}\n{body.rstrip()}\n{GUIDE_END}\n"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if GUIDE_BEGIN in text and GUIDE_END in text:
        pre = text[: text.index(GUIDE_BEGIN)]
        post = text[text.index(GUIDE_END) + len(GUIDE_END) :].lstrip("\n")
        new, action = pre + block + post, "updated"
    else:
        sep = "" if not text.strip() else (text if text.endswith("\n") else text + "\n") + "\n"
        new, action = sep + block, "created" if not text.strip() else "appended"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(new, encoding="utf-8")
    return action


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


def run(cmd: str, display: str | None = None, **kw) -> int:
    print(dim(f"  $ {display if display is not None else cmd}"))
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
        for k in missing_env(t):
            print(f"  {yellow('needs config:')} {k} — fill in {CONFIG}")
        doc = t.get("docs", "")
        if doc and not doc.startswith("http"):
            print(f"  {dim('docs:')} {REPO / doc}")
        print()
    missing = [t["id"] for t in tools if not is_installed(t)]
    if missing:
        print(yellow(f"missing: {', '.join(missing)}   →   python scripts/setup.py install"))
    else:
        print(green("all managed tools installed"))

    # guidelines status
    claude_agents = Path.home() / ".claude" / "AGENTS.md"
    have = claude_agents.exists() and GUIDE_BEGIN in claude_agents.read_text(encoding="utf-8")
    print(f"\n{bold('Agent guidelines'):<28} {green('● installed') if have else red('○ not installed')}")
    print("  Always-on behavioral rules (AGENTS.md canonical, CLAUDE.md references it).")
    print(f"  {dim('install:')} python scripts/setup.py guidelines")

    # bundled skills
    skills = bundled_skills()
    print(f"\n{bold('Bundled skills'):<28} {', '.join(s.name for s in skills) if skills else dim('(none in skills/)')}")
    if skills:
        print(f"  {dim('install:')} python scripts/setup.py skills")

    # external plugins
    plugins = load_plugins()
    if plugins:
        print(f"\n{bold('External plugins')}")
        for p in plugins:
            print(f"  {bold(p['id']):<26} {p['purpose'][:90]}…")
        print(f"  {dim('install:')} python scripts/setup.py plugins  (per-harness; some are interactive)")

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


def mcp_spec(t: dict) -> tuple[str, list[str]]:
    """(command, args) for this tool's MCP server, with a per-OS override applied."""
    m = {**t["mcp"], **t["mcp"].get(OS, {})}
    return m["command"], list(m.get("args", []))


def _warn_missing_env(t: dict) -> None:
    miss = missing_env(t)
    if not miss:
        return
    for k in miss:
        print(yellow(f"  {t['id']}: {k} not set — server registered but idle until you fill it in"))
    print(dim(f"      {CONFIG}   (then re-run: setup.py wire <harness>)"))
    if t.get("setup"):
        print(dim(f"      {t['setup']}"))


def _mcp_env(t: dict, flag: str) -> tuple[str, str]:
    """(real, masked) '<flag> K=V' string: non-secret [tool.env] + resolved required secrets."""
    pairs = list(t.get("env", {}).items()) + list(resolved_env(env_required(t)).items())
    secret = set(env_required(t))
    real = " ".join(f"{flag} {k}={v}" for k, v in pairs)
    masked = " ".join(f"{flag} {k}={'***' if k in secret else v}" for k, v in pairs)
    return real, masked


def bundled_skills() -> list[Path]:
    """Every skills/<name>/ folder in the repo that has a SKILL.md."""
    if not SKILLS_DIR.is_dir():
        return []
    return sorted(d for d in SKILLS_DIR.iterdir() if d.is_dir() and (d / "SKILL.md").is_file())


def _install_skills(dest_root: Path) -> None:
    skills = bundled_skills()
    if not skills:
        print(dim("  skills: none bundled in skills/"))
        return
    dest_root.mkdir(parents=True, exist_ok=True)
    for src in skills:
        dst = dest_root / src.name
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        print(green(f"  skill  → {dst}"))


CLAUDE_REF = (
    "# Agent guidelines\n\n"
    "Follow every guideline in `~/.claude/AGENTS.md` (shared cross-harness rules: "
    "think before coding, simplicity first, surgical changes, goal-driven execution)."
)


def _codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))


def _install_guidelines(harness: str) -> None:
    """Install the always-on behavioral guidelines into a harness's instruction file.

    AGENTS.md carries the full text; CLAUDE.md only references it.
    All edits are marker-delimited and idempotent.
    """
    body = guidelines_text()
    if harness == "claude-code":
        home = Path.home() / ".claude"
        a = upsert_block(home / "AGENTS.md", body)
        c = upsert_block(home / "CLAUDE.md", CLAUDE_REF)
        print(green(f"  guidelines → {home / 'AGENTS.md'} ({a}),  {home / 'CLAUDE.md'} ({c}, reference only)"))
    elif harness == "codex":
        p = _codex_home() / "AGENTS.md"
        print(green(f"  guidelines → {p} ({upsert_block(p, body)})"))
    elif harness == "gemini-cli":
        p = Path.home() / ".gemini" / "GEMINI.md"
        print(green(f"  guidelines → {p} ({upsert_block(p, body)})"))
    elif harness == "cursor":
        print(dim(f"  guidelines: add {REPO / 'guidelines' / 'AGENTS.md'} as a project AGENTS.md"))
        print(dim("             or .cursor/rules/agents.mdc (alwaysApply: true)"))
    else:
        print(dim(f"  guidelines: load {REPO / 'guidelines' / 'AGENTS.md'} as always-on context"))


def _install_plugins(harness: str) -> None:
    plugins = load_plugins()
    if not plugins:
        return
    for p in plugins:
        cmd = p.get("install", {}).get(harness)
        if not cmd:
            print(dim(f"  plugin {p['id']}: no install path for {harness}"))
            continue
        if cmd.lstrip().startswith("#"):
            print(yellow(f"  plugin {p['id']}: {cmd.lstrip('# ').strip()}"))
            continue
        rc = run(cmd)
        print((green if rc == 0 else red)(f"  plugin {p['id']} {'installed' if rc == 0 else 'FAILED — install manually'}"))


def wire_claude_code(tools) -> int:
    if shutil.which("claude") is None:
        print(red("  `claude` CLI not found — is Claude Code installed?"))
        return 1
    _install_skills(Path.home() / ".claude" / "skills")
    for t in _mcp_tools(tools):
        command, arglist = mcp_spec(t)
        args = " ".join(arglist)
        # -e/--env is variadic, so it must come *after* the server name.
        env, env_masked = _mcp_env(t, "-e")
        subprocess.run(f'claude mcp remove {t["id"]} -s user', shell=True, capture_output=True)
        base = f'claude mcp add --scope user {t["id"]} {{}} -- {command} {args}'
        run(" ".join(base.format(env).split()), display=" ".join(base.format(env_masked).split()))
        _warn_missing_env(t)
    print(dim("  (graphify registers its own skill: run `graphify install --platform claude`)"))
    return 0


def wire_codex(tools) -> int:
    if shutil.which("codex") is None:
        print(red("  `codex` CLI not found."))
        return 1
    codex_home = _codex_home()
    _install_skills(codex_home / "skills")
    for t in _mcp_tools(tools):
        command, arglist = mcp_spec(t)
        args = " ".join(arglist)
        env, env_masked = _mcp_env(t, "--env")
        cmd = shutil.which(command) or command
        # `codex mcp add [--env K=V] <name> -- <cmd> <args>` — overwrites cleanly.
        base = f'codex mcp add {{}} {t["id"]} -- {cmd} {args}'
        if run(" ".join(base.format(env).split()), display=" ".join(base.format(env_masked).split())) != 0:
            print(yellow(f"  `codex mcp add` failed for {t['id']} — add manually to {codex_home}/config.toml"))
        _warn_missing_env(t)
    print(dim("  graphify: run `graphify install --platform codex`"))
    return 0


def _print_bundled_skills() -> None:
    skills = bundled_skills()
    if skills:
        print(dim("  bundled skills (wire manually — no native skills dir):"))
        for s in skills:
            print(dim(f"    {s / 'SKILL.md'}"))


def wire_cursor(tools) -> int:
    _print_mcp_json(tools, Path.home() / ".cursor" / "mcp.json")
    _print_bundled_skills()
    print(dim("  graphify: run `graphify install --platform cursor`"))
    return 0


def wire_gemini(tools) -> int:
    _print_mcp_json(tools, Path.home() / ".gemini" / "settings.json", key="mcpServers")
    _print_bundled_skills()
    print(dim("  graphify: run `graphify install --platform gemini`"))
    return 0


def _print_mcp_json(tools, path: Path, key: str = "mcpServers") -> None:
    import json

    block = {}
    for t in _mcp_tools(tools):
        command, arglist = mcp_spec(t)
        entry = {"command": command, "args": arglist}
        if t.get("env"):
            entry["env"] = t["env"]
        for k in t.get("mcp", {}).get("env_required", []):
            entry.setdefault("env", {})[k] = f"${{{k}}}"
        block[t["id"]] = entry
    print(bold(f"\n  merge into {path} :\n"))
    print(json.dumps({key: block}, indent=2))
    print()


def wire_generic(tools) -> int:
    _print_mcp_json(tools, Path("<your-client-mcp-config>"))
    _print_bundled_skills()
    return 0


WIRERS = {
    "claude-code": wire_claude_code,
    "codex": wire_codex,
    "cursor": wire_cursor,
    "gemini-cli": wire_gemini,
    "generic": wire_generic,
}


def cmd_config(_args) -> int:
    state = write_config_template()
    print(bold("\nlocal config\n"))
    print(f"  {CONFIG}   {dim(f'({state})')}")
    have, need = config_env(), all_required_env()
    for k in need:
        state = green("set") if k in have else yellow("empty — fill this in")
        print(f"  {k:<20} {state}")
    if not need:
        print(dim("  no tools need any config values"))
    else:
        print(dim("\n  edit the file, then: setup.py wire <harness>"))
    return 0


def cmd_wire(args) -> int:
    fn = WIRERS.get(args.harness)
    if not fn:
        print(red(f"unknown harness '{args.harness}'. choices: {', '.join(WIRERS)}"))
        return 2
    if write_config_template() == "created":
        print(dim(f"created {CONFIG} — fill in any tokens and re-run for them to take effect"))
    print(bold(f"\nwiring ai-dev-env into {args.harness}\n"))
    rc = fn(load_tools())
    _install_guidelines(args.harness)
    _install_plugins(args.harness)
    return rc


def cmd_guidelines(args) -> int:
    targets = [args.harness] if args.harness else ["claude-code", "codex", "gemini-cli"]
    print(bold("\ninstalling agent guidelines\n"))
    for h in targets:
        print(dim(h))
        _install_guidelines(h)
    return 0


def cmd_plugins(args) -> int:
    targets = [args.harness] if args.harness else ["claude-code"]
    print(bold("\ninstalling external plugins\n"))
    for h in targets:
        print(dim(h))
        _install_plugins(h)
    return 0


def cmd_skills(args) -> int:
    print(bold("\ninstalling bundled skills\n"))
    if args.harness in (None, "claude-code") and shutil.which("claude"):
        print(dim("claude-code"))
        _install_skills(Path.home() / ".claude" / "skills")
    if args.harness in (None, "codex") and shutil.which("codex"):
        print(dim("codex"))
        _install_skills(_codex_home() / "skills")
    if args.harness and args.harness not in ("claude-code", "codex"):
        _print_bundled_skills()
    return 0


# ── doctor ─────────────────────────────────────────────────────────────────
def cmd_doctor(_args) -> int:
    rc = 0
    for t in load_tools():
        ok = is_installed(t)
        print(f"{green('PASS') if ok else red('FAIL')}  {t['name']:<24} {dim(t.get('verify',''))}")
        rc |= 0 if ok else 1
        for k in missing_env(t):
            print(f"{yellow('WARN')}  {t['name']:<24} {k} missing — fill in {CONFIG}")
            if t.get("setup"):
                print(f"      {dim(t['setup'])}")
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

    sub.add_parser("config", help="create/show ~/.ai-dev-env/config.toml").set_defaults(fn=cmd_config)

    pw = sub.add_parser("wire", help="install bundled skills + MCP + guidelines into a harness")
    pw.add_argument("harness", choices=list(WIRERS))
    pw.set_defaults(fn=cmd_wire)

    pg = sub.add_parser("guidelines", help="install always-on agent guidelines (AGENTS.md + CLAUDE.md ref)")
    pg.add_argument("harness", nargs="?", choices=list(WIRERS), help="default: claude-code, codex, gemini-cli")
    pg.set_defaults(fn=cmd_guidelines, harness=None)

    ps = sub.add_parser("skills", help="install bundled skills/ into a harness")
    ps.add_argument("harness", nargs="?", choices=list(WIRERS), help="default: claude-code + codex")
    ps.set_defaults(fn=cmd_skills, harness=None)

    pp = sub.add_parser("plugins", help="install external plugin ecosystems (e.g. superpowers)")
    pp.add_argument("harness", nargs="?", choices=list(WIRERS), help="default: claude-code")
    pp.set_defaults(fn=cmd_plugins, harness=None)

    sub.add_parser("doctor", help="verify each tool").set_defaults(fn=cmd_doctor)

    args = p.parse_args()
    if not getattr(args, "fn", None):
        return cmd_report(args)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
