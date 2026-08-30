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
| **Notion MCP** | official `@notionhq/notion-mcp-server` (npm global), runs locally — read/create/update Notion pages & DBs (token in `config.toml`) |

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

**Skills** land in every harness's skills dir (`~/.claude/skills/`,
`$CODEX_HOME/skills/`) via `wire` / `setup.py skills`. Two kinds
(see [`skills/README.md`](skills/README.md)):

| skill | kind | what |
|---|---|---|
| your own | local folder in `skills/` | committed, frozen, edit freely |
| `grill-me` (+ `grilling`) | `[[skill]]` in `manifest.toml` | cloned fresh from [mattpocock/skills](https://github.com/mattpocock/skills) at install — **latest each run** — `/grill-me` |

**External plugins** — large, self-updating ecosystems recorded under
`[[plugin]]` in `manifest.toml` and installed per-harness (not vendored):

| plugin | what |
|---|---|
| `superpowers` | obra's agentic dev methodology: 20+ auto-activating skills (TDD, debugging, brainstorming, worktrees) |

`setup.py skills` / `setup.py plugins` re-apply each group.

There is deliberately **no `ai-dev-env` skill** — the agent already learns about
this repo from the "Environment repo" section that `guidelines` writes into
`AGENTS.md`, and `setup.py report` is the live status command.

## Local config (secrets)

Tokens that MCP servers need (e.g. `NOTION_TOKEN`) go in
**`~/.ai-dev-env/config.toml`** — a file you own, outside the repo clone, never
committed. `setup.py config` creates it with every needed key blank; fill them
in and re-run `wire`. Values are passed to each MCP server at wire time; an
exported env var of the same name is the fallback.

## Commands

```
setup.py report              # default — installed?, purpose, usage, what's missing
setup.py install [ids] [--all|--each]
setup.py config              # create/show ~/.ai-dev-env/config.toml
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

## Adding something

`manifest.toml` has four sections — pick by what the thing is (decision table at
the top of that file):

| you have | add | installed by |
|---|---|---|
| a CLI to install | `[[tool]]` | `install` |
| an MCP server | `[[tool]]` + `[tool.mcp]` | `install` + `wire` |
| a third-party skill (want latest at install) | `[[skill]]` (git repo + sub-paths) | `skills` / `wire` |
| your own skill | a folder under `skills/` | `skills` / `wire` |
| a plugin ecosystem | `[[plugin]]` (per-harness install cmds) | `plugins` / `wire` |
| an always-on rule | edit `guidelines/AGENTS.md` | `guidelines` / `wire` |

Commit, push. No `setup.py` change needed for any of these.

## Layout

```
AGENTS.md / CLAUDE.md    how to work on THIS repo (read first)
manifest.toml            source of truth — [guidelines] / [[tool]] / [[skill]] / [[plugin]]
scripts/
  setup.py               orchestrator (stdlib only, py3.11+)
  install.sh / .ps1      bootstrap (ensure uv, run setup.py)
guidelines/
  AGENTS.md              behavioural rules distributed to each harness (env-repo
                         pointer is appended at install with the real clone path)
  CLAUDE.md              project-root reference stub (template for other repos)
skills/                  your own skill folders (committed); third-party ones are [[skill]] in manifest.toml
harnesses/               per-harness wiring notes
docs/tools/              per-tool / per-skill / per-plugin docs
```

Root `AGENTS.md` / `CLAUDE.md` document working **on** this repo; the ones in
`guidelines/` are content **distributed to** each machine — different jobs.
