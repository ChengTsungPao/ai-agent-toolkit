#!/usr/bin/env python3
"""ai-dev-env orchestrator.

Cross-platform (Windows / macOS / Linux). Requires Python 3.11+ — the bootstrap
scripts always invoke it as `uv run --python 3.12`, so `tomllib` is available.

manifest.toml has four sections; each subcommand acts on a subset:

  [guidelines]  1 table   ── guidelines,  wire
  [[tool]]      installs   ── install, doctor;  wire (if it has [tool.mcp])
  [[skill]]     git-cloned ── skills,  wire
  [[plugin]]    harness    ── plugins,  wire

Subcommands
-----------
report            (default) grouped status: MCP servers / CLI tools / Skills /
                  Plugins / Guidelines
bootstrap         fresh machine: install every tool, then wire every harness found
install [tools]   install missing [[tool]] entries; "confirm each" vs "install all"
upgrade [tools]   upgrade installed tools (uv tool upgrade / npm / installer) and
                  re-pull [[skill]] entries to their latest
config            create/show ~/.ai-dev-env/config.toml (fill in tokens here)
choose            pick which managed items to skip (writes config [skip].ids;
                  honoured by install / wire / skills / plugins)
statusline [--off] add / remove a 'ctx NN%' segment on the Claude Code statusLine
wire <harness>    everything for one harness: MCP servers + skills + guidelines + plugins
unwire <harness>  reverse of wire — remove MCP servers, skills, guidelines block
guidelines        (re)install the always-on agent guidelines
skills            (re)install skills — local skills/ folders + [[skill]] entries
                  ([[skill]] entries are re-cloned fresh, so this pulls their latest)
plugins           (re)install [[plugin]] ecosystems (e.g. superpowers)
doctor            run each [[tool]] verify command + flag missing config

Secrets (Notion token, …) go in ~/.ai-dev-env/config.toml — a file you own,
outside the repo clone. `wire` reads it and passes the values to each MCP server.
`install` always prints a plan and asks first. `unwire` is the only subcommand
that removes things, and only ever harness wiring — never an installed CLI or
your config.
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "manifest.toml"
SKILLS_DIR = REPO / "skills"
CONFIG = Path(os.environ.get("AI_DEV_ENV_HOME") or Path.home() / ".ai-dev-env") / "config.toml"

OS = {"Windows": "windows", "Darwin": "macos", "Linux": "linux"}.get(platform.system(), "linux")
IS_WINDOWS = OS == "windows"

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


# ── manifest ────────────────────────────────────────────────────────────────
SCHEMA_VERSION = 2
_schema_warned = False


def load_manifest() -> dict:
    global _schema_warned
    with MANIFEST.open("rb") as fh:
        m = tomllib.load(fh)
    if m.get("schema_version") != SCHEMA_VERSION and not _schema_warned:
        _schema_warned = True
        got = m.get("schema_version")
        print(yellow(f"note: manifest.toml schema_version={got!r}, expected {SCHEMA_VERSION}"), file=sys.stderr)
    return m


def load_tools() -> list[dict]:
    return load_manifest()["tool"]


def load_plugins() -> list[dict]:
    return load_manifest().get("plugin", [])


def ext_skills() -> list[dict]:
    """[[skill]] entries — external skills cloned fresh from git at install time."""
    return load_manifest().get("skill", [])


# ── local config (~/.ai-dev-env/config.toml) ───────────────────────────────
def env_required(t: dict) -> dict[str, str]:
    """{ENV_KEY: description} a tool's MCP server needs. Tolerates the old list form."""
    er = t.get("mcp", {}).get("env_required", {})
    return er if isinstance(er, dict) else dict.fromkeys(er, "")


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


def skipped_ids() -> set[str]:
    """Manifest ids the user has excluded from install / wire (config [skip].ids)."""
    ids = load_config().get("skip", {}).get("ids", [])
    return {str(i) for i in ids} if isinstance(ids, list) else set()


def _toml_kv(k: str, v) -> str:
    if isinstance(v, bool):
        return f"{k} = {str(v).lower()}"
    if isinstance(v, (int, float)):
        return f"{k} = {v}"
    if isinstance(v, list):
        return f"{k} = [" + ", ".join(f'"{x}"' for x in v) + "]"
    return f'{k} = "{v}"'


def _config_body(skip_override: list[str] | None = None) -> str:
    cfg = load_config()
    env = cfg.get("env", {})
    skip = skip_override if skip_override is not None else list(cfg.get("skip", {}).get("ids", []))
    managed = all_required_env()
    lines = [
        "# ai-dev-env local config — this machine only, NOT in git.",
        "",
        "# Secrets each MCP server needs. Fill in, then re-run: setup.py wire <harness>",
        "[env]",
    ]
    for key, desc in managed.items():
        for chunk in _wrap(desc, 74):
            lines.append(f"# {chunk}")
        lines.append(f'{key} = "{env.get(key, "")}"')
        lines.append("")
    extra_env = {k: v for k, v in env.items() if k not in managed}
    if extra_env:
        lines.append("# keys you added — not required by any current tool, kept as-is")
        lines += [_toml_kv(k, v) for k, v in extra_env.items()]
        lines.append("")
    lines += [
        "# Managed items to leave OUT of install / wire / skills / plugins.",
        "# ids come from `setup.py report`; edit here or run `setup.py choose`.",
        "[skip]",
        "ids = [" + ", ".join(f'"{i}"' for i in skip) + "]",
    ]
    for name, table in cfg.items():
        if name in ("env", "skip") or not isinstance(table, dict):
            continue
        lines += ["", "# your own table, kept as-is", f"[{name}]"]
        lines += [_toml_kv(k, v) for k, v in table.items()]
    return "\n".join(lines).rstrip() + "\n"


def write_config_template() -> str:
    """Ensure config.toml exists and matches the manifest, keeping existing
    values. Returns 'created', 'updated', or 'unchanged'."""
    was = CONFIG.exists()
    text = _config_body()
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    if was and CONFIG.read_text(encoding="utf-8") == text:
        return "unchanged"
    CONFIG.write_text(text, encoding="utf-8")
    return "created" if not was else "updated"


def set_skip(ids: list[str]) -> None:
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(_config_body(sorted(set(ids))), encoding="utf-8")


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
        if r.returncode != 0:
            return ""
        line = (r.stdout or r.stderr).strip().splitlines()[0][:60]
        return "" if line.lower().startswith(("usage", "options")) else line
    except (subprocess.TimeoutExpired, OSError, IndexError):
        return ""


def run(cmd: str, display: str | None = None, **kw) -> int:
    print(dim(f"  $ {display if display is not None else cmd}"))
    return subprocess.run(cmd, shell=True, **kw).returncode


# ── report ─────────────────────────────────────────────────────────────────
def _section(title: str) -> None:
    print(f"\n{bold(title)}\n{dim('─' * len(title))}")


def _report_tool(t: dict, skip: set[str]) -> None:
    if t["id"] in skip:
        mark, ver = dim("⊘ skipped"), ""
    else:
        ok = is_installed(t)
        mark = green("● installed") if ok else red("○ missing")
        ver = version_of(t) if ok else ""
    print(f"{bold(t['name']):<24} {mark}  {dim(ver)}")
    print(f"  {t['purpose']}")
    if t.get("usage", {}).get("short"):
        print(f"  {dim('use:')} {t['usage']['short']}")
    for k in missing_env(t):
        print(f"  {yellow('needs config:')} {k} — fill in {CONFIG}")
    doc = t.get("docs", "")
    if doc and not doc.startswith("http"):
        print(f"  {dim('docs:')} {REPO / doc}")
    print()


def _skip_tag(id_: str, skip: set[str]) -> str:
    return dim("  ⊘ skipped") if id_ in skip else ""


def cmd_report(_args) -> int:
    tools = load_tools()
    skip = skipped_ids()
    print(bold(f"\nai-dev-env  ·  {platform.system()}  ·  repo: {REPO}"))

    mcp = [t for t in tools if t.get("mcp")]
    cli = [t for t in tools if not t.get("mcp")]

    if mcp:
        _section("MCP servers")
        for t in mcp:
            _report_tool(t, skip)
    if cli:
        _section("CLI tools")
        for t in cli:
            _report_tool(t, skip)

    _section("Skills")
    for s in bundled_skills():
        print(f"{bold(s.name):<24} {dim('local (committed)')}{_skip_tag(s.name, skip)}")
    for s in ext_skills():
        origin = "/".join(s["repo"].rstrip("/").split("/")[-2:])
        print(f"{bold(s['id']):<24} {dim(f'external — latest from {origin}')}{_skip_tag(s['id'], skip)}")
    if not bundled_skills() and not ext_skills():
        print(dim("(none)"))
    print(f"  {dim('install:')} setup.py skills")

    plugins = load_plugins()
    if plugins:
        _section("Plugins")
        for p in plugins:
            print(f"{bold(p['id']):<24} {p['purpose'][:80]}…{_skip_tag(p['id'], skip)}")
        print(f"  {dim('install:')} setup.py plugins  (per-harness; some interactive)")

    _section("Guidelines")
    claude_agents = Path.home() / ".claude" / "AGENTS.md"
    have = claude_agents.exists() and GUIDE_BEGIN in claude_agents.read_text(encoding="utf-8")
    mark = green("● installed") if have else red("○ not installed")
    print(f"{'':<24} {mark}  {dim('AGENTS.md canonical, CLAUDE.md references it')}")
    print(f"  {dim('install:')} setup.py guidelines")

    missing = [t for t in tools if t["id"] not in skip and not is_installed(t)]
    missing_auto = [t["id"] for t in missing if install_cmd(t)]
    missing_manual = [t["id"] for t in missing if not install_cmd(t)]
    print()
    if skip:
        print(dim(f"skipped (config [skip]): {', '.join(sorted(skip))}   ·   change: setup.py choose"))
    if missing_auto:
        print(yellow(f"missing: {', '.join(missing_auto)}   →   setup.py install"))
    if missing_manual:
        print(yellow(f"missing (install yourself): {', '.join(missing_manual)}   →   see docs/"))
    if not missing:
        print(green("all tools installed"))
    print(dim("wire a harness:  setup.py wire <claude-code|codex|cursor|generic>"))
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
    _first_run_gate()
    tools = load_tools()
    skip = skipped_ids()
    # explicit `install <id>` overrides the skip list; a bare run honours it
    wanted = set(args.tools) if args.tools else {t["id"] for t in tools} - skip
    missing = [t for t in tools if t["id"] in wanted and not is_installed(t)]
    todo = [t for t in missing if install_cmd(t)]
    manual = [t for t in missing if not install_cmd(t)]
    already = [t["id"] for t in tools if t["id"] in wanted and is_installed(t)]
    left_out = sorted({t["id"] for t in tools} & skip - set(args.tools or []))

    if already:
        print(dim(f"already installed: {', '.join(already)}"))
    if left_out:
        print(dim(f"skipped (config [skip]): {', '.join(left_out)}"))
    if manual:
        print(yellow("install these yourself — no managed install command on this OS:"))
        for t in manual:
            doc = t.get("docs", "")
            hint = t.get("usage", {}).get("short") or (f"see {doc}" if doc else "")
            print(f"  • {bold(t['name'])}{f' — {hint}' if hint else ''}")
    if not todo:
        print(green("nothing to install automatically.") if manual else green("nothing to install."))
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
        if mode == "each" and input(f"install {t['name']}? [y/N] ").strip().lower() not in ("y", "yes"):
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
    skip = skipped_ids()
    return [t for t in tools if t.get("mcp") and t["id"] not in skip]


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


def managed_items() -> list[tuple[str, str]]:
    """(id, kind label) for everything install / wire can act on, in display order."""
    items = [(t["id"], "MCP server" if t.get("mcp") else "tool") for t in load_tools()]
    items += [(s.name, "skill (local)") for s in bundled_skills()]
    items += [(s["id"], "skill") for s in ext_skills()]
    items += [(p["id"], "plugin") for p in load_plugins()]
    return items


def _copy_skill_dir(src: Path, dest_root: Path, note: str = "") -> None:
    dst = dest_root / src.name
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".git"))
    print(green(f"  skill  → {dst}") + (dim(f"  {note}") if note else ""))


def _install_ext_skills(dest_root: Path) -> None:
    """Shallow-clone each [[skill]] repo and copy its sub-paths — always latest."""
    skip = skipped_ids()
    for s in ext_skills():
        if s["id"] in skip:
            print(dim(f"  skill {s['id']}: skipped (config [skip])"))
            continue
        with tempfile.TemporaryDirectory(prefix="ai-dev-env-") as tmp:
            r = subprocess.run(f'git clone --depth 1 -q {s["repo"]} "{tmp}"', shell=True, capture_output=True)
            if r.returncode != 0:
                print(red(f"  skill {s['id']}: git clone failed ({s['repo']}) — skipped this run"))
                continue
            for sub in s.get("paths", [s["id"]]):
                src = Path(tmp) / sub
                if not (src / "SKILL.md").is_file():
                    print(red(f"  skill {s['id']}: {sub}/SKILL.md not found upstream — skipped"))
                    continue
                origin = "/".join(s["repo"].rstrip("/").split("/")[-2:])
                _copy_skill_dir(src, dest_root, f"(latest from {origin})")


def _install_skills(dest_root: Path) -> None:
    local, ext = bundled_skills(), ext_skills()
    if not local and not ext:
        print(dim("  skills: none configured"))
        return
    skip = skipped_ids()
    dest_root.mkdir(parents=True, exist_ok=True)
    for src in local:
        if src.name in skip:
            print(dim(f"  skill {src.name}: skipped (config [skip])"))
            continue
        _copy_skill_dir(src, dest_root)
    _install_ext_skills(dest_root)


CLAUDE_REF = (
    "# Agent guidelines\n\n"
    "Follow every guideline in `~/.claude/AGENTS.md` (shared cross-harness rules: "
    "think before coding, simplicity first, surgical changes, goal-driven execution)."
)


def repo_display() -> str:
    """This machine's clone path, ~-relative when under home (for docs/prose)."""
    try:
        return "~/" + REPO.relative_to(Path.home()).as_posix()
    except ValueError:
        return REPO.as_posix()


def env_repo_pointer() -> str:
    """Generated 'Environment repo' section — path-accurate for this machine."""
    r = repo_display()
    return (
        "## Environment repo\n\n"
        f"Tools, MCP servers, skills, plugins, and these guidelines are managed by "
        f"`{r}`. When the user asks what is installed, how to use a managed tool, "
        "or to install / fix / set up something:\n\n"
        f"- **Report:** `uv run --python 3.12 {r}/scripts/setup.py report`\n"
        "- **Install:** list what is missing plus each command, ask the user "
        '*"confirm each"* or *"install all"*, then `setup.py install --each|--all`.\n'
        "- **Wire a harness:** `setup.py wire <claude-code|codex|cursor|generic>` "
        "(`unwire` reverses it; `bootstrap` = install + wire in one go).\n"
        "- **Update everything:** `setup.py upgrade`.\n"
        f"- Per-entry docs: `{r}/docs/*.md`. Add things by editing "
        f"`{r}/manifest.toml` (4 sections: `[guidelines]` / `[[tool]]` / "
        "`[[skill]]` / `[[plugin]]`)."
    )


def _codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))


def _install_guidelines(harness: str) -> None:
    """Install the always-on behavioral guidelines into a harness's instruction file.

    AGENTS.md carries the full text; CLAUDE.md only references it.
    All edits are marker-delimited and idempotent.
    """
    body = guidelines_text().rstrip() + "\n\n" + env_repo_pointer()
    if harness == "claude-code":
        home = Path.home() / ".claude"
        a = upsert_block(home / "AGENTS.md", body)
        c = upsert_block(home / "CLAUDE.md", CLAUDE_REF)
        print(green(f"  guidelines → {home / 'AGENTS.md'} ({a}),  {home / 'CLAUDE.md'} ({c}, reference only)"))
    elif harness == "codex":
        p = _codex_home() / "AGENTS.md"
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
    skip = skipped_ids()
    for p in plugins:
        if p["id"] in skip:
            print(dim(f"  plugin {p['id']}: skipped (config [skip])"))
            continue
        cmd = p.get("install", {}).get(harness)
        if not cmd:
            print(dim(f"  plugin {p['id']}: no install path for {harness}"))
            continue
        if cmd.lstrip().startswith("#"):
            print(yellow(f"  plugin {p['id']}: {cmd.lstrip('# ').strip()}"))
            continue
        rc = run(cmd)
        msg = "installed" if rc == 0 else "FAILED — install manually"
        print((green if rc == 0 else red)(f"  plugin {p['id']} {msg}"))


_GRAPHIFY_PLATFORM = {"claude-code": "claude", "codex": "codex", "cursor": "cursor"}


def _install_graphify_skill(harness: str) -> None:
    """graphify ships its skill via its own installer, not as a [[skill]]/bundle."""
    plat = _GRAPHIFY_PLATFORM.get(harness)
    if not plat:
        return
    g = next((t for t in load_tools() if t["id"] == "graphify"), None)
    if not g or g["id"] in skipped_ids():
        return
    if shutil.which("graphify") is None:
        print(dim("  graphify: CLI not installed — skipping its skill (setup.py install graphify)"))
        return
    rc = run(f"graphify install --platform {plat}", capture_output=True)
    tail = "installed" if rc == 0 else "installer returned nonzero"
    print((green if rc == 0 else yellow)(f"  graphify skill ({plat}) {tail}"))


def wire_claude_code(tools) -> int:
    if shutil.which("claude") is None:
        print(red("  `claude` CLI not found — is Claude Code installed?"))
        return 1
    _install_skills(Path.home() / ".claude" / "skills")
    for t in _mcp_tools(tools):
        command, arglist = mcp_spec(t)
        command = shutil.which(command) or command  # absolute path — don't rely on the harness's PATH
        args = " ".join(arglist)
        # -e/--env is variadic, so it must come *after* the server name.
        env, env_masked = _mcp_env(t, "-e")
        subprocess.run(f"claude mcp remove {t['id']} -s user", shell=True, capture_output=True)
        base = f"claude mcp add --scope user {t['id']} {{}} -- {command} {args}"
        run(" ".join(base.format(env).split()), display=" ".join(base.format(env_masked).split()))
        _warn_missing_env(t)
    _install_graphify_skill("claude-code")
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
        base = f"codex mcp add {{}} {t['id']} -- {cmd} {args}"
        if run(" ".join(base.format(env).split()), display=" ".join(base.format(env_masked).split())) != 0:
            print(yellow(f"  `codex mcp add` failed for {t['id']} — add manually to {codex_home}/config.toml"))
        _warn_missing_env(t)
    _install_graphify_skill("codex")
    return 0


def _print_bundled_skills() -> None:
    skills = bundled_skills()
    if skills:
        print(dim("  local skills (wire manually — no native skills dir):"))
        for s in skills:
            print(dim(f"    {s / 'SKILL.md'}"))
    for s in ext_skills():
        print(dim(f"  external skill '{s['id']}': clone {s['repo']} and copy {', '.join(s.get('paths', [s['id']]))}"))


def wire_cursor(tools) -> int:
    _print_mcp_json(tools, Path.home() / ".cursor" / "mcp.json")
    _print_bundled_skills()
    _install_graphify_skill("cursor")
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

    skip = skipped_ids()
    print(f"\n  {bold('[skip]')}  {', '.join(sorted(skip)) if skip else dim('(nothing skipped)')}")
    print(dim("  change: setup.py choose"))
    if need:
        print(dim("\n  fill in the file, then: setup.py wire <harness>"))
    return 0


def _choose_interactive() -> None:
    """Toggle which managed items are skipped; writes config [skip].ids."""
    items = managed_items()
    skip = skipped_ids()
    while True:
        print()
        for i, (id_, kind) in enumerate(items, 1):
            mark = red("skip") if id_ in skip else green(" on ")
            print(f"  {i:>2}  [{mark}]  {bold(id_):<24} {dim(kind)}")
        raw = input("\ntoggle (numbers/ids, space-separated; blank = done) > ").strip()
        if not raw:
            break
        valid = {i[0] for i in items}
        for tok in raw.replace(",", " ").split():
            id_ = items[int(tok) - 1][0] if tok.isdigit() and 1 <= int(tok) <= len(items) else tok
            if id_ not in valid:
                print(red(f"  ? unknown: {tok}"))
            elif id_ in skip:
                skip.discard(id_)
            else:
                skip.add(id_)
    set_skip(sorted(skip))
    print(green(f"\nsaved → {CONFIG}"))
    print(dim(f"skipping: {', '.join(sorted(skip)) or '(nothing)'}"))


def _first_run_gate() -> None:
    """On the very first config creation, offer to pick what to skip."""
    if write_config_template() != "created":
        return
    print(dim(f"created {CONFIG}"))
    if not sys.stdin.isatty():
        return
    n = len(managed_items())
    print(bold(f"\nFirst run — {n} managed items (tools, MCP servers, skills, plugins)."))
    if input("Set up [A]ll, or [c]hoose what to skip?  ").strip().lower() in ("c", "choose"):
        _choose_interactive()


def cmd_choose(_args) -> int:
    write_config_template()
    _choose_interactive()
    return 0


def cmd_wire(args) -> int:
    fn = WIRERS.get(args.harness)
    if not fn:
        print(red(f"unknown harness '{args.harness}'. choices: {', '.join(WIRERS)}"))
        return 2
    _first_run_gate()
    print(bold(f"\nwiring ai-dev-env into {args.harness}\n"))
    rc = fn(load_tools())
    _install_guidelines(args.harness)
    _install_plugins(args.harness)
    return rc


# ── bootstrap ──────────────────────────────────────────────────────────────
def _detected_harnesses() -> list[str]:
    """Harnesses whose CLI is on PATH that `wire` fully automates, in wire order."""
    return [h for h, exe in (("claude-code", "claude"), ("codex", "codex")) if shutil.which(exe)]


def cmd_bootstrap(args) -> int:
    """Fresh machine, one shot: install every tool, then wire every harness found."""
    print(bold("\nai-dev-env bootstrap\n"))
    _first_run_gate()

    rc = cmd_install(argparse.Namespace(tools=[], mode=args.mode))
    if rc != 0 and not args.keep_going:
        print(red("\ninstall reported errors — fix them, or re-run with --keep-going. Not wiring."))
        return rc

    harnesses = _detected_harnesses()
    if not harnesses:
        print(yellow("\nno harness CLI on PATH (claude / codex) — install one, then: setup.py wire <harness>"))
    for h in harnesses:
        cmd_wire(argparse.Namespace(harness=h))

    need = [k for k in all_required_env() if k not in config_env()]
    if need:
        print(yellow(f"\nsecrets still needed in {CONFIG}: {', '.join(need)}"))
        print(dim("  fill them in, then re-run: setup.py wire <harness>"))
    print(green("\nbootstrap done.") if rc == 0 else yellow("\nbootstrap done (with install errors above)."))
    return rc if args.keep_going else 0


# ── upgrade ────────────────────────────────────────────────────────────────
def upgrade_cmd(t: dict) -> str | None:
    """How to upgrade a tool: explicit [tool.upgrade], else inferred from install."""
    up = t.get("upgrade", {})
    if up.get(OS) or up.get("default"):
        return up.get(OS) or up.get("default")
    if t["id"] == "uv":
        return "uv self update"
    ins = install_cmd(t) or ""
    if "uv tool install" in ins:
        return f"uv tool upgrade {t.get('pypi') or t['id']}"
    if "npm install -g" in ins:
        return ins  # re-running `npm install -g <pkg>` pulls the latest
    if "| sh" in ins or "| iex" in ins:
        return ins  # these one-line installers double as upgraders
    return None


def cmd_upgrade(args) -> int:
    tools = load_tools()
    wanted = set(args.tools) if args.tools else {t["id"] for t in tools} - skipped_ids()
    targets = [t for t in tools if t["id"] in wanted and is_installed(t)]
    print(bold("\nupgrading installed tools\n"))
    rc = 0
    for t in targets:
        cmd = upgrade_cmd(t)
        if not cmd:
            print(dim(f"  {t['name']}: no known upgrade path — skip"))
            continue
        before = version_of(t)
        if run(cmd) != 0:
            print(red(f"  {t['name']}: upgrade failed"))
            rc = 1
            continue
        after = version_of(t)
        delta = "unchanged" if before == after else f"{before or '?'} -> {after or '?'}"
        print(green(f"  {t['name']}: {delta}"))
    if not args.tools and (ext_skills() or bundled_skills()):
        print(bold("\nrefreshing skills ([[skill]] re-cloned = their upgrade)\n"))
        for h, d in (("claude", Path.home() / ".claude" / "skills"), ("codex", _codex_home() / "skills")):
            if shutil.which(h if h == "codex" else "claude"):
                print(dim(h))
                _install_skills(d)
    print(dim("\nplugins auto-update through their harness (e.g. `claude plugin update`)."))
    return rc


# ── unwire ─────────────────────────────────────────────────────────────────
def _strip_block(path: Path) -> bool:
    """Remove the marker-delimited guidelines block from a file. Returns whether it was there."""
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    if GUIDE_BEGIN not in text or GUIDE_END not in text:
        return False
    pre = text[: text.index(GUIDE_BEGIN)]
    post = text[text.index(GUIDE_END) + len(GUIDE_END) :]
    body = (pre.rstrip() + "\n\n" + post.lstrip()).strip()
    path.write_text(body + "\n" if body else "", encoding="utf-8")
    return True


def cmd_unwire(args) -> int:
    h = args.harness
    if h not in WIRERS:
        print(red(f"unknown harness '{h}'. choices: {', '.join(WIRERS)}"))
        return 2
    print(bold(f"\nremoving ai-dev-env wiring from {h}\n"))
    mcp_ids = [t["id"] for t in load_tools() if t.get("mcp")]

    if h in ("claude-code", "codex"):
        remove = "claude mcp remove {} -s user" if h == "claude-code" else "codex mcp remove {}"
        for i in mcp_ids:
            subprocess.run(remove.format(i), shell=True, capture_output=True)
            print(dim(f"  mcp removed: {i}"))
        skills_dir = (Path.home() / ".claude" if h == "claude-code" else _codex_home()) / "skills"
        names = [s.name for s in bundled_skills()]
        names += [Path(sub).name for s in ext_skills() for sub in s.get("paths", [s["id"]])]
        for n in names:
            if (skills_dir / n).exists():
                shutil.rmtree(skills_dir / n, ignore_errors=True)
                print(dim(f"  skill removed: {n}"))
        agents = (Path.home() / ".claude" if h == "claude-code" else _codex_home()) / "AGENTS.md"
        print(dim(f"  guidelines block: AGENTS.md removed={_strip_block(agents)}"))
        if h == "claude-code":
            print(dim(f"  guidelines block: CLAUDE.md removed={_strip_block(Path.home() / '.claude' / 'CLAUDE.md')}"))
    else:
        print(dim(f"  {h}: manual — remove the MCP entries, skill dirs, and guidelines block yourself"))

    print(dim("\n  kept: installed CLIs, ~/.ai-dev-env/config.toml, plugins, statusline."))
    print(dim("  uninstall a CLI:   uv tool uninstall <id>   /   npm uninstall -g <pkg>"))
    print(dim("  statusline off:    setup.py statusline --off"))
    return 0


def cmd_guidelines(args) -> int:
    # default matches `skills` / `plugins`: the two harnesses `wire` fully
    # automates. `cursor` is opt-in — pass it explicitly.
    targets = [args.harness] if args.harness else ["claude-code", "codex"]
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


# ── statusline ─────────────────────────────────────────────────────────────
STATUSLINE_DIR = Path.home() / ".claude" / "ai-dev-env-statusline"
_CLAUDE_SETTINGS = Path.home() / ".claude" / "settings.json"


def _load_claude_settings() -> dict:
    if not _CLAUDE_SETTINGS.exists():
        return {}
    import json

    try:
        return json.loads(_CLAUDE_SETTINGS.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_claude_settings(d: dict) -> None:
    import json

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


# ── doctor ─────────────────────────────────────────────────────────────────
def cmd_doctor(_args) -> int:
    rc = 0
    skip = skipped_ids()
    for t in load_tools():
        if t["id"] in skip:
            print(f"{dim('SKIP')}  {t['name']:<24} {dim('config [skip]')}")
            continue
        ok = is_installed(t)
        if ok:
            print(f"{green('PASS')}  {t['name']:<24} {dim(t.get('verify', ''))}")
        elif not install_cmd(t):
            # a prerequisite with no managed install (e.g. node) — advisory, not a failure
            print(f"{yellow('WARN')}  {t['name']:<24} {dim('not installed — install it yourself, see docs/')}")
        else:
            print(f"{red('FAIL')}  {t['name']:<24} {dim(t.get('verify', ''))}")
            rc |= 1
        for k in missing_env(t):
            print(f"{yellow('WARN')}  {t['name']:<24} {k} missing — fill in {CONFIG}")
            if t.get("setup"):
                print(f"      {dim(t['setup'])}")
    return rc


# ── main ───────────────────────────────────────────────────────────────────
def main() -> int:
    p = argparse.ArgumentParser(
        prog="setup.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("report", help="show managed tools (default)").set_defaults(fn=cmd_report)

    pi = sub.add_parser("install", help="install missing tools")
    pi.add_argument("tools", nargs="*", help="tool ids (default: all)")
    g = pi.add_mutually_exclusive_group()
    g.add_argument("--all", dest="mode", action="store_const", const="all", help="install everything, no prompt")
    g.add_argument("--each", dest="mode", action="store_const", const="each", help="confirm each tool")
    pi.set_defaults(fn=cmd_install, mode=None)

    pb = sub.add_parser("bootstrap", help="fresh machine: install all tools + wire every harness found")
    gb = pb.add_mutually_exclusive_group()
    gb.add_argument("--all", dest="mode", action="store_const", const="all", help="no prompts")
    gb.add_argument("--each", dest="mode", action="store_const", const="each", help="confirm each tool")
    pb.add_argument("--keep-going", action="store_true", help="wire even if some installs failed")
    pb.set_defaults(fn=cmd_bootstrap, mode=None)

    pup = sub.add_parser("upgrade", help="upgrade installed tools + re-pull [[skill]] latest")
    pup.add_argument("tools", nargs="*", help="tool ids (default: all installed)")
    pup.set_defaults(fn=cmd_upgrade)

    sub.add_parser("config", help="create/show ~/.ai-dev-env/config.toml").set_defaults(fn=cmd_config)

    sub.add_parser("choose", help="pick which tools/skills/plugins to skip").set_defaults(fn=cmd_choose)

    psl = sub.add_parser("statusline", help="add a context-usage segment to the Claude Code statusLine")
    psl.add_argument("--off", action="store_true", help="remove it, restoring the previous statusLine")
    psl.set_defaults(fn=cmd_statusline)

    pw = sub.add_parser("wire", help="install bundled skills + MCP + guidelines into a harness")
    pw.add_argument("harness", choices=list(WIRERS))
    pw.set_defaults(fn=cmd_wire)

    pun = sub.add_parser("unwire", help="remove ai-dev-env wiring (MCP + skills + guidelines) from a harness")
    pun.add_argument("harness", choices=list(WIRERS))
    pun.set_defaults(fn=cmd_unwire)

    pg = sub.add_parser("guidelines", help="install always-on agent guidelines (AGENTS.md + CLAUDE.md ref)")
    pg.add_argument("harness", nargs="?", choices=list(WIRERS), help="default: claude-code + codex")
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
