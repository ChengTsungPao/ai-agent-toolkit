# statusline

An optional context-usage segment for the Claude Code statusLine — shows
` | ctx NN% (842k/1m)` at the bottom of the window, green / yellow / red.

```
setup.py statusline        # install
setup.py statusline --off   # remove, restore what was there before
```

## How it works

- `ctx.py` — reads the statusLine JSON on stdin, finds the newest `usage` record
  in `transcript_path`, prints the segment. Harness-agnostic; never raises.
- `statusline.sh` — the wrapper Claude Code actually runs: it first runs
  **whatever statusLine command was there before** (saved to
  `~/.claude/ai-dev-env-statusline/statusline-prev.txt` on install) so a host's
  own hook keeps working, then appends the `ctx.py` segment.

`setup.py statusline` copies both into `~/.claude/ai-dev-env-statusline/` and
points `~/.claude/settings.json` `statusLine` at the wrapper.

## Caveats

- **Orca** owns the statusLine slot as a data pipe and may **rewrite
  `settings.json`** — if the segment disappears, re-run `setup.py statusline`.
- **macOS**: works on plain Claude Code. macOS + Orca is **untested** (whether
  Orca passes Claude Code's statusLine through).
- The number is the context size *at the start of the last turn* — lags by one.
- Needs a real `python3` / `python` on PATH (falls back to `uv run`).
