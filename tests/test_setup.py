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


def _run(tmp_path, *cmd, extra_env=None):
    env = {**os.environ, "NO_COLOR": "1", "AI_DEV_ENV_HOME": str(tmp_path), **(extra_env or {})}
    return subprocess.run(
        [sys.executable, str(SETUP), *cmd],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=120,
    )


def test_report_runs_with_no_tools_installed(tmp_path):
    r = _run(tmp_path, "report")
    assert r.returncode == 0, r.stderr
    assert "MCP servers" in r.stdout
    assert "CLI tools" in r.stdout


def test_report_survives_a_non_utf8_stdout(tmp_path):
    # box-drawing / bullet glyphs must not crash on a cp1252 pipe (Windows CI, redirects)
    r = _run(tmp_path, "report", extra_env={"PYTHONIOENCODING": "cp1252"})
    assert r.returncode == 0, r.stderr


def test_config_template_generates(tmp_path):
    r = _run(tmp_path, "config")
    assert r.returncode == 0, r.stderr
    cfg = tmp_path / "config.toml"
    assert cfg.is_file()
    body = cfg.read_text(encoding="utf-8")
    assert "[env]" in body
    assert "[skip]" in body


def test_mcp_spec_applies_windows_override(monkeypatch):
    m = load()
    notion = next(t for t in m.load_tools() if t["id"] == "notion-mcp")
    monkeypatch.setattr(m, "OS", "windows")
    assert m.mcp_spec(notion) == ("cmd", ["/c", "notion-mcp-server"])
    monkeypatch.setattr(m, "OS", "macos")
    assert m.mcp_spec(notion)[0] == "notion-mcp-server"


def test_install_cmd_resolves_per_os(monkeypatch):
    m = load()
    uv = next(t for t in m.load_tools() if t["id"] == "uv")
    monkeypatch.setattr(m, "OS", "windows")
    assert "irm" in m.install_cmd(uv)
    monkeypatch.setattr(m, "OS", "macos")
    assert "astral.sh/uv/install.sh" in m.install_cmd(uv)


def test_upgrade_cmd_inference():
    m = load()
    by_id = {t["id"]: t for t in m.load_tools()}
    assert m.upgrade_cmd(by_id["uv"]) == "uv self update"
    assert m.upgrade_cmd(by_id["graphify"]) == "uv tool upgrade graphifyy"
    assert m.upgrade_cmd(by_id["notion-mcp"]) == "npm install -g @notionhq/notion-mcp-server"
    assert m.upgrade_cmd(by_id["node"]) is None  # nothing to upgrade — install-yourself


def test_wire_targets_have_a_harness_doc():
    m = load()
    for h in m.WIRERS:
        name = "generic-mcp" if h == "generic" else h
        assert (REPO / "harnesses" / f"{name}.md").is_file(), h


def test_schema_version_matches_manifest():
    m = load()
    assert m.load_manifest()["schema_version"] == m.SCHEMA_VERSION


def test_statusline_command_needs_no_bash(monkeypatch):
    m = load()
    cmd = m._statusline_command()
    assert "wrapper.py" in cmd
    assert "bash" not in cmd and ".sh" not in cmd


def test_strip_block_removes_only_the_marked_region(tmp_path):
    m = load()
    f = tmp_path / "CLAUDE.md"
    f.write_text(f"# mine\n\nkeep this\n\n{m.GUIDE_BEGIN}\ngenerated\n{m.GUIDE_END}\n", encoding="utf-8")
    assert m._strip_block(f) is True
    body = f.read_text(encoding="utf-8")
    assert "keep this" in body and "generated" not in body and m.GUIDE_BEGIN not in body
    assert m._strip_block(f) is False  # idempotent — nothing left to strip


def test_config_body_preserves_unmanaged_env_keys(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_DEV_ENV_HOME", str(tmp_path))
    m = load()
    (tmp_path / "config.toml").write_text(
        '[env]\nMY_OWN_KEY = "hi"\n\n[skip]\nids = []\n\n[my_table]\nx = 1\n', encoding="utf-8"
    )
    body = m._config_body()
    assert 'MY_OWN_KEY = "hi"' in body
    assert "[my_table]" in body and "x = 1" in body
    import tomllib

    tomllib.loads(body)  # still valid TOML


def test_skip_list_is_honoured(tmp_path, monkeypatch):
    (tmp_path / "config.toml").write_text('[env]\n\n[skip]\nids = ["chrome-devtools"]\n', encoding="utf-8")

    # subprocess (read-only): report marks the skipped item
    rep = _run(tmp_path, "report")
    assert "skipped (config [skip]): chrome-devtools" in rep.stdout
    assert "⊘ skipped" in rep.stdout

    # in-process: the filters exclude it (no real installs triggered)
    monkeypatch.setenv("AI_DEV_ENV_HOME", str(tmp_path))
    m = load()
    assert "chrome-devtools" in m.skipped_ids()
    assert all(t["id"] != "chrome-devtools" for t in m._mcp_tools(m.load_tools()))
    ids = [t["id"] for t in m.load_tools()]
    wanted = set(ids) - m.skipped_ids()
    assert "chrome-devtools" not in wanted
