# graphify

**Repo:** https://github.com/Graphify-Labs/graphify · **PyPI:** `graphifyy`
(double y; the CLI is `graphify`)

## What it is

Turns a folder — code, docs, PDFs, images — into a queryable knowledge graph.
Code is parsed locally and deterministically with tree-sitter (37+ languages);
no LLM and no API key for a code-only run. Docs/images use an LLM backend only
if you set one (Gemini key), otherwise the host agent is the LLM. Communities
are found with Leiden clustering.

Outputs into `<target>/graphify-out/`:
- `graph.html` — interactive force-directed graph
- `GRAPH_REPORT.md` — god nodes, surprising connections, suggested questions
- `graph.json` — the raw queryable graph

## graphify vs Basic Memory

| | graphify | Basic Memory |
|---|---|---|
| content | derived structure over a codebase | curated long-term facts |
| built by | automatic AST + clustering | you + the AI, by hand |
| lifespan | disposable, rebuild anytime | permanent, versioned |
| edit by hand | no (regenerate) | yes (it's the point) |

Use both: graphify to *understand* a repo fast, Basic Memory to *remember*
what you concluded.

## How to use

Per-harness skill (registers `/graphify`):
```
graphify install --platform <claude|codex|cursor|gemini|...>
```

Then:
```
/graphify .                     # build graph for the current repo
/graphify https://github.com/owner/repo
graphify query "how does auth work"
graphify extract <path>         # headless, for CI/scripts
graphify update <path>          # incremental re-extract
```

Fast path: once `graphify-out/graph.json` exists, natural-language questions
about the repo are answered from the graph instead of rebuilding.

## Install / upgrade

```
uv tool install graphifyy
uv tool upgrade graphifyy
```
