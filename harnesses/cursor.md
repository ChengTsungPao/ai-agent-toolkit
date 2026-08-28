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

## Guidelines + skills

Cursor has no global skills dir. Options:

- Put `guidelines/AGENTS.md` at a project root as `AGENTS.md` (Cursor reads it),
  or as `.cursor/rules/agents.mdc` with `alwaysApply: true`.
- For each `skills/<name>/SKILL.md` you want active, add its body as a
  `.cursor/rules/<name>.mdc` rule (`Agent Requested`, description from the
  frontmatter).

`setup.py wire cursor` prints the bundle paths.

## graphify

```bash
graphify install --platform cursor     # writes .cursor/rules/graphify.mdc
```
