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

## Guidelines

`setup.py guidelines gemini-cli` writes the full guidelines (incl. the
"Environment repo" pointer) as a marker-delimited block in `~/.gemini/GEMINI.md`.

## Skills

Gemini CLI has no skills dir. `setup.py wire gemini-cli` prints the bundle
paths; add each as a GEMINI.md section or a custom command if you want it
always available.

## graphify

```bash
graphify install --platform gemini     # writes GEMINI.md section + hook
```
