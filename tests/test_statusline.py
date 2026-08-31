"""contrib/statusline/ctx.py computes the context segment from a transcript."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

SL = Path(__file__).resolve().parent.parent / "contrib" / "statusline"
CTX = SL / "ctx.py"


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


def test_wrapper_runs_ctx_with_no_previous_command(tmp_path):
    d = tmp_path / "sl"
    d.mkdir()
    for f in ("wrapper.py", "ctx.py"):
        shutil.copy(SL / f, d / f)  # no statusline-prev.txt -> only ctx.py runs
    t = tmp_path / "t.jsonl"
    t.write_text(json.dumps({"message": {"usage": {"input_tokens": 100_000}}}), encoding="utf-8")
    r = subprocess.run(
        [sys.executable, str(d / "wrapper.py")],
        input=json.dumps({"model": {"id": "claude-sonnet-5"}, "transcript_path": str(t)}),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert r.returncode == 0, r.stderr
    assert "ctx 10%" in r.stdout  # 100k / 1m


def test_wrapper_survives_a_broken_previous_command(tmp_path):
    if not shutil.which("sh"):
        return  # the chain step needs sh; skip where it's absent
    d = tmp_path / "sl"
    d.mkdir()
    for f in ("wrapper.py", "ctx.py"):
        shutil.copy(SL / f, d / f)
    (d / "statusline-prev.txt").write_text("nonexistent-cmd-xyz; exit 3", encoding="utf-8")
    t = tmp_path / "t.jsonl"
    t.write_text(json.dumps({"message": {"usage": {"input_tokens": 100_000}}}), encoding="utf-8")
    r = subprocess.run(
        [sys.executable, str(d / "wrapper.py")],
        input=json.dumps({"model": {"id": "claude-sonnet-5"}, "transcript_path": str(t)}),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert r.returncode == 0
    assert "ctx 10%" in r.stdout  # ctx segment still emitted despite the broken prev
