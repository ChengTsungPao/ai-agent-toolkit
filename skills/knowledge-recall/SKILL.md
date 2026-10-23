---
name: "knowledge-recall"
description: "查 Jack 的知識庫回答問題：Google AI Memory、Meta AI Memory、Claude AI Memory（其他 artifact、Claude memory、Project 文件）。觸發：查我的筆記/memory/知識庫、我之前整理過的 X。"
---

# Knowledge Recall

從 Jack 自己累積的三個知識來源找答案，回答以來源為準，不用網路搜尋取代。

## 來源

| 代號 | 內容 | 位置 |
|---|---|---|
| Google | Google AI Memory（Drive「Youtube Knowledge」等筆記摘要） | https://claude.ai/code/artifact/bdf9dc59-01fb-4c6a-b63e-0fd06211cf23 |
| Meta | Meta AI Memory（Drive「Meta AI」資料夾摘要） | https://claude.ai/code/artifact/87c6b966-131b-4235-a4d3-7bed7acdfb40 |
| Claude | 上面兩個以外的所有 artifact + Claude memory + 目前 Project 文件 | Artifact list / memory / Projects |

## 提問規則（硬性）

- 需要問使用者時，一律用 AskUserQuestion 出選擇題，不用純文字提問。
- 每題 2–4 個選項，AI 建議的放第一個並標「(Recommended)」。
- 不要自己加「其他／自行輸入」選項，工具會自動提供。
- 多個問題一次問完（最多 4 題），不要分好幾輪。
- AskUserQuestion 不可用時，才改用文字提問，並附編號選項讓使用者回數字。

## Step 1：選來源

- 使用者訊息已指定來源（例如「查 Meta」「全部查」）→ 直接用，不再問。
- 否則用 AskUserQuestion（multiSelect: true）問一題：「要查哪個？」選項：Google AI Memory、Meta AI Memory、Claude AI Memory、全部（Recommended，放第一個）。
- AskUserQuestion 不可用或無人回應 → 查全部，並在回答開頭說明。

## Step 2：抽關鍵字

從問題抽 3–8 個關鍵字，中英文都列（例：命中率 / hit rate / skill / tool calling / 路由 / routing）。筆記標題與內容中英混雜，只用一種語言會漏。

## Step 3：查各來源（選了多個就在同一輪並行呼叫）

### Google / Meta（兩者 schema 相同）

1. `ArtifactData` action `list`、collection `files`、`out_dir` 設在 scratchpad 下（例 `<scratchpad>/kr/google`、`<scratchpad>/kr/meta`），有 `next_cursor` 就繼續翻頁到完。
2. 用 Grep 在存下來的 JSON 搜關鍵字（`-i`，output_mode files_with_matches），欄位涵蓋 title、summary、tags、points、flows、tables、sections。
3. 預設略過 `removed: true` 的文件（通常已有 Google 文件版取代），除非沒有其他命中。
4. 讀命中的 JSON，先用 summary / points / flows / tables 回答。
5. 摘要不夠具體、或使用者要細節 → 用 `mcp__Google_Drive__read_file_content`，fileId = 該文件的 id，讀原文。`partial: true` 代表摘要不完整，優先讀原文。
6. 問題跟日期有關（「上週新增什麼」「10/15 的筆記」）→ 改查 collection `days`（doc id 為 YYYY-MM-DD）。

### Claude

1. **其他 artifact**：`Artifact` action `list`、scope `mine`、limit 50，排除 Google AI Memory 與 Meta AI Memory 兩個 URL。依標題挑相關的，用 action `read` 讀；頁面被截斷就用 `path: "index.html"` 讀完整檔再 Grep。頁面若用資料庫存內容（HTML 裡出現 `window.claude` db 或註解提到 collection），改用 ArtifactData 讀。
2. **Claude memory**：看 context 裡的 memory listing，依描述挑相關檔案，一次 `mcp__memory__memory_read` 多個 path。
3. **Project 文件**：有 Projects 工具時用 `project_search` 查關鍵字，必要時 `project_read`。

### 都沒命中

換同義詞或上位詞再搜一輪。仍沒有就直說「三個來源都沒有相關筆記」，列出查了哪些，再用 AskUserQuestion 問「上網查（Recommended）／不用」（要換關鍵字，使用者會用自行輸入）；不要自己用網路結果冒充筆記內容。

## Step 4：回答

- 繁體中文、精簡、先講答案。
- 每個重點標來源：`[Meta]` `[Google]` `[Claude]`。
- 同一主題多個來源講法不同 → 明確指出差異，不要自己挑一個默默合併。
- 筆記裡標註未驗證、示意數字、或明顯有誤的內容（例：與已知事實衝突）→ 保留並註明，不當成定論。
- 結尾列「來源」：文件標題 + Google Doc 連結或 artifact 名稱，不貼原始 JSON。
- 只是查詢，不修改任何 artifact、資料庫或 memory；使用者要求補寫時再另外處理。