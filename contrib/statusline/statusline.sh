#!/usr/bin/env bash
# Claude Code statusLine — prints whatever the previous statusLine printed, then
# appends a context-usage segment. Installed by `setup.py statusline`.
#
# `setup.py statusline` copies this + ctx.py into ~/.claude/ and saves the
# statusLine command that was there before into ~/.claude/statusline-prev.txt
# (empty file if there was none). That keeps a host's own statusLine hook
# working — e.g. Orca, which uses the slot as a data pipe.
#
# POSIX-ish: works on macOS's bash 3.2. No bash-4 features.

payload="$(cat)"
d="$(cd "$(dirname "$0")" && pwd)"

# 1. run the previous statusLine command (if any) and pass its output through
prev="$d/statusline-prev.txt"
if [ -s "$prev" ]; then
  printf '%s' "$payload" | sh -c "$(cat "$prev")" 2>/dev/null
fi

# 2. context segment — find a real Python, then run ctx.py
py=""
for c in python3 python; do
  if "$c" --version 2>&1 | grep -q '^Python [0-9]'; then py="$c"; break; fi
done
if [ -z "$py" ] && command -v uv >/dev/null 2>&1; then py="uv run --python 3.12 python"; fi
[ -n "$py" ] && printf '%s' "$payload" | $py "$d/ctx.py" 2>/dev/null
