"""setup.py loads, its helpers behave, and `report` runs anywhere."""

import argparse
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
SETUP = SCRIPTS / "setup.py"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load():
    # reload the kernel first so a test's monkeypatched AI_DEV_ENV_HOME reaches
    # the CONFIG path constant (evaluated at _common import time)
    for name in ("_common", "_statusline"):
        if name in sys.modules:
            importlib.reload(sys.modules[name])
    spec = importlib.util.spec_from_file_location("setup_mod", SETUP)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def load_statusline():
    import _statusline

    return _statusline


def test_imports():
    load()


def test_wirers_are_the_supported_harnesses():
    assert set(load().WIRERS) == {"claude-code", "codex", "antigravity", "cursor", "generic"}


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
    assert m.upgrade_cmd(by_id["codegraph"]) is None  # web installer — never auto-run (see upgrade_cmd docstring)


def test_wire_targets_have_a_harness_doc():
    m = load()
    for h in m.WIRERS:
        name = "generic-mcp" if h == "generic" else h
        assert (REPO / "harnesses" / f"{name}.md").is_file(), h


def test_schema_version_matches_manifest():
    m = load()
    assert m.load_manifest()["schema_version"] == m.SCHEMA_VERSION


def test_statusline_command_needs_no_bash():
    cmd = load_statusline()._statusline_command()
    assert "wrapper.py" in cmd
    assert "bash" not in cmd and ".sh" not in cmd
    # must NOT start with a quote — cmd.exe /c strips a matched outer pair and a
    # leading "C:\...exe" then becomes unbalanced (statusLine silently fails)
    assert not cmd.startswith('"')


def test_common_kernel_importable_and_shared():
    import _common

    assert _common.REPO == REPO
    assert callable(_common.run) and callable(_common.green)
    assert load().run is _common.run  # setup.py re-exports the kernel's helpers


def test_bootstrap_runs_install_then_wire_per_detected_harness(monkeypatch):
    m = load()
    calls = []
    monkeypatch.setattr(m, "_first_run_gate", lambda: None)
    monkeypatch.setattr(m, "_install", lambda ids, mode: calls.append(("install", tuple(ids), mode)) or 0)
    monkeypatch.setattr(m, "_wire", lambda h: calls.append(("wire", h)) or 0)
    monkeypatch.setattr(m, "_detected_harnesses", lambda: ["claude-code", "codex"])
    monkeypatch.setattr(m, "all_required_env", dict)
    m.cmd_bootstrap(argparse.Namespace(mode="all", keep_going=False))
    assert calls == [("install", (), "all"), ("wire", "claude-code"), ("wire", "codex")]


def test_bootstrap_stops_before_wiring_when_install_fails(monkeypatch):
    m = load()
    wired = []
    monkeypatch.setattr(m, "_first_run_gate", lambda: None)
    monkeypatch.setattr(m, "_install", lambda ids, mode: 1)
    monkeypatch.setattr(m, "_wire", lambda h: wired.append(h))
    monkeypatch.setattr(m, "_detected_harnesses", lambda: ["claude-code"])
    rc = m.cmd_bootstrap(argparse.Namespace(mode="all", keep_going=False))
    assert rc == 1 and wired == []


# ── upgrade / unwire orchestration ─────────────────────────────────────────
def test_upgrade_runs_the_upgrade_command_for_each_installed_tool(monkeypatch):
    m = load()
    monkeypatch.setattr(
        m,
        "load_tools",
        lambda: [
            {"id": "uv", "name": "uv"},
            {"id": "np", "name": "Np", "install": {"default": "npm install -g np"}},
            {"id": "gone", "name": "Gone"},
        ],
    )
    monkeypatch.setattr(m, "skipped_ids", set)
    monkeypatch.setattr(m, "is_installed", lambda t: t["id"] != "gone")
    monkeypatch.setattr(m, "version_of", lambda t: "1.0")
    monkeypatch.setattr(m, "ext_skills", list)
    monkeypatch.setattr(m, "bundled_skills", list)
    ran = []
    monkeypatch.setattr(m, "run", lambda cmd, **kw: ran.append(cmd) or 0)
    rc = m.cmd_upgrade(argparse.Namespace(tools=[]))
    assert rc == 0
    assert ran == ["uv self update", "npm install -g np"]  # 'gone' not installed → not touched


def test_upgrade_refreshes_graphify_skill_only_when_its_version_changed(monkeypatch):
    m = load()
    monkeypatch.setattr(
        m,
        "load_tools",
        lambda: [{"id": "graphify", "name": "graphify", "install": {"default": "uv tool install graphifyy"}}],
    )
    monkeypatch.setattr(m, "skipped_ids", set)
    monkeypatch.setattr(m, "is_installed", lambda t: True)
    monkeypatch.setattr(m, "run", lambda cmd, **kw: 0)
    monkeypatch.setattr(m, "ext_skills", list)
    monkeypatch.setattr(m, "bundled_skills", list)
    monkeypatch.setattr(m, "_detected_harnesses", lambda: ["claude-code"])
    refreshed = []
    monkeypatch.setattr(m, "_install_graphify_skill", lambda h: refreshed.append(h))

    monkeypatch.setattr(m, "version_of", lambda t: "0.9.51")  # before == after
    m.cmd_upgrade(argparse.Namespace(tools=["graphify"]))
    assert refreshed == []

    versions = iter(["0.9.51", "0.9.53"])
    monkeypatch.setattr(m, "version_of", lambda t: next(versions))
    m.cmd_upgrade(argparse.Namespace(tools=["graphify"]))
    assert refreshed == ["claude-code"]


def test_upgrade_skips_no_path_tools_and_reports_failure(monkeypatch):
    m = load()
    monkeypatch.setattr(m, "load_tools", lambda: [{"id": "no", "name": "NoPath"}, {"id": "uv", "name": "uv"}])
    monkeypatch.setattr(m, "skipped_ids", set)
    monkeypatch.setattr(m, "is_installed", lambda t: True)
    monkeypatch.setattr(m, "version_of", lambda t: "x")
    monkeypatch.setattr(m, "ext_skills", list)
    monkeypatch.setattr(m, "bundled_skills", list)
    ran = []
    monkeypatch.setattr(m, "run", lambda cmd, **kw: ran.append(cmd) or 1)  # every upgrade "fails"
    rc = m.cmd_upgrade(argparse.Namespace(tools=["no", "uv"]))
    assert ran == ["uv self update"]  # 'no' has no upgrade path → skipped, not run
    assert rc == 1  # uv's non-zero return propagates


def test_upgrade_refreshes_skills_only_without_explicit_ids(monkeypatch):
    m = load()
    monkeypatch.setattr(m, "load_tools", list)
    monkeypatch.setattr(m, "skipped_ids", set)
    monkeypatch.setattr(m, "ext_skills", lambda: [{"id": "grill", "repo": "https://x/y", "paths": ["p"]}])
    monkeypatch.setattr(m, "bundled_skills", list)
    monkeypatch.setattr(m.shutil, "which", lambda _name: "/usr/bin/x")  # both harness CLIs "present"
    refreshed = []
    monkeypatch.setattr(m, "_install_skills", lambda d: refreshed.append(d))
    m.cmd_upgrade(argparse.Namespace(tools=[]))
    assert len(refreshed) == 3  # ~/.claude/skills + $CODEX_HOME/skills + <agy>/skills
    refreshed.clear()
    m.cmd_upgrade(argparse.Namespace(tools=["grill"]))
    assert refreshed == []  # explicit ids → no skills refresh


def _unwire_recorders(monkeypatch, m):
    ran, stripped, removed = [], [], []
    monkeypatch.setattr(
        m,
        "load_tools",
        lambda: [{"id": "aa", "mcp": {"command": "x"}}, {"id": "bb", "mcp": {"command": "y"}}, {"id": "cc"}],
    )
    monkeypatch.setattr(m, "bundled_skills", list)
    monkeypatch.setattr(m, "ext_skills", list)
    monkeypatch.setattr(m.subprocess, "run", lambda cmd, **kw: ran.append(cmd))
    monkeypatch.setattr(m, "_strip_block", lambda p: stripped.append(p.name) or True)
    monkeypatch.setattr(m.shutil, "rmtree", lambda p, **kw: removed.append(p))
    return ran, stripped, removed


def test_unwire_claude_code_removes_mcp_then_guidelines(monkeypatch):
    m = load()
    ran, stripped, _ = _unwire_recorders(monkeypatch, m)
    rc = m.cmd_unwire(argparse.Namespace(harness="claude-code"))
    assert rc == 0
    assert ran == ["claude mcp remove aa -s user", "claude mcp remove bb -s user"]  # 'cc' has no mcp
    assert stripped == ["AGENTS.md", "CLAUDE.md"]


def test_unwire_codex_uses_codex_remove_and_spares_claude_md(monkeypatch):
    m = load()
    ran, stripped, _ = _unwire_recorders(monkeypatch, m)
    rc = m.cmd_unwire(argparse.Namespace(harness="codex"))
    assert rc == 0
    assert ran == ["codex mcp remove aa", "codex mcp remove bb"]
    assert stripped == ["AGENTS.md"]  # codex has no CLAUDE.md


def test_unwire_cursor_touches_nothing(monkeypatch):
    m = load()
    ran, stripped, removed = _unwire_recorders(monkeypatch, m)
    rc = m.cmd_unwire(argparse.Namespace(harness="cursor"))
    assert rc == 0 and ran == [] and stripped == [] and removed == []


def test_unwire_unknown_harness_returns_2():
    assert load().cmd_unwire(argparse.Namespace(harness="bogus")) == 2


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


def test_wire_antigravity_merges_mcp_and_keeps_foreign_servers(monkeypatch, tmp_path):
    import json

    m = load()
    monkeypatch.setenv("AGY_CONFIG_HOME", str(tmp_path))
    (tmp_path / "mcp_config.json").write_text(json.dumps({"mcpServers": {"mine": {"command": "keep"}}}))
    monkeypatch.setattr(m.shutil, "which", lambda name: f"/bin/{name}")
    monkeypatch.setattr(m, "_install_skills", lambda d: None)
    monkeypatch.setattr(m, "_install_graphify_skill", lambda h: None)
    monkeypatch.setattr(m, "skipped_ids", set)
    monkeypatch.setattr(m, "resolved_env", lambda keys: {})
    tools = [{"id": "aa", "mcp": {"command": "x", "args": ["1"]}, "env": {"K": "v"}}]
    assert m.wire_antigravity(tools) == 0
    servers = json.loads((tmp_path / "mcp_config.json").read_text())["mcpServers"]
    assert servers["mine"] == {"command": "keep"}
    assert servers["aa"] == {"command": "/bin/x", "args": ["1"], "env": {"K": "v"}}


def test_wire_antigravity_tolerates_empty_mcp_file(monkeypatch, tmp_path):
    import json

    m = load()
    monkeypatch.setenv("AGY_CONFIG_HOME", str(tmp_path))
    (tmp_path / "mcp_config.json").write_text("")
    monkeypatch.setattr(m.shutil, "which", lambda name: f"/bin/{name}")
    monkeypatch.setattr(m, "_install_skills", lambda d: None)
    monkeypatch.setattr(m, "_install_graphify_skill", lambda h: None)
    monkeypatch.setattr(m, "skipped_ids", set)
    assert m.wire_antigravity([]) == 0
    assert json.loads((tmp_path / "mcp_config.json").read_text()) == {"mcpServers": {}}


def test_unwire_antigravity_removes_only_managed_servers(monkeypatch, tmp_path):
    import json

    m = load()
    ran, stripped, _ = _unwire_recorders(monkeypatch, m)
    monkeypatch.setenv("AGY_CONFIG_HOME", str(tmp_path))
    (tmp_path / "mcp_config.json").write_text(json.dumps({"mcpServers": {"aa": {}, "mine": {}}}))
    assert m.cmd_unwire(argparse.Namespace(harness="antigravity")) == 0
    assert list(json.loads((tmp_path / "mcp_config.json").read_text())["mcpServers"]) == ["mine"]
    assert stripped == ["AGENTS.md"] and ran == []


def test_wire_antigravity_configures_remote_control_default(monkeypatch, tmp_path):
    import json

    m = load()
    monkeypatch.setenv("AGY_CONFIG_HOME", str(tmp_path))
    monkeypatch.delenv("AGY_INSTANCE_NAME", raising=False)
    monkeypatch.setattr(m.shutil, "which", lambda name: f"/bin/{name}")
    monkeypatch.setattr(m, "_install_skills", lambda d: None)
    monkeypatch.setattr(m, "_install_graphify_skill", lambda h: None)
    monkeypatch.setattr(m, "skipped_ids", set)
    monkeypatch.setattr(m.subprocess, "run", lambda *a, **kw: type("R", (), {"returncode": 0})())

    assert m.wire_antigravity([]) == 0
    cfg = json.loads((tmp_path / "config.json").read_text())
    assert cfg["userSettings"]["remoteControlEnabled"] is True
    assert cfg["userSettings"]["remoteControlHostname"] == "Dev-Workstation"
    assert cfg["userSettings"]["cliRemoteControlHostname"] == "Dev-Workstation"


def test_wire_antigravity_preserves_existing_remote_control_name(monkeypatch, tmp_path):
    import json

    m = load()
    monkeypatch.setenv("AGY_CONFIG_HOME", str(tmp_path))
    monkeypatch.delenv("AGY_INSTANCE_NAME", raising=False)
    existing = {"userSettings": {"remoteControlHostname": "My-Custom-PC"}}
    (tmp_path / "config.json").write_text(json.dumps(existing))
    monkeypatch.setattr(m.shutil, "which", lambda name: f"/bin/{name}")
    monkeypatch.setattr(m, "_install_skills", lambda d: None)
    monkeypatch.setattr(m, "_install_graphify_skill", lambda h: None)
    monkeypatch.setattr(m, "skipped_ids", set)
    monkeypatch.setattr(m.subprocess, "run", lambda *a, **kw: type("R", (), {"returncode": 0})())

    assert m.wire_antigravity([]) == 0
    cfg = json.loads((tmp_path / "config.json").read_text())
    assert cfg["userSettings"]["remoteControlHostname"] == "My-Custom-PC"
    assert cfg["userSettings"]["cliRemoteControlHostname"] == "My-Custom-PC"


def test_wire_antigravity_honours_agy_instance_name_env(monkeypatch, tmp_path):
    import json

    m = load()
    monkeypatch.setenv("AGY_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("AGY_INSTANCE_NAME", "Office-Rig")
    monkeypatch.setattr(m.shutil, "which", lambda name: f"/bin/{name}")
    monkeypatch.setattr(m, "_install_skills", lambda d: None)
    monkeypatch.setattr(m, "_install_graphify_skill", lambda h: None)
    monkeypatch.setattr(m, "skipped_ids", set)
    monkeypatch.setattr(m.subprocess, "run", lambda *a, **kw: type("R", (), {"returncode": 0})())

    assert m.wire_antigravity([]) == 0
    cfg = json.loads((tmp_path / "config.json").read_text())
    assert cfg["userSettings"]["remoteControlHostname"] == "Office-Rig"
    assert cfg["userSettings"]["cliRemoteControlHostname"] == "Office-Rig"
