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
- `wrapper.py` — what Claude Code actually runs. It first runs **whatever
  statusLine command was configured before this one** (saved to
  `~/.claude/<repo>-statusline/statusline-prev.txt` on install) so a host's
  own hook keeps working, then appends the `ctx.py` segment. Pure Python +
  stdlib.

`setup.py statusline` copies both into `~/.claude/<repo>-statusline/` and
sets `~/.claude/settings.json` `statusLine` to
`uv run --python 3.12 --no-project "<…>/wrapper.py"` (falls back to a validated
system `python` if `uv` is absent).

The interpreter is a **bare command name, never an absolute quoted path**.
Claude Code on Windows runs the statusLine via `cmd.exe /c "<command>"`; cmd
strips a matched outer quote pair, so a leading `"C:\…\uv.exe"` becomes
unbalanced and the whole command fails silently (`The filename, directory name,
or volume label syntax is incorrect`). A bare `uv` — like the `bash` the shell
version used — is resolved from PATH and avoids this.

## Requirements

- **`uv`** (the repo's one prerequisite) or a real `python3` / `python` on PATH.
  No shell is involved for a plain Claude Code install.
- **`sh` or `bash`** — only when chaining to a previous command (e.g. under a
  host like Orca). That command is POSIX `sh` syntax; on Windows this is the
  Git Bash that such hosts already require. If neither resolves, only the
  previous segment is skipped — the `ctx` segment still renders.

## Caveats

- **Orca** owns the statusLine slot as a data pipe and may **rewrite
  `settings.json`** — if the segment disappears, re-run `setup.py statusline`.
- **macOS**: works on plain Claude Code. macOS + Orca is **untested** (whether
  Orca passes Claude Code's statusLine through).
- The number is the context size *at the start of the last turn* — lags by one.
