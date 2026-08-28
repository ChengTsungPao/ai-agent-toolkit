# Codex CLI (OpenAI)

**Automated by** `setup.py wire codex`:

- copies the skill → `$CODEX_HOME/skills/ai-dev-env/SKILL.md`
  (`CODEX_HOME` defaults to `~/.codex`; some managed setups override it —
  the script honours the env var)
- `codex mcp add --env <K=V> <id> -- <command> <args>` for each MCP tool
- guidelines: full text → `$CODEX_HOME/AGENTS.md` (marker-delimited block)

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
graphify install --platform codex
```

Note: `graphify install` writes to `~/.codex/skills/graphify/` and ignores
`$CODEX_HOME`. If your Codex runs with a non-default `CODEX_HOME` (e.g. a
managed / orca setup), copy the folder over:

```bash
cp -r ~/.codex/skills/graphify "$CODEX_HOME/skills/"
```

## Removing

```bash
codex mcp remove basic-memory
rm -rf "$CODEX_HOME/skills/ai-dev-env"
```
