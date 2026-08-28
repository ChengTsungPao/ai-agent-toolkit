# Any other MCP client

`setup.py wire generic` prints a standard MCP server block. Most clients
(Cline, Windsurf, Zed, Continue, VS Code, Claude Desktop, …) accept the same
shape — only the config file path differs.

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

- **command**: on Windows, the absolute path to `basic-memory.exe`
  (`%USERPROFILE%\.local\bin\basic-memory.exe`); on macOS/Linux, `basic-memory`
  is fine if `~/.local/bin` is on PATH.
- **transport**: stdio (default). For HTTP clients run
  `basic-memory mcp --transport streamable-http --port 8000` and point the
  client at `http://127.0.0.1:8000/mcp`.

For the skill itself: load `skills/ai-dev-env/SKILL.md` as a system prompt /
rules / context file, however that client supports persistent instructions.

## Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or
`%APPDATA%\Claude\claude_desktop_config.json` (Windows) — same `mcpServers`
shape.
