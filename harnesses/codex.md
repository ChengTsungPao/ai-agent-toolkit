# Codex CLI (OpenAI)

**Automated by** `setup.py wire codex`:

- copies the skill → `$CODEX_HOME/skills/ai-dev-env/SKILL.md`
  (`CODEX_HOME` defaults to `~/.codex`; some managed setups override it —
  the script honours the env var)
- `codex mcp add <id> --env <K=V> -- <command> <args>` for each MCP tool

## Manual / verification

```bash
codex mcp list                  # basic-memory → enabled
codex mcp get basic-memory
```

Config file: `$CODEX_HOME/config.toml`, block:

```toml
[mcp_servers.basic-memory]
command = "/abs/path/to/basic-memory"     # or basic-memory.exe on Windows
args    = ["mcp"]
env     = { BASIC_MEMORY_NO_PROMOS = "1" }
```

On Windows use the full path to `basic-memory.exe`
(`%USERPROFILE%\.local\bin\basic-memory.exe`) — Codex does not always resolve
`PATH` for MCP children.

## graphify

```bash
graphify install --platform codex      # writes AGENTS.md section
```

## Removing

```bash
codex mcp remove basic-memory
rm -rf "$CODEX_HOME/skills/ai-dev-env"
```
