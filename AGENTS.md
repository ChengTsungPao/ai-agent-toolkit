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

## Making a change

1. **Edit `manifest.toml`** (or `guidelines/AGENTS.md` for a rule). Adding an
   entry never needs a `setup.py` change — the manifest *is* the input.
2. **Check** → `uv run --python 3.12 scripts/setup.py report`, then `… doctor`.
3. **Apply** → `… wire claude-code` (idempotent — re-run any time).
4. **Optional doc** → add `docs/<id>.md` and link it from the entry's `docs = …`
   *only* if there's a real decision or a painful setup worth recording; skip it
   when `usage.short` already says enough.

`setup.py` itself changes only for a whole new *kind* of thing or a new
subcommand — and stays stdlib-only, Python 3.11+.

## Invariants — don't break these

1. **No hard-coded clone path.** The repo must work cloned anywhere;
   `~/ai-dev-env` is only the recommended spot. Scripts find their own root
   (`Path(__file__).resolve().parent.parent`, `$PSScriptRoot`,
   `${BASH_SOURCE[0]}`); every manifest path (`docs`, `guidelines.canonical`,
   `[[skill]].paths`) is relative to that root.

2. **Secrets never enter the repo.** They live in `~/.ai-dev-env/config.toml`
   (created by `setup.py config`; dir overridable with `$AI_DEV_ENV_HOME`).
   Mind the dot — `~/.ai-dev-env/` is machine state, `~/ai-dev-env/` is the clone.

3. **The installed guidelines' "Environment repo" section is generated** by
   `setup.py` (`repo_display()`), with this machine's real path. Never hand-write
   it into `guidelines/AGENTS.md`.

4. **Per-OS code lives in exactly three places:** `[tool.install]` OS keys,
   `[tool.mcp.<os>]` command overrides, and `_persist_env()`. Nowhere else.

5. **Style:** `pathlib.Path` in code, never string-joined paths; forward slashes
   in docs; `.gitattributes` keeps everything LF except `*.ps1` (CRLF).
