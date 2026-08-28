# Superpowers

**Source:** [obra/superpowers](https://github.com/obra/superpowers) — MIT ©
Jesse Vincent. Installed as a **plugin**, not vendored.

## What it is

A full software-development methodology for coding agents: 20+ composable skills
that **auto-activate** based on what you're doing, plus a bootstrap
(`using-superpowers`) that makes the agent check for a relevant skill before
every task. Includes test-driven development, systematic debugging, brainstorming,
code-review workflows, and git-worktree management.

Unlike `grill-me` (one user-invoked skill), Superpowers is an integrated system —
the skills are meant to fire on their own, and cherry-picking breaks the design.

## Why plugin, not vendored

It's large and ships updates frequently. Vendoring would bloat this repo and
freeze you on one version. `manifest.toml` records it under `[[plugin]]` and
`setup.py` installs it per-harness; updates come from the plugin mechanism.

## Install / update per harness

| harness | install | update |
|---|---|---|
| Claude Code | `claude plugin install superpowers@claude-plugins-official` | `claude plugin update superpowers` |
| Gemini CLI | `gemini extensions install https://github.com/obra/superpowers` | `gemini extensions update superpowers` |
| Codex CLI | interactive: `/plugins` → search `superpowers` → Install | — |
| Cursor | interactive: `/add-plugin superpowers` | — |

`setup.py wire <harness>` and `setup.py plugins <harness>` run the scriptable
ones and print the interactive ones.

## How to use

Nothing to invoke — once installed, skills activate automatically. To learn the
system, ask the agent to "use superpowers" or read its `using-superpowers` skill.

## Uninstall (Claude Code)

```
claude plugin uninstall superpowers
```
