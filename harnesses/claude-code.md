# Claude Code

**Automated by** `setup.py wire claude-code`:

- copies `skills/ai-dev-env/SKILL.md` → `~/.claude/skills/ai-dev-env/SKILL.md`
- `claude mcp add --scope user <id> -e <ENV> -- <command> <args>` for each MCP tool
- guidelines: full text → `~/.claude/AGENTS.md`; a one-line reference block
  (marker-delimited) is appended to `~/.claude/CLAUDE.md`

## Manual / verification

```bash
claude mcp list                 # basic-memory should show "Connected"
claude mcp get basic-memory
ls ~/.claude/skills/ai-dev-env
```

Invoke the skill in a session with `/ai-dev-env`.

## graphify

graphify ships its own skill installer:

```bash
graphify install --platform claude
```

That writes `~/.claude/skills/graphify/` and a `~/.claude/CLAUDE.md` entry.
Then `/graphify .` in any repo.

## Removing

```bash
claude mcp remove basic-memory -s user
rm -rf ~/.claude/skills/ai-dev-env
```
