# Personal Memory Hub and this toolkit

[Personal Memory Hub](https://github.com/ChengTsungPao/personal-memory-hub) is a separate repo: a local
MemoryCore service plus per-harness adapters (MCP server and lifecycle hooks) for Claude Code, Codex and
Antigravity. This toolkit does not contain it and does not install it. It only **detects** it and **wires**
each harness to it. When the hub is absent, it falls back to [Basic Memory](basic-memory.md).

## Who owns what

| | This toolkit (`ai-agent-toolkit`) | Personal Memory Hub |
|---|---|---|
| Role | Decide which memory backend a harness uses, and write the harness config | The memory service and everything that talks to it |
| MCP server | Registers it (`memorycore`) in the harness config | `agents/claude-code/mcp/server.mjs` (shared by all three harnesses) |
| Lifecycle hooks | Registers them in the harness's hook file | The hook scripts themselves: `agents/<harness>/hooks/*.mjs` |
| Hook logic (recall at session start, capture at stop) | **None.** Change it in the hub repo | Yes |

So a change to *what a hook does* is a hub PR; a change to *where it is registered* is a toolkit PR.
A toolkit PR that registers a new hook script needs the matching hub PR merged first, or the hook points
at a file that does not exist.

## How `wire` decides

`setup.py wire claude-code|codex|antigravity` calls `_memory_backend()`:

1. The hub is **present** when `$PERSONAL_MEMORY_HUB_DIR` (default `~/personal-memory-hub`) contains
   `agents/claude-code/mcp/server.mjs`, `node` is on `PATH`, and MemoryCore answers
   `GET $TDAI_ENDPOINT/health` (default `http://127.0.0.1:8420`) with 200.
2. Present: register the `memorycore` MCP server **and** the hub's hooks, and remove Basic Memory's MCP entry.
3. Absent (not cloned, not running, or no `node`): register Basic Memory and its hooks; remove the hub's
   MCP entry and hooks.

   Switching from Basic Memory to the hub does not remove Basic Memory's own hooks. Run
   `setup.py unwire <harness>` first if you do not want both active.

Re-run `wire` after starting or stopping the hub to switch. `unwire <harness>` removes both.

## Which hooks, registered where

| Harness | File the toolkit edits | Events | Scripts (in the hub repo) |
|---|---|---|---|
| Claude Code | `~/.claude/settings.json` (`hooks`) | `SessionStart`, `Stop` | `agents/claude-code/hooks/memory-recall.mjs`, `memory-capture.mjs` |
| Codex | `$CODEX_HOME/hooks.json` (`hooks`) | `SessionStart`, `Stop` | `agents/claude-code/hooks/memory-recall.mjs`, `agents/codex/hooks/memory-capture.mjs` |
| Antigravity | `$AGY_CONFIG_HOME/hooks.json` (default `~/.gemini/config/hooks.json`), top-level `memory-hub` key | `SessionStart`, `Stop` | `agents/antigravity/hooks/memory-recall.mjs`, `memory-capture.mjs` |

- Existing hooks are kept. Only entries whose command mentions `memory-recall.mjs` or `memory-capture.mjs`
  are replaced or removed.
- Each hook command is `node "<hub>/agents/.../<script>.mjs"`, so it follows `PERSONAL_MEMORY_HUB_DIR`.
- `SessionStart` has a 10 s timeout and `Stop` 45 s. Hooks are meant to fail open: a hub that is down
  must not block a turn.
- When wiring, the toolkit takes the `TDAI_*` settings from the environment, falling back to the existing
  `memorycore` entry in `~/.claude.json`, so re-wiring one harness does not lose them in another.

## Check it

```bash
curl -s http://127.0.0.1:8420/health          # the hub is up
setup.py wire claude-code                    # prints "Memory Hub hooks installed: <file>"
```

Then start a new session in the harness; the first reply should know the project's memory (hook
`SessionStart`), and after a turn the conversation should appear in MemoryCore (hook `Stop`). A hook
change only takes effect in a **new** session.
