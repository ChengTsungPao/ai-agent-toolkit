---
name: ai-dev-env
description: Personal AI dev-environment manifest. Invoke to report which managed tools are installed, what each is for, and how to use them — and, on request, to install missing tools or wire them into the current harness (Claude Code, Codex, Cursor, Gemini CLI, …). Cross-platform (Windows/macOS/Linux).
---

# ai-dev-env

This skill is the front door to the user's environment repo:
**https://github.com/ChengTsungPao/ai-dev-env**

The repo's `manifest.toml` is the source of truth for every tool the user
deliberately installed, its purpose, its per-OS install command, and how it is
wired into AI harnesses. `scripts/setup.py` acts on that manifest.

## Locating the repo

Check in order and use the first that exists:

1. `$AI_DEV_ENV_HOME`
2. `~/ai-dev-env`
3. `~/.ai-dev-env`

If none exist, offer to clone it:
`git clone https://github.com/ChengTsungPao/ai-dev-env ~/ai-dev-env`

Let `REPO` be that path. All commands below run from `REPO`.

## When invoked with no specific ask → report

Run the report and relay it to the user in full:

```
uv run --python 3.12 "$REPO/scripts/setup.py" report
```

(Windows PowerShell: `uv run --python 3.12 "$REPO\scripts\setup.py" report`)

Present, per tool: **name · installed? · one-line purpose · how to use it**.
End with anything missing and the exact command to install it. Do not paraphrase
away the usage lines — the user invokes this skill specifically to be reminded
what each tool does and how to drive it.

## When the user asks to install / fix / set up

1. First run `report` (or `doctor`) to see what is missing.
2. **Ask the user which mode**, and list exactly what will be installed +
   the install command for each:
   - **install all** — no per-item prompt
   - **confirm each** — approve tool by tool
3. Then run:
   - all:  `uv run --python 3.12 "$REPO/scripts/setup.py" install --all`
   - each: `uv run --python 3.12 "$REPO/scripts/setup.py" install --each`
   - subset: append tool ids, e.g. `install basic-memory --all`
4. `setup.py` prints the plan again and (without `--all`/`--each`) prompts
   interactively; if you are running it non-interactively, pass the flag that
   matches the user's choice.

## Wiring into a harness

```
uv run --python 3.12 "$REPO/scripts/setup.py" wire <claude-code|codex|cursor|gemini-cli|generic>
```

This (a) copies this SKILL.md into the harness's skills dir, (b) registers each
MCP-type tool, and (c) installs the agent guidelines. For `cursor` /
`gemini-cli` / `generic` it prints the JSON block to merge (those clients have
no reliable CLI). See `REPO/harnesses/<name>.md` for per-harness details.

## Agent guidelines

`REPO/guidelines/AGENTS.md` holds always-on behavioral rules. `AGENTS.md` is
canonical; `CLAUDE.md` just references it (better cross-harness compatibility).
`wire` installs them; to (re)apply everywhere without a full wire:

```
uv run --python 3.12 "$REPO/scripts/setup.py" guidelines
```

Targets: `~/.claude/AGENTS.md` (+ a one-line ref in `~/.claude/CLAUDE.md`),
`$CODEX_HOME/AGENTS.md`, `~/.gemini/GEMINI.md`. All edits are marker-delimited
and idempotent.

## Adding a new tool later

Append a `[[tool]]` block to `REPO/manifest.toml` (schema documented at the top
of that file), commit, push. No code change needed for install/report/doctor;
add a `[tool.mcp]` block if it is an MCP server so `wire` picks it up.

## Keeping tools current

```
uv tool upgrade --all
```

## Notes

- `setup.py` needs Python 3.11+ for `tomllib`; always launch it via
  `uv run --python 3.12` so this holds on any machine.
- Nothing in `install` is destructive and it always shows a plan first.
- Tool-specific docs: `REPO/docs/tools/*.md`.
