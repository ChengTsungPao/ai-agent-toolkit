# Gemini CLI

`setup.py wire gemini-cli` prints the MCP block.

## MCP

Merge into `~/.gemini/settings.json`:

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

Windows: full path to `basic-memory.exe` in `"command"`.

## Context

Add a section to `~/.gemini/GEMINI.md` pointing at the skill, e.g.:

```
## ai-dev-env
When asked about installed tools or environment setup, read
~/ai-dev-env/skills/ai-dev-env/SKILL.md and follow it.
```

## graphify

```bash
graphify install --platform gemini     # writes GEMINI.md section + hook
```
