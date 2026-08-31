"""Claude Code statusLine wrapper — installed by `setup.py statusline`.

Reads the statusLine JSON on stdin once, then:

1. runs whatever statusLine command was configured *before* this one (saved to
   `statusline-prev.txt` on install) so a host's own hook — e.g. Orca, which
   uses the slot as a data pipe — keeps working;
2. appends the context-usage segment produced by `ctx.py`.

Pure Python + stdlib. A plain Claude Code install has no previous command, so
no shell is involved at all. When there IS one, it is POSIX `sh` syntax and is
run through `sh` (or `bash`) — on Windows that is the Git Bash a host like Orca
already requires.
"""

import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _run(cmd: list[str], payload: str) -> None:
    """Run cmd, feeding it the payload, letting its output through. Never raises."""
    try:
        subprocess.run(cmd, input=payload, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        pass


def main() -> None:
    payload = sys.stdin.read()

    try:
        prev = (HERE / "statusline-prev.txt").read_text(encoding="utf-8").strip()
    except OSError:
        prev = ""
    if prev:
        shell = shutil.which("sh") or shutil.which("bash")
        if shell:
            _run([shell, "-c", prev], payload)

    _run([sys.executable, str(HERE / "ctx.py")], payload)


main()
