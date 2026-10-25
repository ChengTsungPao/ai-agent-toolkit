"""Antigravity Remote Control: the `agy remote-control serve` daemon and its instance name.

Used by `setup.py wire antigravity`. The daemon is what lets https://antigravity.google.com reach this
machine; it stops when `agy` updates or the machine restarts, so `wire` can start it again.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from _common import IS_WINDOWS, WIN_FLAGS, dim, green


def is_daemon_running() -> bool:
    """Check if `agy remote-control serve` process is currently active."""
    if IS_WINDOWS:
        cmd = [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "(Get-CimInstance Win32_Process -Filter \"name like '%agy%'\") | "
            "Where-Object { $_.CommandLine -like '*remote-control serve*' } | "
            "Measure-Object | Select-Object -ExpandProperty Count",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return int(res.stdout.strip() or "0") > 0
    # macOS / Linux
    res = subprocess.run(["pgrep", "-f", "remote-control serve"], capture_output=True)
    return res.returncode == 0


def ensure_daemon_running() -> None:
    """Ensure `agy remote-control serve` is active in the background across platforms."""
    if "PYTEST_CURRENT_TEST" in os.environ:
        return
    try:
        if is_daemon_running():
            return
        agy_exe = shutil.which("agy")
        if not agy_exe:
            return

        if IS_WINDOWS:
            # On Windows, spawn via WMI to detach from current session/console job
            ps_script = (
                "$s = [wmiclass]'Win32_ProcessStartup'; "
                "$cfg = $s.CreateInstance(); "
                "$cfg.ShowWindow = 0; $cfg.CreateFlags = 0x210; "
                "$p = [wmiclass]'Win32_Process'; "
                f"$null = $p.Create('\"{agy_exe}\" remote-control serve', $null, $cfg)"
            )
            subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                capture_output=True,
                text=True,
                **WIN_FLAGS,
            )
        else:
            # On macOS / Linux, start_new_session=True (setsid) fully detaches process from controlling terminal
            subprocess.Popen(
                [agy_exe, "remote-control", "serve"],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
            )
    except Exception:
        pass


def wire_remote_control(home: Path) -> None:
    """Configure Antigravity Remote Control daemon with an instance name.

    Prompts the user during interactive setup to choose whether to enable Remote Control
    and which instance name to use. If declined, prints instructions on how to enable it later.
    """
    import json

    cfg_path = home / "config.json"
    cfg = {}
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8-sig").strip() or "{}")
        except ValueError:
            cfg = {}

    user_settings = cfg.setdefault("userSettings", {})
    existing = user_settings.get("remoteControlHostname") or user_settings.get("cliRemoteControlHostname")
    default_name = os.environ.get("AGY_INSTANCE_NAME") or existing or "Dev-Workstation"

    is_interactive = sys.stdin.isatty()
    enabled = True
    instance_name = default_name

    if is_interactive:
        ans = input("Enable Antigravity Remote Control (https://antigravity.google.com)? [Y/n] ").strip().lower()
        if ans in ("n", "no"):
            enabled = False
        else:
            name_ans = input(f"Instance name for Remote Control [{default_name}]: ").strip()
            if name_ans:
                instance_name = name_ans
    else:
        env_enable = os.environ.get("AGY_ENABLE_REMOTE_CONTROL", "").lower()
        if env_enable in ("0", "false", "no", "n"):
            enabled = False

    user_settings["remoteControlEnabled"] = enabled
    user_settings["remoteControlHostname"] = instance_name
    user_settings["cliRemoteControlHostname"] = instance_name

    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

    if not enabled:
        print(dim("  remote-control → skipped"))
        print(dim('    To enable anytime: agy remote-control start --name "<custom-name>"'))
        print(dim("    Then access sessions at: https://antigravity.google.com/"))
        return

    # Never mutate host agy configuration or processes when running under tests or with an isolated root
    if "PYTEST_CURRENT_TEST" in os.environ or home != Path.home() / ".gemini" / "config":
        if getattr(subprocess.run, "__module__", "") != "subprocess":
            subprocess.run(
                f'agy remote-control start --name "{instance_name}"',
                shell=True,
                capture_output=True,
                text=True,
            )
        return

    cmd = f'agy remote-control start --name "{instance_name}"'
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, **WIN_FLAGS)
    ensure_daemon_running()
    if r.returncode == 0:
        print(green(f"  remote-control → daemon started as '{instance_name}'"))
    else:
        print(dim(f"  remote-control → instance name '{instance_name}' configured"))
    print(dim("    manage & control sessions: https://antigravity.google.com/"))
    print(dim("    (change instance name anytime: agy remote-control start --name <custom-name>)"))
