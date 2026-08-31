"""contrib/statusline/ctx.py computes the context segment from a transcript."""

import json
import subprocess
import sys
from pathlib import Path

CTX = Path(__file__).resolve().parent.parent / "contrib" / "statusline" / "ctx.py"


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
