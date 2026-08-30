# ai-dev-env

My portable AI dev environment. One repo that knows every tool I deliberately
installed, what it's for, and how to wire it — plus skills, plugins, and
always-on guidelines — into whatever AI harness I run (Claude Code, Codex,
Cursor, Gemini CLI), on Windows / macOS / Linux.

Fresh machine = clone + one script.

## Quick start

```bash
# macOS / Linux
git clone https://github.com/ChengTsungPao/ai-dev-env ~/ai-dev-env
~/ai-dev-env/scripts/install.sh                 # report: what's installed + how to use it
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

Only prerequisite is [uv](https://docs.astral.sh/uv/) — the bootstrap installs
it, then runs everything on a pinned Python.

## What's in the box

| | | |
|---|---|---|
| **uv** | tool | Python toolchain; every other CLI is an isolated `uv tool` |
| **Basic Memory** | MCP | private, local, **human-editable** Markdown memory shared across harnesses |
| **Notion MCP** | MCP | official `@notionhq/notion-mcp-server`, runs locally — read/write Notion pages & DBs |
| **graphify** | tool | codebase → queryable knowledge graph (tree-sitter + Leiden), `/graphify` |
| **grill-me** | skill | relentless interview to sharpen a plan before coding, `/grill-me` |
| **superpowers** | plugin | obra's agentic dev methodology — 20+ auto-activating skills |
| Karpathy rules | guidelines | think before coding · simplicity first · surgical changes · goal-driven |

Per-item detail: [`docs/`](docs/). Source of truth:
[`manifest.toml`](manifest.toml).

## Local config (secrets)

Tokens an MCP server needs (e.g. `NOTION_TOKEN`) go in
**`~/.ai-dev-env/config.toml`** — a file you own, outside the clone, never
committed. `setup.py config` creates it with every key blank; fill in and re-run
`wire`.

## Commands

```
setup.py report              # grouped status: MCP servers / CLI tools / Skills / Plugins / Guidelines
setup.py install [ids] [--all|--each]
setup.py config              # create/show ~/.ai-dev-env/config.toml
setup.py wire <claude-code|codex|cursor|gemini-cli|generic>   # MCP + skills + guidelines + plugins
setup.py skills | plugins | guidelines [harness]              # one group only
setup.py doctor
```

Run via `scripts/install.sh` / `.ps1`, or `uv run --python 3.12 scripts/setup.py …`.

## Working on this repo · adding tools/skills/plugins

See **[AGENTS.md](AGENTS.md)** — the model, the path rules, how to add each of
the four kinds, how to test. (`CLAUDE.md` points there too.)

`guidelines/AGENTS.md` is a different file: the behavioural rules this repo
*distributes* to each machine, not instructions for working here.
