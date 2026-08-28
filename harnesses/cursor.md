# Cursor

Cursor has no stable CLI for MCP/rules, so `setup.py wire cursor` prints the
blocks to paste.

## MCP

Merge into `~/.cursor/mcp.json` (global) or `<project>/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "basic-memory": {
      "command": "basic-memory",
      "args": ["mcp"],
      "env": { "BASIC_MEMORY_NO_PROMOS": "1" }
    }
  }
}
```

Windows: set `"command"` to the full path of `basic-memory.exe`.

## Skill as a rule

Create `<project>/.cursor/rules/ai-dev-env.mdc` (or add via Cursor Settings →
Rules) with the body of `skills/ai-dev-env/SKILL.md`. Set it to
`Agent Requested` with the description from the skill's frontmatter.

## graphify

```bash
graphify install --platform cursor     # writes .cursor/rules/graphify.mdc
```
