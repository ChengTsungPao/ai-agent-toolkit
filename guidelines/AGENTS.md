<!--
  Canonical agent behavioral guidelines for this environment.
  Source: https://github.com/multica-ai/andrej-karpathy-skills (MIT), after
  Andrej Karpathy's notes on LLM coding pitfalls.
  Edit here, then re-run `setup.py guidelines`.
  On install, setup.py appends an "Environment repo" section pointing at this
  machine's clone; keep this file to the behavioural rules only.
-->

# Agent Guidelines

Behavioral guidelines to reduce common LLM coding mistakes. Merge with
project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial
tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes,
simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it
work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer
rewrites due to overcomplication, and clarifying questions come before
implementation rather than after mistakes.

## AI Agent Git Commit Attribution

When contributing or committing changes to this repository, AI coding agents (Claude Code, Antigravity, etc.) must append the corresponding official `Co-authored-by` trailer at the bottom of the commit message (preceded by an empty line) so that contributions and avatars render properly on GitHub:

- **Claude Code**:
  ```text
  Co-authored-by: Claude <noreply@anthropic.com>
  ```
- **Antigravity**:
  ```text
  Co-authored-by: Antigravity <347312419+antigravity-code@users.noreply.github.com>
  ```
- **Codex**:
  ```text
  Co-authored-by: Codex <267193182+codex@users.noreply.github.com>
  ```

Rules:
1. Ensure there is a blank line separating the commit message body from the trailers.
2. Maintain standard Git trailer format: `Co-authored-by: Name <email>`.
3. If none of these agents are used (e.g. human-only manual commit), do not append any trailer.

