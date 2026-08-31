"""contrib/statusline/ — the context segment + the wrapper that chains to a host."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

SL = Path(__file__).resolve().parent.parent / "contrib" / "statusline"
CTX = SL / "ctx.py"


def _wrapper_dir(tmp_path, prev: str | None = None):
    d = tmp_path / "sl"
    d.mkdir()
    for f in ("wrapper.py", "ctx.py"):
        shutil.copy(SL / f, d / f)
    if prev is not None:
        (d / "statusline-prev.txt").write_text(prev, encoding="utf-8")
    return d


def _run_wrapper(d: Path, payload: bytes) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(d / "wrapper.py")], input=payload, capture_output=True, timeout=30)


def _run(payload: dict) -> str:
    r = subprocess.run(
        [sys.executable, str(CTX)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert r.returncode == 0, r.stderr
    return r.stdout


def test_reads_last_usage_and_reports_percent(tmp_path):
    t = tmp_path / "t.jsonl"
    t.write_text(
        "\n".join(
            [
                json.dumps({"type": "assistant", "message": {"usage": {"input_tokens": 100}}}),
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {
                            "usage": {
                                "input_tokens": 5,
                                "cache_read_input_tokens": 449_995,
                                "cache_creation_input_tokens": 0,
                            }
                        },
                    }
                ),
                json.dumps({"type": "user", "message": {"content": "hi"}}),  # no usage — must skip back
            ]
        ),
        encoding="utf-8",
    )
    out = _run({"model": {"id": "claude-sonnet-5"}, "transcript_path": str(t)})
    assert "ctx 45%" in out  # 450k / 1m
    assert "450k/1m" in out


def test_haiku_window_is_200k(tmp_path):
    t = tmp_path / "t.jsonl"
    t.write_text(json.dumps({"message": {"usage": {"input_tokens": 100_000}}}), encoding="utf-8")
    out = _run({"model": {"id": "claude-haiku-4-5"}, "transcript_path": str(t)})
    assert "ctx 50%" in out and "200k" in out


def test_missing_transcript_prints_nothing():
    assert _run({"model": {"id": "claude-sonnet-5"}, "transcript_path": "/no/such/file"}) == ""


def test_bad_stdin_prints_nothing():
    r = subprocess.run([sys.executable, str(CTX)], input="not json", capture_output=True, text=True, timeout=30)
    assert r.returncode == 0
    assert r.stdout == ""


def _payload(tmp_path, tokens: int, extra: bytes = b"") -> bytes:
    t = tmp_path / "t.jsonl"
    t.write_text(json.dumps({"message": {"usage": {"input_tokens": tokens}}}), encoding="utf-8")
    obj = json.dumps({"model": {"id": "claude-sonnet-5"}, "transcript_path": str(t)}).encode("utf-8")
    return obj[:-1] + b', "x": "' + extra + b'"}' if extra else obj


def test_wrapper_runs_ctx_with_no_previous_command(tmp_path):
    d = _wrapper_dir(tmp_path)  # no statusline-prev.txt -> only ctx runs
    r = _run_wrapper(d, _payload(tmp_path, 100_000))
    assert r.returncode == 0, r.stderr
    assert b"ctx 10%" in r.stdout  # 100k / 1m


def test_wrapper_survives_a_broken_previous_command(tmp_path):
    if not shutil.which("sh"):
        return  # the chain step needs sh; skip where it's absent
    d = _wrapper_dir(tmp_path, prev="nonexistent-cmd-xyz; exit 3")
    r = _run_wrapper(d, _payload(tmp_path, 100_000))
    assert r.returncode == 0
    assert b"ctx 10%" in r.stdout  # ctx still emitted despite the broken prev


def test_wrapper_survives_a_non_utf8_payload(tmp_path):
    # regression: Claude Code's payload can carry non-UTF-8 bytes; a text-mode
    # round-trip re-encoded them with the Windows locale codec (cp950) and crashed
    # the wrapper before ctx ever ran → the segment vanished every render.
    d = _wrapper_dir(tmp_path, prev="cat >/dev/null" if shutil.which("sh") else None)
    r = _run_wrapper(d, _payload(tmp_path, 100_000, extra=b"\x89\xff\xfe"))
    assert r.returncode == 0, r.stderr
    assert b"ctx 10%" in r.stdout


def test_segment_never_raises_on_junk():
    sys.path.insert(0, str(SL))
    import ctx

    assert ctx.segment(b"\x89\xff not json") == ""
    assert ctx.segment("null") == ""
    assert ctx.segment(b'{"transcript_path": "/no/such"}') == ""
