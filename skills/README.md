# skills/

Skill bundles installed into every harness by `setup.py wire <harness>`
(and by `setup.py skills`).

Two kinds of skill:

- **Local bundles** — folders in *this* directory. Committed, frozen, yours to
  edit. Put your own skills here.
- **External skills** — `[[skill]]` entries in `manifest.toml`. Not stored here;
  `setup.py` shallow-clones the source repo and copies the listed sub-paths at
  install time, so you always get the **latest** version. Not auto-updated
  afterwards — re-run `setup.py skills` to refresh.

## Layout

One folder per skill, each containing a `SKILL.md` with frontmatter:

```
skills/
  my-skill/
    SKILL.md          # required — name + description frontmatter, then body
    references/       # optional — supporting files, copied as-is
```

```markdown
---
name: my-skill
description: One line the agent matches on to decide when to load this skill.
---

# my-skill

What it does and how to use it.
```

## Install targets

| harness | destination |
|---|---|
| Claude Code | `~/.claude/skills/<name>/` |
| Codex | `$CODEX_HOME/skills/<name>/` |
| Cursor / Gemini CLI | no native skills dir — `wire` prints the bundle paths to wire manually |

`wire` copies the whole bundle folder, overwriting the harness copy, so the repo
stays the source of truth. Edit here, re-run `wire`.

## Not here

`graphify` ships its own per-harness skill via `graphify install --platform X`
(it manages its own `references/`), so it is a `[[tool]]` in `manifest.toml`,
not a bundle here.
