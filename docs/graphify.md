# graphify

Repo: https://github.com/Graphify-Labs/graphify · PyPI `graphifyy` (double y;
CLI is `graphify`). See upstream for full usage; `manifest.toml` has the common
commands.

## graphify vs Basic Memory

Kept as separate tools on purpose:

| | graphify | Basic Memory |
|---|---|---|
| content | derived structure over a codebase | curated long-term facts |
| built by | automatic AST + Leiden clustering | you + the AI, by hand |
| lifespan | disposable, rebuild anytime | permanent, versioned |
| edit by hand | no (regenerate) | yes — that's the point |

Use graphify to *understand* a repo fast; Basic Memory to *remember* what you
concluded.

## Notes

- Registers its own per-harness skill via `graphify install --platform <name>`
  (it manages its own `references/`) — that's why it's a `[[tool]]`, not a
  `[[skill]]`.
- Code-only runs need no LLM / API key. Docs/images use Gemini if
  `GEMINI_API_KEY` is set, else the host agent.
