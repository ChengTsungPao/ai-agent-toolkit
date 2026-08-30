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
`wire <harness>` · `skills` · `plugins` · `guidelines` · `doctor`.

## Making changes

- **Add / change a tool, skill, plugin, or guideline** → edit `manifest.toml`
  (or `guidelines/AGENTS.md`) **only**. No `setup.py` change is needed for any of
  the four kinds.
- **Test** → `uv run --python 3.12 scripts/setup.py report` and `… doctor`.
  For wiring changes, `… wire claude-code` is idempotent.
- **Docs** live in `docs/tools/<id>.md`, one per tool/skill/plugin; link them
  from the manifest entry's `docs = …`.
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
