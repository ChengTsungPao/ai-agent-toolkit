# Claude Code

**Automated by** `setup.py wire claude-code`:

- copies every `skills/<name>/` bundle → `~/.claude/skills/<name>/`
- `claude mcp add --scope user <id> -e <ENV> -- <command> <args>` for each MCP tool
- `graphify install --platform claude` (if graphify is installed and not skipped)
- guidelines: full text → `~/.claude/AGENTS.md`; a one-line reference block
  (marker-delimited) is appended to `~/.claude/CLAUDE.md`

## Manual / verification

```bash
claude mcp list                 # basic-memory should show "Connected"
claude mcp get basic-memory
ls ~/.claude/skills                     # bundled skills + graphify
cat ~/.claude/AGENTS.md                 # guidelines + env-repo pointer
```

## graphify

graphify ships its own skill installer; `wire` runs it for you
(`graphify install --platform claude`). It writes `~/.claude/skills/graphify/`
and a `~/.claude/CLAUDE.md` entry. Then `/graphify .` in any repo. Run it by
hand only if graphify was installed *after* the last `wire`.

## Removing

```bash
setup.py unwire claude-code      # MCP servers + bundled/[[skill]] dirs + guidelines block
setup.py statusline --off         # if the context segment was installed
```

`unwire` leaves installed CLIs and your local `config.toml` alone. To also
drop a CLI: `uv tool uninstall <id>` / `npm uninstall -g <pkg>`. graphify's own
skill dir is removed by `graphify` itself if needed.
