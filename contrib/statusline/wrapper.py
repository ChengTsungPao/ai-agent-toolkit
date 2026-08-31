"""Claude Code statusLine wrapper — installed by `setup.py statusline`.

1. runs whatever statusLine command was configured *before* this one (saved to
   `statusline-prev.txt` on install) so a host's own hook — e.g. Orca, which
   uses the slot as a data pipe — keeps working;
2. appends the context-usage segment from `ctx.py`.

The payload is read and forwarded as **bytes**. Claude Code's statusLine JSON
can carry non-UTF-8 sequences (a path, a prompt snippet); a text-mode round-trip
would re-encode them with the Windows locale codec (cp950, …) and crash, which
is exactly what killed the first version of this script. `sh` / `bash` is used
only to run the previous command — a plain Claude Code install has none.
"""

import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ctx  # noqa: E402


def main() -> None:
    payload = sys.stdin.buffer.read()  # bytes — never decode / re-encode

    try:
        prev = (HERE / "statusline-prev.txt").read_text(encoding="utf-8").strip()
    except OSError:
        prev = ""
    if prev:
        shell = shutil.which("sh") or shutil.which("bash")
        if shell:
            try:
                subprocess.run([shell, "-c", prev], input=payload, timeout=10)
            except (OSError, subprocess.SubprocessError):
                pass

    try:
        sys.stdout.buffer.write(ctx.segment(payload).encode("utf-8"))
        sys.stdout.buffer.flush()
    except Exception:
        pass


main()
