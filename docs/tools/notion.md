# Notion MCP

**Package:** [`@notionhq/notion-mcp-server`](https://github.com/makenotion/notion-mcp-server)
(official, MIT). Installed globally via npm, run locally. Free.

## What it does

Search, read, create, and update Notion pages and databases; add comments.
Database **deletion is blocked** by design. Talks straight to `api.notion.com`
with your token — no middleman service.

"Local" = the MCP process and token live on your machine. Your Notion content
still lives in Notion's cloud (Notion is a cloud product); anything the MCP
creates or edits is written to your Notion workspace.

## One-time setup

1. **Create an integration**: https://www.notion.so/profile/integrations →
   *New integration* → *Internal*. Copy the secret (`ntn_...`).
   Set its capabilities to *Read content* only if you want it read-only.
2. **Put the token in your local config** — `~/.ai-dev-env/config.toml`
   (`setup.py config` creates it; it lives outside the repo clone and is never
   committed):
   ```toml
   [env]
   NOTION_TOKEN = "ntn_..."
   ```
   Then `setup.py wire <harness>` again so the value reaches the MCP server.
3. **Grant access to content**: on each Notion page or database you want it to
   touch → `•••` → *Connect to integration* → pick your integration.
   The integration only sees what you share.

## Wiring

`setup.py install` runs `npm install -g @notionhq/notion-mcp-server`.
`setup.py wire claude-code` / `wire codex` then registers the `notion-mcp-server`
binary as an MCP server. On Windows the command is `cmd /c notion-mcp-server`
(the harness can't reliably resolve the npm `.cmd`/`.ps1` shim on its own);
elsewhere plain `notion-mcp-server`.

If `NOTION_TOKEN` is blank in `config.toml` at wire time, the server is still
registered but idle — `setup.py doctor` / `report` flag it. Fill it in, re-run
`wire`, restart the harness. (An exported `NOTION_TOKEN` env var also works and
takes second priority after the config file.)

## Requirements

Node.js + npm. (`npx -y @notionhq/notion-mcp-server` also works in principle but
npm 11.16–11.17 has an `npx` regression on Windows — `Cannot read properties of
undefined (reading 'standard')` — so a global install is used instead.)

On macOS, `npm install -g` needs a user-writable global prefix — fine with
Homebrew node, nvm, fnm, or volta; a raw `/usr/local` system node may need
`sudo` or `npm config set prefix ~/.npm-global`.

## Usage

Talk to the agent ("add this to my Notion tasks", "what's in my reading list?")
or use the **`notion` skill** (`skills/notion/SKILL.md`) — fill its workspace
map with your real database IDs so routing doesn't need to be re-explained.

Key tools: `notion-search`, `notion-fetch`, `notion-create-pages`,
`notion-update-page`, `notion-create-comment`.

## Notes

Notion is steering people toward its hosted remote MCP (`https://mcp.notion.com/mcp`,
OAuth) and gives this local package lower-priority support — it may be sunset
eventually. Switch by replacing the `[tool.mcp]` block with an HTTP transport
entry if that happens.
