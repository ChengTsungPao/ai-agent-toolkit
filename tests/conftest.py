"""Keep every test away from the real home folder, the real harness configs and the shell's CODEX_HOME."""

import pytest


@pytest.fixture(autouse=True)
def isolated_home(tmp_path_factory, monkeypatch):
    home = tmp_path_factory.mktemp("home")
    for var in ("HOME", "USERPROFILE"):
        monkeypatch.setenv(var, str(home))
    for var in ("CODEX_HOME", "AGY_CONFIG_HOME"):
        monkeypatch.delenv(var, raising=False)
