# Notion MCP

**Package:** [`@notionhq/notion-mcp-server`](https://github.com/makenotion/notion-mcp-server)
(official, MIT). Run locally via `npx`. Free.

## What it does

Search, read, create, and update Notion pages and databases; add comments.
Database **deletion is blocked** by design. Talks straight to `api.notion.com`
with your token — no middleman service.

"Local" = the MCP process and token live on your machine. Your Notion content
still lives in Notion's cloud (Notion is a cloud product); anything the MCP
creates or edits is written to your Notion workspace.

## One-time setup (manual)

1. **Create an integration**: https://www.notion.so/profile/integrations →
   *New integration* → *Internal*. Copy the secret (`ntn_...`).
   Set its capabilities to *Read content* only if you want it read-only.
2. **Set the token** (persistent env var — never committed, never written into
   harness config):
   - Windows: `setx NOTION_TOKEN "ntn_..."` (then open a new shell / restart the harness)
   - macOS/Linux: add `export NOTION_TOKEN="ntn_..."` to `~/.zprofile`
3. **Grant access to content**: on each Notion page or database you want it to
   touch → `•••` → *Connect to integration* → pick your integration.
   The integration only sees what you share.

## Wiring

`setup.py wire claude-code` / `wire codex` registers it. On Windows the MCP
command is `cmd /c npx -y @notionhq/notion-mcp-server` (npx needs the `cmd`
wrapper when spawned by a harness); elsewhere plain `npx`.

If `NOTION_TOKEN` isn't set at wire time, the server is still registered but
won't connect — `setup.py doctor` / `report` flag this. Set the token and
restart the harness.

## Requirements

Node.js (for `npx`). Nothing is installed permanently; `npx` fetches the package
on first run and caches it.

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
