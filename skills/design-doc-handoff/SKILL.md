---
name: design-doc-handoff
description: Pull, handoff, and review design documents from Google Drive across Google AI, Claude AI, and Meta AI folders with interactive selection.
---

# Design Doc Handoff from Google Drive

This skill guides the agent to interactively select and download design documents from Google Drive into the workspace.

## Ecosystem Resolution

Resolve the root ecosystem folder dynamically by name:
- **Google AI**: search for folder named `Google AI` (`title = 'Google AI' and mimeType = 'application/vnd.google-apps.folder'`)
- **Claude AI**: search for folder named `Claude AI` (`title = 'Claude AI' and mimeType = 'application/vnd.google-apps.folder'`)
- **Meta AI**: search for folder named `Meta AI` (`title = 'Meta AI' and mimeType = 'application/vnd.google-apps.folder'`)

Or search via CLI:
```bash
gdrive readonly search --name "<ECOSYSTEM_NAME>" --type folder
```

## Execution Workflow

When the user asks to pull, inspect, or fetch a design document from Google Drive:

### Step 1: Ask for Ecosystem
Use the `ask_question` tool to prompt the user:
```json
{
  "question": "請問要從哪一個 AI 生態系拉取 Design Doc？",
  "options": [
    "(Recommended) Google AI",
    "Claude AI",
    "Meta AI"
  ]
}
```

### Step 2: List & Ask for Specific Design Doc
Once the ecosystem is chosen, resolve the target folder using the following priority:
1. **Exact Match First**: Search for a subfolder named exactly `Design Doc` inside the selected ecosystem folder.
2. **Keyword Match Fallback**: If no exact `Design Doc` folder exists, search for subfolders whose names contain the keyword `Design Doc` (e.g., `gdrive readonly search --parent-id <ECOSYSTEM_ID> --name-contains "Design Doc" --type folder`).
3. **Document Listing**: Once the folder is resolved, run `gdrive readonly ls <RESOLVED_FOLDER_ID>` to get the dynamic list of design documents (including Google Docs and Markdown files).
4. **Interactive Prompt**: Prompt the user via `ask_question` with the dynamically retrieved documents.

### Step 3: Export & Read Document
Run `gdrive readonly export` to export the chosen document as Markdown:
```bash
gdrive readonly export <FILE_ID> <target_markdown_file_path> --format md
```

*(On Windows PowerShell if `gdrive` is not globally on PATH, invoke via `& "<root>\plugins\gdrive\skills\gdrive\scripts\gdrive.cmd" readonly export ...`)*

### Step 4: Present & Review
Read the exported Markdown document and present its architecture, components, and next steps to the user.
