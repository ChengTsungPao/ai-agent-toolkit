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
| **graphify** | codebase → queryable knowledge graph (tree-sitter AST + Leiden), `/graphify` |

Full detail per tool: [`docs/tools/`](docs/tools/). Source of truth:
[`manifest.toml`](manifest.toml).

## Agent guidelines

[`guidelines/AGENTS.md`](guidelines/AGENTS.md) — always-on behavioral rules
(think before coding · simplicity first · surgical changes · goal-driven
execution), after [Karpathy's notes](https://github.com/multica-ai/andrej-karpathy-skills)
on LLM coding pitfalls. `AGENTS.md` is canonical (the cross-harness standard);
`CLAUDE.md` / `GEMINI.md` just reference it, so there's one source of truth.

`wire` installs them into a harness; `setup.py guidelines` (re)applies them
everywhere.

## Skills & plugins

**Bundled skills** — `skills/<name>/SKILL.md` bundles (see
[`skills/README.md`](skills/README.md)); `wire` copies them into every harness's
skills dir (`~/.claude/skills/`, `$CODEX_HOME/skills/`). Currently:

| skill | what |
|---|---|
| `grill-me` (+ `grilling`) | relentless interview to sharpen a plan before coding — `/grill-me` |

**External plugins** — large, self-updating ecosystems recorded under
`[[plugin]]` in `manifest.toml` and installed per-harness (not vendored):

| plugin | what |
|---|---|
| `superpowers` | obra's agentic dev methodology: 20+ auto-activating skills (TDD, debugging, brainstorming, worktrees) |

`setup.py skills` / `setup.py plugins` re-apply each group.

There is deliberately **no `ai-dev-env` skill** — the agent already learns about
this repo from the "Environment repo" section that `guidelines` writes into
`AGENTS.md`, and `setup.py report` is the live status command.

## Commands

```
setup.py report              # default — installed?, purpose, usage, what's missing
setup.py install [ids] [--all|--each]
setup.py wire <claude-code|codex|cursor|gemini-cli|generic>   # skills + MCP + guidelines + plugins
setup.py skills [harness]                                     # just the bundled skills
setup.py plugins [harness]                                    # just the external plugins
setup.py guidelines [harness]                                 # just the guidelines
setup.py doctor              # verify each tool
```

Run via `scripts/install.sh` / `scripts/install.ps1` (they guarantee uv + the
right Python), or directly with `uv run --python 3.12 scripts/setup.py ...`.

## Harnesses

`wire` automates Claude Code and Codex (skill copy + MCP registration +
guidelines). Cursor / Gemini CLI / other MCP clients get a printed JSON block to
paste — see [`harnesses/`](harnesses/).

## Adding a tool

Append a `[[tool]]` block to `manifest.toml` (schema at the top of that file),
commit, push. `report` / `install` / `doctor` pick it up with no code change;
add `[tool.mcp]` if it's an MCP server so `wire` registers it too.

## Layout

```
manifest.toml            source of truth (tools + guidelines + plugins)
scripts/
  setup.py               orchestrator (stdlib only, py3.11+)
  install.sh / .ps1      bootstrap (ensure uv, run setup.py)
guidelines/
  AGENTS.md              canonical always-on agent rules + env-repo pointer
  CLAUDE.md              project-level reference stub
skills/                  vendored skill bundles installed into every harness
harnesses/               per-harness wiring notes
docs/tools/              per-tool / per-skill / per-plugin docs
```
