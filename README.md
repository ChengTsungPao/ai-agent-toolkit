# ai-dev-env

My portable AI dev-environment. One repo that knows every tool I deliberately
installed, what it's for, how to use it, and how to wire it into whatever
AI harness I'm running — on Windows, macOS, or Linux.

Future machine setup = clone this + run one script.

## Quick start

```bash
# macOS / Linux
git clone https://github.com/ChengTsungPao/ai-dev-env ~/ai-dev-env
~/ai-dev-env/scripts/install.sh                 # report: what's installed, what each does
~/ai-dev-env/scripts/install.sh install         # install missing (asks: all vs confirm-each)
~/ai-dev-env/scripts/install.sh wire claude-code
~/ai-dev-env/scripts/install.sh wire codex
```

```powershell
# Windows
git clone https://github.com/ChengTsungPao/ai-dev-env $HOME\ai-dev-env
& $HOME\ai-dev-env\scripts\install.ps1
& $HOME\ai-dev-env\scripts\install.ps1 install
& $HOME\ai-dev-env\scripts\install.ps1 wire codex
```

The only prerequisite is [uv](https://docs.astral.sh/uv/); the bootstrap script
installs it if missing, then runs everything on a pinned Python.

## What's in the box

| tool | purpose |
|---|---|
| **uv** | Python toolchain; installs every other CLI as an isolated `uv tool` |
| **Basic Memory** | private, local, **human-editable** Markdown memory shared across all harnesses (MCP) |
| **graphify** | codebase → queryable knowledge graph (tree-sitter AST + Leiden), `/graphify` skill |

Full detail per tool: [`docs/tools/`](docs/tools/). Source of truth:
[`manifest.toml`](manifest.toml).

## Commands

```
setup.py report              # default — installed?, purpose, usage, what's missing
setup.py install [ids] [--all|--each]
setup.py wire <claude-code|codex|cursor|gemini-cli|generic>
setup.py doctor              # verify each tool
```

Run via `scripts/install.sh` / `scripts/install.ps1` (they guarantee uv + the
right Python), or directly with `uv run --python 3.12 scripts/setup.py ...`.

## Harnesses

`wire` automates Claude Code and Codex (skill copy + MCP registration).
Cursor / Gemini CLI / other MCP clients get a printed JSON block to paste —
see [`harnesses/`](harnesses/).

## The `ai-dev-env` skill

[`skills/ai-dev-env/SKILL.md`](skills/ai-dev-env/SKILL.md) is installed into each
harness by `wire`. Invoking it (`/ai-dev-env` in Claude Code) makes the agent
report the current toolset — name, purpose, how to use — and, on request,
install or wire what's missing.

## Adding a tool

Append a `[[tool]]` block to `manifest.toml` (schema at the top of that file),
commit, push. `report` / `install` / `doctor` pick it up with no code change;
add `[tool.mcp]` if it's an MCP server so `wire` registers it too.

## Layout

```
manifest.toml            source of truth
scripts/
  setup.py               orchestrator (stdlib only, py3.11+)
  install.sh / .ps1      bootstrap (ensure uv, run setup.py)
skills/ai-dev-env/       the portable skill
harnesses/               per-harness wiring notes
docs/tools/              per-tool docs
```
