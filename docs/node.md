# Node.js

**Site:** https://nodejs.org · **License:** MIT

## Why it's in the manifest

Two MCP servers in this environment are distributed only as npm packages and are
installed with `npm install -g`:

- **Notion MCP** (`@notionhq/notion-mcp-server`)
- **Chrome DevTools MCP** (`chrome-devtools-mcp`)

Node.js (which bundles `npm`) is therefore a prerequisite for those two — and
only those two. `uv` and everything installed as a `uv tool` do not need it.

## Why it is not auto-installed

`setup.py install` will **not** install Node. There is no single reliable
one-liner that works across macOS, Windows and Linux, and the choice between a
system package, the official installer, and a version manager (nvm / fnm /
volta) is personal. `report` and `doctor` flag it as missing so you know to
handle it; after installing, re-run `setup.py install`.

## How to install

| platform | command |
|---|---|
| macOS | `brew install node` |
| Windows | `winget install OpenJS.NodeJS.LTS` |
| Linux | distro package, or [nodesource](https://github.com/nodesource/distributions) |
| any (version manager) | [`nvm`](https://github.com/nvm-sh/nvm) · [`fnm`](https://github.com/Schniz/fnm) · [`volta`](https://volta.sh) |

Node **LTS** is enough. Verify with `node --version` and `npm --version`.

## Windows note

npm 11.16–11.17 has a bug where `npx -y <pkg>` crashes with
*"Cannot read properties of undefined (reading 'standard')"*. That is why the
npm-based MCP servers here are installed with `npm install -g` and wired as
`cmd /c <bin>` (see `[tool.mcp.windows]` in `manifest.toml`) rather than run via
`npx`.

## Removing the dependency

Skip `notion-mcp` and `chrome-devtools` (`setup.py choose`, or
`[skip].ids` in `~/.ai-dev-env/config.toml`) and nothing in this environment
needs Node at all.
