# LinkedIn MCP

**Package:** [`mcp-server-linkedin`](https://pypi.org/project/mcp-server-linkedin/)
from [`stickerdaniel/linkedin-mcp-server`](https://github.com/stickerdaniel/linkedin-mcp-server)
(Apache-2.0). Installed as a `uv tool`, run locally. Free, no API keys.

**Community project — not affiliated with, authorized by, or endorsed by
LinkedIn.**

## Why it's here

There is no official LinkedIn API for this. Everything that reads arbitrary
public profiles / companies / jobs by URL does it by driving a logged-in
session. This one uses [Patchright](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python)
(a stealth Playwright fork) against a real browser profile, so it behaves like a
person browsing rather than hitting an undocumented API. It is the
best-maintained option (FastMCP-based, active releases) and keeps the session
and browser entirely on this machine.

## What it does

Read: `get_person_profile`, `get_my_profile`, `get_company_profile`,
`get_company_employees`, `get_company_posts`, `get_job_details`, `get_saved_jobs`,
`get_feed`, `get_inbox`, `get_conversation`; search: `search_people`,
`search_companies`, `search_jobs`, `search_posts`, `search_conversations`.

Write (acts on your account — use deliberately): `send_message`,
`connect_with_person`.

`close_session` releases the browser.

## ⚠️ Account risk

LinkedIn's [User Agreement](https://www.linkedin.com/legal/user-agreement)
prohibits automated access. Accounts using tools like this **can be restricted
or banned**, and the author gives no guarantee of account safety. Mitigations:

- Personal, **low volume** only. Tool calls run through a sequential queue, but
  you are responsible for how much automation you run — don't loop it over
  hundreds of profiles.
- Prefer read tools. Be explicit before any `send_message` / `connect_with_person`.
- Don't run it from a datacentre IP / VPN exit far from your normal location —
  that pattern trips LinkedIn's checks. A home connection is fine; see the
  upstream README's proxy section if you genuinely need one (most people don't).

## One-time setup (no secrets in config)

Auth is a browser login, not a token — nothing goes in
`~/.ai-dev-env/config.toml`. The session is stored under `~/.linkedin-mcp/`.

Pick one:

```bash
# A. sign in via a browser window this opens
mcp-server-linkedin --login

# B. reuse a browser you're already signed into LinkedIn on
mcp-server-linkedin --import-from-browser edge     # or chrome / brave / chromium / arc / vivaldi / auto
```

`--import-from-browser` is blocked by Chrome/Edge 127+ app-bound cookie
encryption (`v20`) — if it fails to decrypt, use `--login` instead.

Check / clear:

```bash
mcp-server-linkedin --status     # session state
mcp-server-linkedin --logout     # clear the stored session
```

Re-run `--login` when the session expires (tool calls start returning an
auth error).

If the first tool call in a harness returns "authentication in progress" /
"setup in progress", that's the browser warming up — retry in a few seconds.

## Wiring

`setup.py install` runs `uv tool install mcp-server-linkedin`. `setup.py wire
claude-code` / `wire codex` registers the `mcp-server-linkedin` binary as a
stdio MCP server — plain command, no `cmd /c` wrapper (a `uv tool` shim is a
real executable the harness can spawn directly, unlike an npm `.cmd`).

No per-OS override. Default transport is stdio; `args = []`.

## Requirements

- `uv` (already the repo's one prerequisite). Pulls its own Python 3.12.4+.
- A Chromium-family browser for the automation. Patchright downloads a matching
  Chromium on first run if none is found; point at an installed one with
  `--chrome-path` or `CHROME_PATH` if needed.

## Usage

Talk to the agent: "what's this person's background — <linkedin url>",
"summarise this job posting", "find product roles in Taipei posted this week",
"who at <company> works on infra". It calls the read/search tools above.

`UV_HTTP_TIMEOUT=300` (upstream's default in its Claude Desktop config) only
matters if you switch to `uvx mcp-server-linkedin@latest` (fetches the package
each run) — not needed with the `uv tool install` used here.
