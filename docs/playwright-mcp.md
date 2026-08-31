# Playwright MCP

**Package:** [`@playwright/mcp`](https://github.com/microsoft/playwright-mcp)
(Microsoft, Apache-2.0). Installed globally via npm, run locally. Free, no token.

## What it does

Drives a browser from the agent, working off the page's **accessibility tree**
(not pixel-guessing): navigate, click, type, fill whole forms, hover, drag,
press keys, wait for elements, upload files, handle dialogs, screenshot, read
console + network, and **generate Playwright test code** for what it just did.
Chromium / Firefox / WebKit / MS Edge.

## Why it's here alongside Chrome DevTools MCP

Both automate a browser; kept side by side (like graphify / codegraph) because
they optimise for different jobs:

| | Playwright MCP | Chrome DevTools MCP |
|---|---|---|
| built for | **repeatable automation**, cross-browser tests | **debugging a live Chrome** — why is it slow / broken |
| browser | fresh isolated context (or `--cdp-endpoint` to attach) | attaches to **your running Chrome** (your logins, profile) |
| engines | Chromium / Firefox / WebKit / Edge | Chrome only |
| strengths | auto-waiting, robust locators, `--codegen`, device emulation | performance traces, Lighthouse, heap snapshots, DevTools-grade network panel |
| weak at | perf profiling, Lighthouse, heap | cross-browser, durable scripts |

Rule of thumb: **writing tests / CI / cross-browser → Playwright MCP.**
**"look at my running app and tell me why X" → Chrome DevTools MCP.**

## Setup

`setup.py install playwright-mcp` runs `npm install -g @playwright/mcp` (pulls
`playwright-core`). `setup.py wire <harness>` registers the `playwright-mcp`
binary as an MCP server. On Windows the command goes through `cmd /c` because
the npm global bin is a `.cmd` shim the harness can't spawn directly.

### Browsers

The manifest wires it with **`--browser chrome`**, which uses the system Chrome
channel — no ~150 MB Playwright browser download, and this machine already has
Chrome (Chrome DevTools MCP uses it too).

For Firefox / WebKit, or a pinned Chromium build:

```bash
npx playwright install chromium firefox webkit
```

then change the MCP args (`claude mcp remove playwright-mcp -s user` and re-add,
or edit `~/.claude.json`) to `--browser firefox` etc.

## Useful flags

| flag | effect |
|---|---|
| `--browser <chrome\|firefox\|webkit\|msedge>` | engine / channel |
| `--headless` | no visible window (default is headed) |
| `--device "iPhone 15"` / `--mobile` | device emulation |
| `--isolated` | ephemeral profile, wiped on exit |
| `--caps vision,pdf,devtools` | extra tool groups (coordinate-based clicks, PDF, a DevTools subset) |
| `--codegen <typescript\|python\|java\|csharp>` | language for generated test code |
| `--cdp-endpoint <url>` | attach to an already-running browser over CDP |

## Requirements

Node.js + npm. (`npx @playwright/mcp@latest` also works in principle, but npm
11.16–11.17 has an `npx` regression on Windows — `Cannot read properties of
undefined (reading 'standard')` — so a global install is used instead, same as
the other npm-based MCP servers here.)

## Usage

Talk to the agent: "open example.com and screenshot it", "fill the login form
and submit, then tell me any console errors", "navigate the checkout flow and
generate a Playwright test for it". It picks elements by their accessible name
/ role from the snapshot, so instructions can be in plain language.
