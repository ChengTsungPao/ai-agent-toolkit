# Google Antigravity (`agy`)

**Automated by** `setup.py wire antigravity` (needs the `agy` CLI on PATH).
Everything lands in Antigravity's global config root, `~/.gemini/config/`
(override with `$AGY_CONFIG_HOME`):

- skills: every `skills/<name>/` bundle and `[[skill]]` → `<root>/skills/<name>/`
- MCP: each manifest MCP tool is **merged** into `<root>/mcp_config.json`
  (`{"mcpServers": {id: {command, args, env}}}`). Hand-added servers are never
  removed; only manifest ids are rewritten. Commands are resolved to absolute paths.
- guidelines: full text → `<root>/AGENTS.md` (marker-delimited block)
- graphify: `graphify install --platform antigravity[-windows]` (if installed)
- remote control: prompts during wire/setup to enable Remote Control with an instance name
  (defaults to existing or `Dev-Workstation`) and starts the daemon immediately; if skipped,
  prints instructions on how to enable anytime via `agy remote-control start --name <name>`.
  Control sessions at https://antigravity.google.com/
- plugins: none — `superpowers` has no Antigravity install path

Memory is selected automatically: `wire antigravity` prefers the local
Personal Memory Hub (`memorycore`) when MemoryCore is healthy, and falls back
to Basic Memory when the hub is absent or unreachable.

## Verify

```bash
setup.py report
agy            # then: Additional Options (...) > MCP Servers
```

## Not covered

Claude Code hooks (e.g. the LinkedIn daily-limit hook) and the statusline are
Claude-specific. Antigravity hooks live in `<root>/hooks.json` (different schema).

## Removing

```bash
setup.py unwire antigravity   # managed MCP entries + skill dirs + guidelines block
```

Leaves hand-added MCP servers, installed CLIs and your local `config.toml` alone.
