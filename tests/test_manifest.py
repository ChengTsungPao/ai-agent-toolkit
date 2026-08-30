"""manifest.toml is the source of truth — check it stays well-formed."""

import tomllib
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
M = tomllib.loads((REPO / "manifest.toml").read_text(encoding="utf-8"))

KINDS = {"prerequisite", "cli", "mcp", "cli+mcp", "cli+skill"}
TOOLS = M["tool"]
SKILLS = M.get("skill", [])
PLUGINS = M.get("plugin", [])


def test_sections_present():
    assert M["schema_version"] == 2
    assert "guidelines" in M
    assert TOOLS, "at least one [[tool]]"


def test_guidelines_canonical_resolves():
    assert (REPO / M["guidelines"]["canonical"]).is_file()


@pytest.mark.parametrize("t", TOOLS, ids=[t.get("id", "?") for t in TOOLS])
def test_tool_wellformed(t):
    for key in ("id", "name", "kind", "purpose", "verify"):
        assert key in t, f"missing {key}"
    assert t["kind"] in KINDS, f"bad kind {t['kind']!r}"
    ins = t.get("install", {})
    assert ins, "no [tool.install]"
    assert "default" in ins or {"macos", "linux", "windows"} & ins.keys(), "no install command for any OS"


def test_tool_ids_unique():
    ids = [t["id"] for t in TOOLS]
    assert len(ids) == len(set(ids)), f"duplicate tool id: {ids}"


@pytest.mark.parametrize("t", [t for t in TOOLS if "mcp" in t], ids=[t["id"] for t in TOOLS if "mcp" in t])
def test_mcp_block_consistent(t):
    assert t["mcp"].get("command"), "[tool.mcp] has no command"
    assert "mcp" in t["kind"], f"has [tool.mcp] but kind={t['kind']!r}"
    for os_key in ("windows", "macos", "linux"):
        if os_key in t["mcp"]:
            assert t["mcp"][os_key].get("command"), f"[tool.mcp.{os_key}] has no command"


@pytest.mark.parametrize("s", SKILLS, ids=[s.get("id", "?") for s in SKILLS])
def test_skill_wellformed(s):
    assert s.get("id") and s.get("paths")
    assert str(s.get("repo", "")).startswith("https://"), "skill repo must be an https git URL"


@pytest.mark.parametrize("p", PLUGINS, ids=[p.get("id", "?") for p in PLUGINS])
def test_plugin_wellformed(p):
    assert p.get("id") and p.get("purpose")
    assert p.get("install"), "no [plugin.install]"


@pytest.mark.parametrize(
    "e",
    TOOLS + SKILLS + PLUGINS,
    ids=[e.get("id", "?") for e in TOOLS + SKILLS + PLUGINS],
)
def test_docs_path_exists(e):
    doc = e.get("docs", "")
    if doc and not doc.startswith("http"):
        assert (REPO / doc).is_file(), f"docs points at missing file: {doc}"
