# Superpowers

[obra/superpowers](https://github.com/obra/superpowers) — MIT © Jesse Vincent.
A methodology-as-plugin: 20+ skills that **auto-activate** based on what you're
doing (TDD, systematic debugging, brainstorming, code review, git worktrees)
plus a `using-superpowers` bootstrap. It's an integrated system — cherry-picking
individual skills breaks it, so it's a `[[plugin]]` (installed through each
harness's own plugin mechanism, which also updates it), not vendored.

Once installed, nothing to invoke — skills fire on their own.

## Install / update / uninstall per harness

| harness | install | update | uninstall |
|---|---|---|---|
| Claude Code | `claude plugin install superpowers@claude-plugins-official` | `claude plugin update superpowers` | `claude plugin uninstall superpowers` |
| Codex CLI | interactive: `/plugins` → search `superpowers` → Install | — | `/plugins` |
| Cursor | interactive: `/add-plugin superpowers` | — | — |

(Upstream also supports Gemini CLI, Antigravity, and more — see the obra repo.
This repo doesn't wire those.)

`setup.py wire <harness>` / `setup.py plugins <harness>` runs the scriptable
ones and prints the interactive ones.
