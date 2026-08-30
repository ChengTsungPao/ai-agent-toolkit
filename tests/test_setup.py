"""setup.py loads, its helpers behave, and `report` runs anywhere."""

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SETUP = REPO / "scripts" / "setup.py"


def load():
    spec = importlib.util.spec_from_file_location("setup_mod", SETUP)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_imports():
    load()


def test_wirers_are_the_supported_harnesses():
    assert set(load().WIRERS) == {"claude-code", "codex", "cursor", "generic"}


def test_repo_display_is_under_this_repo():
    m = load()
    d = m.repo_display()
    assert isinstance(d, str) and d
    assert d.rstrip("/").endswith("ai-dev-env")


def test_env_repo_pointer_is_current():
    ptr = load().env_repo_pointer()
    assert "## Environment repo" in ptr
    assert "docs/tools" not in ptr, "stale path — docs/ was flattened"
    assert "gemini" not in ptr.lower(), "gemini-cli was dropped as a wire target"


def test_kind_enum_matches_manifest_test():
    # keep the two lists of valid kinds from drifting apart
    from test_manifest import KINDS

    # every kind used in the manifest must be one setup.py could reason about
    m = load()
    for t in m.load_tools():
        assert t["kind"] in KINDS


def _run_report(tmp_path, extra_env=None):
    env = {**os.environ, "NO_COLOR": "1", "AI_DEV_ENV_HOME": str(tmp_path), **(extra_env or {})}
    return subprocess.run(
        [sys.executable, str(SETUP), "report"],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=120,
    )


def test_report_runs_with_no_tools_installed(tmp_path):
    r = _run_report(tmp_path)
    assert r.returncode == 0, r.stderr
    assert "MCP servers" in r.stdout
    assert "CLI tools" in r.stdout


def test_report_survives_a_non_utf8_stdout(tmp_path):
    # box-drawing / bullet glyphs must not crash on a cp1252 pipe (Windows CI, redirects)
    r = _run_report(tmp_path, {"PYTHONIOENCODING": "cp1252"})
    assert r.returncode == 0, r.stderr


def test_config_template_generates(tmp_path):
    env = {**os.environ, "NO_COLOR": "1", "AI_DEV_ENV_HOME": str(tmp_path)}
    r = subprocess.run(
        [sys.executable, str(SETUP), "config"],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )
    assert r.returncode == 0, r.stderr
    cfg = tmp_path / "config.toml"
    assert cfg.is_file()
    assert "[env]" in cfg.read_text(encoding="utf-8")
