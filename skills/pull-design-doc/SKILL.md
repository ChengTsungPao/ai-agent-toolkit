---
name: pull-design-doc
description: Pull and review design documents from Google Drive across Google AI, Claude AI, and Meta AI folders with interactive selection.
---

# Pull Design Doc from Google Drive

This skill guides the agent to interactively select and download design documents from Google Drive into the workspace.

## Drive Folder Structure & IDs

- **Google AI Folder ID**: `1jVIoV0aLtWErGOVlMKOCLw03LAqDIW3k`
  - **Design Doc Folder (`Google AI/Design Doc`)**: `1qLKJRoJflN2uiz4FUqCgdqKi-XMeipPt`
    - `AI_Usage_Monitor_Design_Doc.md` (`1wFbkX0C6FX-ciW5ljv8_ftfsxq20QWGgZ5Cxo-UKRAc`)
    - `Gemini Live 控制 Claude App MCP 計畫` (`1-82-2u-696qOaml5uvh_M8o5eFQ17s8pMyykfa2Wuo0`)

- **Claude AI Folder ID**: `15k89RX_vcGgNxaNKgU0NLYIkPbOIoN8p`
  - Documents & Specs: `Agentic Workflow Note`, `Distill Model Note`, `Versus Incident EKS`, `Model Training Note`, etc. (Check for a `Design Doc` subfolder if present, or list root specs).

- **Meta AI Folder ID**: `1s2E-EJSHcVwrTDi2chaRIR4tMfSILNua`
  - Documents & Frameworks:
    - `00_MetaAI_目錄導覽_超詳細版_2026.md` (`11t7r1qP328LNaVNhizqbKMORYzEdKDWO3lyheX7YKFo`)
    - `AI Agent Skills 命中率優化 - 重構與架構實戰.md` (`1AA7z5sBtn4tKl42MtRchB3mnjVOmVUIQMrDZkSK8tTU`)
    - `Anthropic Scion 取代 Git 完整整合.md` (`1fLiZO1VVPes_Xf0-5vWZotTgG0lQetkLYolQaPnfzm4`)
    - Subfolder `02_agent_frameworks` (`1F_G0HbrQLhAL2NBhbVRnPcCrPrEWdhnw`)

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
1. **Exact Match First**: Search for a subfolder named exactly `Design Doc` inside the selected ecosystem folder (e.g. `Google AI/Design Doc`, Folder ID: `1qLKJRoJflN2uiz4FUqCgdqKi-XMeipPt`).
2. **Keyword Match Fallback**: If no exact `Design Doc` folder exists, search for subfolders whose names contain the keyword `Design Doc` (e.g., `gdrive readonly search --parent-id <ECOSYSTEM_ID> --name-contains "Design Doc" --type folder`).
3. **Document Listing**: Once the folder is resolved, run `gdrive readonly ls <RESOLVED_FOLDER_ID>` to get the up-to-date list of design documents (including Google Docs and Markdown files).
4. **Interactive Prompt**: Prompt the user via `ask_question` with the retrieved documents.

Example for `Google AI`:
```json
{
  "question": "請問要拉取 Google AI/Design Doc 資料夾底下的哪一份文件？",
  "options": [
    "(Recommended) AI_Usage_Monitor_Design_Doc.md (AI 多帳號用量監控儀表板)",
    "Gemini Live 控制 Claude App MCP 計畫"
  ]
}
```

### Step 3: Export & Read Document
Run `gdrive readonly export` to export the chosen document as Markdown:
```bash
gdrive readonly export <FILE_ID> <target_markdown_file_path> --format md
```

*(On Windows PowerShell if `gdrive` is not globally on PATH, invoke via `& "<root>\plugins\gdrive\skills\gdrive\scripts\gdrive.cmd" readonly export ...`)*

### Step 4: Present & Review
Read the exported Markdown document and present its architecture, components, and next steps to the user.
