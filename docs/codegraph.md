# CodeGraph

[colbymchenry/codegraph](https://github.com/colbymchenry/codegraph) — MIT.
Rust extraction kernel + TypeScript CLI/MCP, local SQLite (FTS5). 100% local,
no keys, no cloud.

## Why it's here alongside graphify

Both build a code knowledge graph; they're kept as separate tools while being
compared.

| | CodeGraph | graphify |
|---|---|---|
| shape | always-live **MCP server** | one-shot build → `graph.html` + `GRAPH_REPORT.md` + `graph.json` + `/graphify` skill |
| freshness | background daemon auto-syncs on file change (~0.3s) | manual `graphify --update` |
| best at | mid-coding "who calls X / impact of changing Y / how does X reach Y" | a shareable map of a repo, god-nodes / community view, onboarding to an unfamiliar codebase |
| output | MCP tool responses (`codegraph_explore`, `codegraph_node`, …) | files you open / share |

Pick one per repo while evaluating — running both means two indexes + two file
watchers.

## Setup

`setup.py install` runs the bundle installer (self-contained, **no Node needed**):
`curl -fsSL …/install.sh | sh` (macOS/Linux) or `irm …/install.ps1 | iex`
(Windows). It adds `~/…/codegraph/current/bin` to PATH — **open a new shell**
before `setup.py doctor` will see it.

`setup.py wire <harness>` registers the MCP as `codegraph serve --mcp`
(Windows: `cmd /c codegraph serve --mcp`). Post-install turns **telemetry off**
(`codegraph telemetry off`).

Do **not** run `codegraph install` yourself — it wires agents its own way and,
like graphify, writes to `~/.codex` rather than `$CODEX_HOME`. Let `setup.py
wire` handle it.

## Per project

```
cd your-repo
codegraph init          # builds .codegraph/codegraph.db
```

`codegraph init` writes a `.codegraph/.gitignore` for its own db, but add
`.codegraph/` to the project's `.gitignore` so the folder doesn't show in
`git status`. `codegraph uninit` removes it. `codegraph daemon` lists / stops
the background watchers.

## Use

The agent calls the MCP tools automatically for structural questions. CLI
equivalents:

```
codegraph impact <symbol>       # what changes if you touch this
codegraph callers <symbol>      # who calls it
codegraph callees <symbol>      # what it calls
codegraph explore "how does auth work"
codegraph affected <files...>   # test files hit by a change
codegraph status
```

## Upgrading

`setup.py upgrade` **does not** touch CodeGraph — its only upgrade path is
re-running the web installer, and on Windows that partially deletes the running
install: `install.ps1` does `Remove-Item -Recurse -Force` on `codegraph/current`,
but the `.node` kernel is file-locked by every `codegraph serve --mcp` the agents
have spawned, so the delete half-completes and then fails.

To upgrade by hand: close every agent/session using CodeGraph (or
`Stop-Process` the `codegraph/current/node.exe` processes), then re-run the
installer from `manifest.toml`. `setup.py doctor` afterwards to confirm.

## Uninstall

```
setup.py … (or)  claude mcp remove codegraph -s user ; codex mcp remove codegraph
codegraph uninit <each repo>
rm -rf ~/.local/…/codegraph   # ~/AppData/Local/codegraph on Windows
```
