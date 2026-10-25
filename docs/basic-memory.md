# Basic Memory (fallback)

See [memory-hub.md](memory-hub.md) for how the toolkit chooses between the hub and Basic Memory.

`setup.py wire claude-code`, `setup.py wire codex`, and
`setup.py wire antigravity` prefer the local Personal
Memory Hub when its MCP server and MemoryCore health endpoint are available.
Basic Memory is used only when the hub is unavailable. Set
`PERSONAL_MEMORY_HUB_DIR` to override the default `$HOME/personal-memory-hub`.

**Repo:** https://github.com/basicmachines-co/basic-memory ·
**Docs:** https://docs.basicmemory.com · **License:** AGPL-3.0

## What it is

A private, local-first memory layer for AI assistants. Every memory is a plain
Markdown file on your disk; a local SQLite database indexes them for full-text
and (local) semantic search. The knowledge graph is just wiki-links and
`relation`/`observation` lines inside those files — fully human-readable and
human-editable.

## Why this one (vs Cognee / Graphiti / mem0)

The requirement was **memory you can review and edit**. Graph-DB memory systems
build an opaque blob you can only query. Basic Memory keeps memory as files you
open in any editor or Obsidian, diff in git, and hand-correct.

Trade-off: the "graph" is what you and the AI write by hand, not auto-extracted
entities. For large-scale automatic code graphs, use **graphify** instead — the
two are complementary.

## Privacy

- All data local: `~/basic-memory/` (Markdown) + local SQLite index.
- No account, no network needed for core use.
- The only external party is your LLM, via the harness — Basic Memory itself
  calls no LLM.
- Minimal anonymous telemetry about cloud-signup prompts only (never file
  contents / titles / PII / IP). Disabled here via `BASIC_MEMORY_NO_PROMOS=1`
  and `cloud_promo_opt_out=true`.
- The optional paid Cloud tier is fully opt-in and unused.

## Layout on this machine

```
~/basic-memory/
├── code/            # architecture decisions, conventions, gotchas per project
├── knowledge/       # personal long-term facts, preferences, project list, people
├── conversations/   # distilled highlights from AI sessions
├── research/        # summaries of docs, web pages, PDFs
└── .git/            # snapshot history — `git revert` bad AI writes
```

A single project named `main` points at `~/basic-memory`. Scopes are folders,
so the graph stays unified and cross-scope links work.

## How to use

**From any wired harness** — just talk:
- "remember that we decided X for project Y" → the agent calls `write_note`
- "what do I know about Z?" → `search_notes` / `build_context`
- "update the note about our deploy process" → `edit_note`

**CLI** (`basic-memory` or `bm`):
```
basic-memory status                    # index health
basic-memory reindex                   # rebuild FTS + embeddings
basic-memory doctor                    # file/db consistency
basic-memory tool search-notes "query"
basic-memory tool write-note --title T --folder knowledge --tags a,b
basic-memory tool recent-activity
```

## Maintenance

1. AI writes notes into the right scope folder via MCP.
2. Periodically open `~/basic-memory` in Obsidian: merge duplicate entities,
   fix relations, delete stale facts, add context.
3. `git commit` as a snapshot; `git revert` if the AI wrote garbage.
4. Save a file → the running MCP server re-indexes automatically.

## Config touched by this repo

| setting | value | why |
|---|---|---|
| env `BASIC_MEMORY_NO_PROMOS` | `1` | kill telemetry + cloud prompts |
| `cloud_promo_opt_out` | `true` | same, persisted in config.json |

## Lifecycle hooks

- `setup.py wire claude-code` / `setup.py wire codex` automatically run
  `basic-memory hook install` for the corresponding harness. This installs
  idempotent session-start context and pre-compact lifecycle capture hooks;
  user-authored hooks are preserved. Use `basic-memory hook remove --harness
  <claude|codex>` to remove Basic Memory's entries only.
- Reranker: `reranker_enabled=true` for higher-quality semantic search.
