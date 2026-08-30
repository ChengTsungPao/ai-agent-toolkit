# Working on ai-dev-env

This repo provisions a personal AI dev environment: it installs a fixed set of
tools and wires them — plus skills, plugins, and always-on guidelines — into
whatever AI harness you run (Claude Code, Codex, Cursor), on
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
| `[guidelines]` | always-on behavioural rules, marker-injected into each harness's `AGENTS.md` (+ a one-line ref in `CLAUDE.md`) | `guidelines`, `wire` |
| `[[tool]]` | a CLI installed by a package manager. A `[tool.mcp]` sub-block ⇒ it is also wired as an MCP server | `install`, `doctor`, `wire` |
| `[[skill]]` | a third-party skill — git repo + sub-paths, shallow-cloned **fresh at install** (latest, not auto-updated after) | `skills`, `wire` |
| `[[plugin]]` | a plugin ecosystem installed through the harness's own plugin mechanism (which also updates it) | `plugins`, `wire` |

Your **own** skills go as committed folders under `skills/<name>/` (with a
`SKILL.md`); `wire` / `skills` copies them into `~/.claude/skills/` and
`$CODEX_HOME/skills/`. Cursor has no skills dir — its paths are printed for
manual wiring.

`setup.py` commands: `report` (default, grouped status) · `install` · `config` ·
`wire <harness>` · `skills` · `plugins` · `guidelines` · `doctor`. `wire`
automates Claude Code and Codex fully; for Cursor / generic it prints the MCP
JSON and skill paths to apply by hand.

Gemini CLI and Google Antigravity are **not** wired by this repo (no reliable
global config path known / not in active use). Add them to `WIRERS` if that
changes.

There is deliberately **no `ai-dev-env` skill** — an agent learns about the repo
from the generated "Environment repo" section in the installed `AGENTS.md`, and
`setup.py report` is the live status command. Do not add one.

## Layout

Data flow: **`manifest.toml` declares → `scripts/setup.py` acts →** the rest is
content it distributes or notes.

| path | what it's for | you edit it to… |
|---|---|---|
| `manifest.toml` | the declaration — 4 sections + decision table | add/change/remove any tool, skill, plugin, or the guidelines pointer |
| `scripts/` | the engine (`setup.py`, stdlib-only, py3.11+, run via `uv`) + the fresh-machine bootstrap (`install.sh` / `.ps1`) | add a new *kind* of thing or a subcommand — never for a new entry |
| `guidelines/` | the behavioural rules **distributed to** every machine (`AGENTS.md` = the rules; `CLAUDE.md` = a stub for other repos). Not this file. | change the always-on rules |
| `skills/` | the user's **own** skill bundles, copied verbatim to each harness (`skills/README.md` = format) | add one of the user's own skills |
| `harnesses/` | per-harness reference: what `wire <name>` does + manual steps | when a harness's wiring changes |
| `docs/` | optional per-entry pages — rationale + fiddly setup, not tutorials | record a real decision or a painful setup |
| `AGENTS.md`, `CLAUDE.md` (root) | how to work on this repo (this file) | when the repo's own structure/rules change |

`~/.ai-dev-env/config.toml` — the machine's secrets, **outside the clone**;
`setup.py config` creates it, and it can't be committed (it's in `$HOME`).

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

## Tests, lint, CI

```
uv run --python 3.12 --with pytest pytest                 # tests/  (manifest + setup.py)
uv run --python 3.12 --with ruff ruff check scripts tests
uv run --python 3.12 --with ruff ruff format scripts tests
```

`tests/` needs no repo dependency — pytest and ruff are fetched on demand.
`.pre-commit-config.yaml` runs ruff + pytest on commit (`pre-commit install` once).
`.github/workflows/ci.yml` runs lint (Linux) + tests (Linux **and** Windows) on
push/PR.

**Free-tier CI note:** this is a private repo on the Free plan (2,000
Linux-minutes/month; Windows drains 2×). If a CI check shows a *billing / quota /
spending-limit* message instead of test results, that's the monthly limit — **not
a code failure**. The local commands above are the source of truth; re-run them
and say so on the PR.

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
