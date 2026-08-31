# ai-dev-env

My portable AI dev environment. One repo that knows every tool I deliberately
installed, what it's for, and how to wire it — plus skills, plugins, and
always-on guidelines — into whatever AI harness I run (Claude Code, Codex,
Cursor), on Windows / macOS / Linux.

Fresh machine = clone + one script.

## Quick start

```bash
# macOS / Linux
git clone https://github.com/ChengTsungPao/ai-dev-env ~/ai-dev-env
~/ai-dev-env/scripts/install.sh              # report: what's installed + how to use it
~/ai-dev-env/scripts/install.sh bootstrap    # install missing + wire every harness found
```

```powershell
# Windows
git clone https://github.com/ChengTsungPao/ai-dev-env $HOME\ai-dev-env
& $HOME\ai-dev-env\scripts\install.ps1
& $HOME\ai-dev-env\scripts\install.ps1 bootstrap
```

`bootstrap` asks *all vs confirm-each*, installs, then wires Claude Code / Codex
if their CLI is present. Or drive the steps yourself: `install` → `wire
<harness>`. Fill any secrets into `~/.ai-dev-env/config.toml` and re-run `wire`.

Only prerequisite is [uv](https://docs.astral.sh/uv/) — the bootstrap installs
it, then runs everything on a pinned Python.

## What's in the box

| | | |
|---|---|---|
| **uv** | tool | Python toolchain; every other CLI is an isolated `uv tool` |
| **Node.js** | prereq | not auto-installed — needed only by the two npm-based MCP servers below ([`docs/node.md`](docs/node.md)) |
| **Basic Memory** | MCP | private, local, **human-editable** Markdown memory shared across harnesses |
| **Notion MCP** | MCP | official `@notionhq/notion-mcp-server`, runs locally — read/write Notion pages & DBs |
| **Chrome DevTools MCP** | MCP | drive a local Chrome — navigate, screenshot, console, Lighthouse, perf traces |
| **graphify** | tool | codebase → queryable knowledge graph (tree-sitter + Leiden), `/graphify` |
| **CodeGraph** | MCP | live auto-syncing code graph — "who calls X / impact of changing Y" in one call (overlaps graphify; being compared) |
| **grill-me** | skill | relentless interview to sharpen a plan before coding, `/grill-me` |
| **superpowers** | plugin | obra's agentic dev methodology — 20+ auto-activating skills |
| Karpathy rules | guidelines | think before coding · simplicity first · surgical changes · goal-driven |

Per-item detail: [`docs/`](docs/). Source of truth:
[`manifest.toml`](manifest.toml).

## Local config

**`~/.ai-dev-env/config.toml`** — a file you own, outside the clone, never
committed. Holds two things:

- `[env]` — secrets each MCP server needs (e.g. `NOTION_TOKEN`)
- `[skip]` — ids of tools/skills/plugins to leave out of `install` / `wire`

The first `install` / `wire` on a fresh machine creates it and asks *"set up
everything, or choose what to skip?"*. Change the picks any time with
`setup.py choose` (or edit `[skip].ids`).

## Commands

```
setup.py report              # grouped status: MCP servers / CLI tools / Skills / Plugins / Guidelines
setup.py bootstrap [--all|--each]   # install everything + wire every harness found
setup.py install [ids] [--all|--each]
setup.py upgrade [ids]       # uv tool upgrade / npm / installer + re-pull [[skill]] latest
setup.py config              # create/show ~/.ai-dev-env/config.toml
setup.py choose              # pick which items to skip
setup.py statusline [--off]  # add a 'ctx NN%' segment to the Claude Code statusLine (contrib/statusline/)
setup.py wire   <claude-code|codex|cursor|generic>   # MCP + skills + guidelines + plugins
setup.py unwire <claude-code|codex|cursor|generic>   # reverse of wire (keeps CLIs + config)
setup.py skills | plugins | guidelines [harness]              # one group only
setup.py doctor
```

Run via `scripts/install.sh` / `.ps1`, or `uv run --python 3.12 scripts/setup.py …`.

## How the repo is laid out

`manifest.toml` **declares** what the environment should have.
`scripts/setup.py` **reads it and does the work**. Everything else is content
`setup.py` distributes to your machines, or notes.

| path | what it's for |
|---|---|
| **`manifest.toml`** | the declaration — 4 sections (`[guidelines]` / `[[tool]]` / `[[skill]]` / `[[plugin]]`), decision table at the top |
| **`scripts/`** | the engine (`setup.py`) and the fresh-machine bootstrap (`install.sh` / `install.ps1`) |
| **`guidelines/`** | the always-on behavioural rules injected into every harness — content distributed *to* machines, not docs about this repo |
| **`skills/`** | your **own** skill bundles (committed). Third-party skills live in `manifest.toml` as `[[skill]]`, not here |
| **`harnesses/`** | per-harness reference — what `wire` does for Claude Code / Codex / Cursor, and the manual steps |
| **`contrib/`** | optional harness tweaks that aren't a tool/skill/plugin/MCP — each is a helper script + a `setup.py` subcommand (currently `statusline/`) |
| **`docs/`** | one optional page per manifest entry: *why* it was chosen + fiddly setup |
| **`AGENTS.md`** / **`CLAUDE.md`** | how to work **on this repo** |

Secrets live in `~/.ai-dev-env/config.toml` — **outside the repo**, created by
`setup.py config`.

## Working on this repo · adding tools/skills/plugins

See **[AGENTS.md](AGENTS.md)** — the model, the path rules, how to add each of
the four kinds, how to test. (`CLAUDE.md` points there too.)

`guidelines/AGENTS.md` is a different file: the behavioural rules this repo
*distributes* to each machine, not instructions for working here.
