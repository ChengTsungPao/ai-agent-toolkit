# Working on this repo

This repo provisions a personal AI dev environment: it installs a fixed set of
tools and wires them — plus skills, plugins, and always-on guidelines — into
whatever AI harness you run (Claude Code, Codex, Antigravity, Cursor), on
Windows / macOS / Linux.

Also follow the behavioural rules in [`guidelines/AGENTS.md`](guidelines/AGENTS.md).

## Setup on a fresh machine

```sh
./scripts/install.sh            # macOS/Linux   (install.ps1 on Windows)
./scripts/install.sh bootstrap  # install missing + wire every harness found
```

`bootstrap` = `install` (asks all vs each) then `wire` for each of Claude Code /
Codex whose CLI is on PATH. Run the steps individually when you need to.

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
`$CODEX_HOME/skills/` and `~/.gemini/config/skills/`. Cursor has no skills dir — its paths are printed for
manual wiring.

`setup.py` commands: `report` (default) · `bootstrap` · `install` · `upgrade` ·
`config` · `choose` · `statusline` · `wire <harness>` · `unwire <harness>` ·
`skills` · `plugins` · `guidelines` · `doctor`. `wire` automates Claude Code and
Codex fully (including `graphify install`); for Cursor / generic it prints the
MCP JSON and skill paths to apply by hand. `unwire` reverses `wire` (MCP + skill
dirs + guidelines block) but never touches an installed CLI or the config.

Google Antigravity (`agy`) is wired via `wire antigravity` into `~/.gemini/config/`
(skills, merged `mcp_config.json`, `AGENTS.md`; see `harnesses/antigravity.md`).
Gemini CLI is **not** wired. Add harnesses to `WIRERS`.

There is deliberately **no repo-management skill** — an agent learns about the repo
from the generated "Environment repo" section in the installed `AGENTS.md`, and
`setup.py report` is the live status command. Do not add one.

## Layout

Data flow: **`manifest.toml` declares → `scripts/setup.py` acts →** the rest is
content it distributes or notes.

| path | what it's for | you edit it to… |
|---|---|---|
| `manifest.toml` | the declaration — 4 sections + decision table | add/change/remove any tool, skill, plugin, or the guidelines pointer |
| `scripts/` | the engine — `setup.py` (the orchestrator), `_common.py` (constants + ANSI + `run()`, the shared kernel), `_statusline.py` (the one extracted subcommand); all stdlib-only, py3.11+, run via `uv` — plus the fresh-machine bootstrap (`install.sh` / `.ps1`) | add a new *kind* of thing or a subcommand — never for a new entry |
| `guidelines/` | the behavioural rules **distributed to** every machine (`AGENTS.md` = the rules; `CLAUDE.md` = a stub for other repos). Not this file. | change the always-on rules |
| `skills/` | the user's **own** skill bundles, copied verbatim to each harness (`skills/README.md` = format) | add one of the user's own skills |
| `harnesses/` | per-harness reference: what `wire <name>` does + manual steps | when a harness's wiring changes |
| `contrib/` | harness tweaks that aren't a tool/skill/plugin/MCP — each `contrib/<name>/` is helper scripts + one `setup.py` subcommand (currently `statusline/`: the Claude Code context-usage segment) | add a new opt-in harness customization |
| `docs/` | optional per-entry pages — rationale + fiddly setup, not tutorials | record a real decision or a painful setup |
| `AGENTS.md`, `CLAUDE.md` (root) | how to work on this repo (this file) | when the repo's own structure/rules change |

`~/.<repo>/config.toml` — **outside the clone**, per machine. `[env]` holds
MCP secrets; `[skip].ids` lists tools/skills/plugins to leave out of
`install` / `wire` (set via `setup.py choose`; the first run asks). `setup.py
config` creates it; it can't be committed (it's in `$HOME`).

## Making a change

1. **Edit `manifest.toml`** (or `guidelines/AGENTS.md` for a rule). Adding an
   entry never needs a `setup.py` change — the manifest *is* the input.
2. **Check** → `uv run --python 3.12 scripts/setup.py report`, then `… doctor`.
3. **Apply** → `… wire claude-code` (idempotent — re-run any time).
4. **Optional doc** → add `docs/<id>.md` and link it from the entry's `docs = …`
   *only* if there's a real decision or a painful setup worth recording; skip it
   when `usage.short` already says enough.

`setup.py` itself changes only for a whole new *kind* of thing or a new
subcommand — and stays stdlib-only, Python 3.11+. It is the single orchestrator:
`cmd_*` functions plus thin cores (`_install`, `_wire`) they and `bootstrap`
share. Shared constants / ANSI / `run()` live in `_common.py`; a subcommand only
moves into its own `scripts/_<name>.py` when it is genuinely separable (touches a
different config surface, pairs with a `contrib/` dir) — `_statusline.py` is the
precedent, don't split further without reason.

A **harness tweak that isn't a tool/skill/plugin/MCP** (something that edits a
harness's own config, not the manifest) goes in `contrib/<name>/` with its own
`setup.py` subcommand — opt-in, reversible (`--off`), and it must not run as part
of `wire`. `statusline` is the model to copy.

## Tests, lint, CI

```
uv run --python 3.12 --with pytest pytest                 # tests/  (manifest + setup.py)
uv run --python 3.12 --with ruff ruff check scripts tests
uv run --python 3.12 --with ruff ruff format scripts tests
```

`tests/` needs no repo dependency — pytest and ruff are fetched on demand.
`.pre-commit-config.yaml` runs ruff + pytest on commit (`pre-commit install` once).
`.github/workflows/ci.yml` runs lint (Linux) + tests (Linux, Windows **and**
macOS) on push/PR.

**Free-tier CI note:** this is a private repo on the Free plan (2,000
Linux-minutes/month; Windows drains 2×, macOS 10× — the jobs run in seconds, so
this stays cheap). If a CI check shows a *billing / quota / spending-limit*
message instead of test results, that's the monthly limit — **not a code
failure**. The local commands above are the source of truth; re-run them
and say so on the PR.

## Invariants — don't break these

1. **No hard-coded clone path or repo name.** The repo must work cloned anywhere
   under any directory name. Scripts find their own root and name dynamically
   (`Path(__file__).resolve().parent.parent`, `$PSScriptRoot`,
   `${BASH_SOURCE[0]}`); every manifest path (`docs`, `guidelines.canonical`,
   `[[skill]].paths`) is relative to that root.

2. **Secrets never enter the repo.** They live in `~/.<repo>/config.toml`
   (created by `setup.py config`; dir overridable with `$<REPO>_HOME`).
   Mind the dot — `~/.<repo>/` is machine state, `~/<repo>/` is the clone.

3. **The installed guidelines' "Environment repo" section is generated** by
   `setup.py` (`repo_display()`), with this machine's real path. Never hand-write
   it into `guidelines/AGENTS.md`.

4. **Per-OS code lives in exactly three places:** `[tool.install]` OS keys,
   `[tool.mcp.<os>]` command overrides, and `_persist_env()`. Nowhere else.

5. **Style:** `pathlib.Path` in code, never string-joined paths; forward slashes
   in docs; `.gitattributes` keeps everything LF except `*.ps1` (CRLF).

## AI Agent Git Commit Attribution

When contributing or committing changes to this repository, AI coding agents (Claude Code, Antigravity, etc.) must append the corresponding official `Co-authored-by` trailer at the bottom of the commit message (preceded by an empty line) so that contributions and avatars render properly on GitHub:

- **Claude Code**:
  ```text
  Co-authored-by: Claude <noreply@anthropic.com>
  ```
- **Antigravity**:
  ```text
  Co-authored-by: Antigravity <347312419+antigravity-code@users.noreply.github.com>
  ```
- **Codex**:
  ```text
  Co-authored-by: Codex <267193182+codex@users.noreply.github.com>
  ```

Rules:
1. Ensure there is a blank line separating the commit message body from the trailers.
2. Maintain standard Git trailer format: `Co-authored-by: Name <email>`.
