# Working on ai-dev-env

This repo provisions a personal AI dev environment: it installs a fixed set of
tools and wires them — plus skills, plugins, and always-on guidelines — into
whatever AI harness you run (Claude Code, Codex, Cursor, Gemini CLI), on
Windows / macOS / Linux.

Also follow the behavioural rules in [`guidelines/AGENTS.md`](guidelines/AGENTS.md).

## Setup on a fresh machine

```sh
git clone <this-repo> ~/ai-dev-env      # ~/ai-dev-env is canonical; any path works
~/ai-dev-env/scripts/install.sh          # macOS/Linux   (install.ps1 on Windows)
~/ai-dev-env/scripts/install.sh install  # install missing tools (asks: all vs each)
~/ai-dev-env/scripts/install.sh wire claude-code
~/ai-dev-env/scripts/install.sh wire codex
```

Only prerequisite is [uv](https://docs.astral.sh/uv/) — the bootstrap installs
it if missing. `setup.py` always runs via `uv run --python 3.12`, so `tomllib`
and a modern Python are guaranteed.

## The model

`manifest.toml` is the single source of truth. Four sections, decision table at
the top of that file:

| section | what it is | `setup.py` subcommand |
|---|---|---|
| `[guidelines]` | always-on behavioural rules, marker-injected into each harness's `AGENTS.md` (+ a one-line ref in `CLAUDE.md` / `GEMINI.md`) | `guidelines`, `wire` |
| `[[tool]]` | a CLI installed by a package manager. A `[tool.mcp]` sub-block ⇒ it is also wired as an MCP server | `install`, `doctor`, `wire` |
| `[[skill]]` | a third-party skill — git repo + sub-paths, shallow-cloned **fresh at install** (latest, not auto-updated after) | `skills`, `wire` |
| `[[plugin]]` | a plugin ecosystem installed through the harness's own plugin mechanism (which also updates it) | `plugins`, `wire` |

Your **own** skills go as committed folders under `skills/<name>/` (with a
`SKILL.md`); `wire` / `skills` copies them into `~/.claude/skills/` and
`$CODEX_HOME/skills/`. Cursor / Gemini have no skills dir — their paths are
printed for manual wiring.

`setup.py` commands: `report` (default, grouped status) · `install` · `config` ·
`wire <harness>` · `skills` · `plugins` · `guidelines` · `doctor`. `wire`
automates Claude Code and Codex fully; for Cursor / Gemini / generic it prints
the MCP JSON and skill paths to apply by hand.

There is deliberately **no `ai-dev-env` skill** — an agent learns about the repo
from the generated "Environment repo" section in the installed `AGENTS.md`, and
`setup.py report` is the live status command. Do not add one.

## Layout

Data flow: **`manifest.toml` declares → `scripts/setup.py` acts →** the rest is
content it distributes or notes.

| path | role | you edit it to… |
|---|---|---|
| `manifest.toml` | the declaration (4 sections + decision table) | add/change/remove any tool, skill, plugin, or the guidelines pointer |
| `scripts/setup.py` | the engine (report/install/config/wire/skills/plugins/guidelines/doctor). stdlib-only, py3.11+, run via `uv run --python 3.12` | only when adding a *new kind* of thing or a new subcommand — never for a new entry |
| `scripts/install.sh`, `install.ps1` | fresh-machine bootstrap: ensure `uv`, then call setup.py | rarely — they're ~20 lines each |
| `guidelines/AGENTS.md` | the behavioural rules **distributed to** every machine (injected into each harness's AGENTS.md). NOT this file. | change the always-on rules |
| `guidelines/CLAUDE.md` | copy-me `CLAUDE.md` stub for *other* repos' roots | almost never |
| `skills/<name>/` | the user's **own** skill bundles, committed, copied verbatim to each harness (`skills/README.md` = format) | add one of the user's own skills |
| `harnesses/<name>.md` | per-harness reference: what `wire <name>` does + manual steps | when a harness's wiring changes |
| `docs/<id>.md` | optional per-entry page — rationale + fiddly setup, not tutorials | when an entry has a real decision or a painful setup worth recording |
| `AGENTS.md`, `CLAUDE.md` (root) | how to work on this repo (this file) | when the repo's own structure/rules change |
| `~/.ai-dev-env/config.toml` | **outside the repo** — the machine's secrets, `setup.py config` creates it | never — it lives in `$HOME`, not the clone, so it can't be committed |

## Making changes

- Adding/changing a tool, skill, plugin, or guideline touches `manifest.toml`
  (or `guidelines/AGENTS.md`) **only** — `report` / `install` / `wire` pick it
  up with no `setup.py` change.
- **Test** → `uv run --python 3.12 scripts/setup.py report` then `… doctor`.
  `… wire claude-code` is idempotent, safe to re-run.
- A `docs/<id>.md` page is optional — write one only when the entry has a real
  decision or a painful setup worth recording; skip it if `usage.short` covers
  it. Link it from the entry's `docs = …`.
- Keep `setup.py` stdlib-only and Python 3.11+ compatible.

## Paths — read this before touching anything path-related

- **Never hard-code the clone location.** Scripts derive the repo root from their
  own location: `Path(__file__).resolve().parent.parent` (setup.py),
  `$PSScriptRoot` (ps1), `${BASH_SOURCE[0]}` (sh). All `manifest.toml` paths
  (`docs`, `guidelines.canonical`, `[[skill]].paths`) are **relative to the repo
  root** and resolved against it.
- `~/ai-dev-env` is the *recommended* path and what the docs show — but the repo
  must keep working cloned anywhere.
- The installed guidelines' "Environment repo" section is **generated** by
  `setup.py` with this machine's real clone path (`repo_display()`), not a
  hard-coded `~/ai-dev-env`. Do not write that section into
  `guidelines/AGENTS.md` by hand.
- **Local state and secrets** live in `~/.ai-dev-env/config.toml` — *outside* the
  clone, never committed. Override the directory with `$AI_DEV_ENV_HOME`.
  (`~/.ai-dev-env/` the state dir is a different thing from `~/ai-dev-env/` the
  clone — note the dot.)
- In code use `pathlib` / `Path`, never string-concatenate paths. In docs use
  forward slashes. `.gitattributes` forces LF everywhere except `*.ps1` (CRLF).
- Per-OS differences live in exactly three places: `[tool.install]` keys
  (`macos`/`linux`/`windows`/`default`), `[tool.mcp.<os>]` command overrides, and
  `_persist_env()`. Add OS branches only there.
