---
name: notion
description: Operate the user's Notion workspace — capture notes, tasks, and links into the right place, and read/update existing pages. Use whenever the user says "put this in Notion", "add to my Notion", "save to Notion", "check my Notion", or names one of their Notion databases below.
---

# notion

Runs on the **notion-mcp** server (`@notionhq/notion-mcp-server`, local). If the
Notion tools aren't available, tell the user to set `NOTION_TOKEN` and restart
the harness — do not fall back to guessing.

## Workspace map

> Fill this in with your real Notion databases and pages. The agent uses it to
> route content without asking every time. Get a database ID from its URL:
> `notion.so/<workspace>/<DB_ID>?v=...`.

| purpose | database / page | ID | notes |
|---|---|---|---|
| Tasks / todos | _e.g. Tasks_ | `TODO` | properties: Status (select), Due (date), Priority |
| Notes / knowledge | _e.g. Notes_ | `TODO` | one page per topic |
| Meeting notes | _e.g. Meetings_ | `TODO` | title = `YYYY-MM-DD <topic>` |
| Reading / links | _e.g. Reading List_ | `TODO` | property: URL, Tags |

If a request doesn't match anything here, ask which database/page before writing.

## Conventions

- **Confirm before creating**: restate what will be written and where, then act.
- **Never delete.** Archive or set a status instead. (The MCP blocks DB deletion
  anyway.)
- Prefer `notion-update-page` on an existing page over making duplicates —
  search first (`notion-search`) to check.
- Dates in ISO `YYYY-MM-DD`. Match each database's existing property names and
  select-option spelling exactly; if unsure, fetch the DB schema first.
- Keep page bodies as clean Markdown; let Notion render it.

## Common tasks

- **Capture a task**: search the Tasks DB for a near-duplicate; if none, create a
  page with Status = the DB's "not started" option and Due if the user gave one.
- **Save a note**: new page in the Notes DB, title = a short noun phrase, body =
  the content; add Tags if the DB has them.
- **Log a meeting**: new page in Meetings, title `YYYY-MM-DD <topic>`, sections
  for Attendees / Decisions / Actions.
- **Save a link**: new row in Reading List with URL set; pull the page title if
  the user didn't give one.

## Relation to Basic Memory

Basic Memory (`~/basic-memory`) is the private, local, always-available memory.
Notion is for things that belong in the user's shared/structured workspace
(tasks others see, project pages, reading list). When unsure which, ask.
