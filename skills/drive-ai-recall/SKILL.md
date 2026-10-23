---
name: drive-ai-recall
description: "查 Jack 放在 Google Drive 的三個 AI 知識庫回答問題：Google AI、Meta AI、Claude AI 三個資料夾（筆記、文件、整理過的資料）。觸發：查我的筆記/知識庫/Drive、我之前整理過的 X。"
---

# Drive AI Recall

從 Jack 的 Google Drive 根目錄下三個資料夾找答案。回答以資料夾內的文件為準，不用網路搜尋取代。

## 來源

| 代號 | Drive 資料夾 | 資料夾 ID |
|---|---|---|
| Google | Google AI（底下有 Youtube Knowledge、AI/ML knowledge、Software Knowledge、Investment knowledge 等子資料夾） | `1jVIoV0aLtWErGOVlMKOCLw03LAqDIW3k` |
| Meta | Meta AI（底下有 IG FB Knowledge 等） | `1s2E-EJSHcVwrTDi2chaRIR4tMfSILNua` |
| Claude | Claude AI | `15k89RX_vcGgNxaNKgU0NLYIkPbOIoN8p` |

ID 找不到或讀取失敗時，用 `title = 'Google AI'`（或 Meta AI、Claude AI）加 `mimeType = 'application/vnd.google-apps.folder'` 重新找資料夾。

## 提問規則（硬性）

- 需要問使用者時，一律用 AskUserQuestion 出選擇題，不用純文字提問。
- 每題 2–4 個選項，AI 建議的放第一個並標「(Recommended)」。
- 不要自己加「其他／自行輸入」選項，工具會自動提供。
- 多個問題一次問完（最多 4 題），不要分好幾輪。
- AskUserQuestion 不可用時，才改用文字提問，並附編號選項讓使用者回數字。

## Step 1：選來源

- 使用者訊息已指定來源（例如「查 Meta」「全部查」）→ 直接用，不再問。
- 否則用 AskUserQuestion（multiSelect: true）問一題：「要查哪個？」選項：Google AI、Meta AI、Claude AI、全部（Recommended，放第一個）。
- AskUserQuestion 不可用或無人回應 → 查全部，並在回答開頭說明。

## Step 2：抽關鍵字

從問題抽 3–8 個關鍵字，中英文都列（例：命中率 / hit rate / skill / tool calling / 路由 / routing）。文件標題與內容中英混雜，只用一種語言會漏。

## Step 3：查各來源（選了多個就在同一輪並行呼叫）

1. 用 Google Drive 的 `search_files`，query 為 `fullText contains '<關鍵字>'`，並用 `parentId = '<資料夾 ID>'` 限定範圍。`parentId` 只涵蓋直屬子項，所以先列出該資料夾的子資料夾（`mimeType = 'application/vnd.google-apps.folder'`），對每個子資料夾再各查一次；沒有子資料夾的就只查本層。
2. 也用 `title contains '<關鍵字>'` 查一輪，標題命中通常最準。多個關鍵字分開查，再合併結果。
3. 優先看標題命中和多個關鍵字同時命中的文件。結果太多時（超過約 10 份）先看標題與摘要再挑，不要全部讀。
4. 用 `read_file_content` 讀命中的文件（fileId 為該文件 id）。內容很長時只讀與問題相關的部分，並以文件標題和章節標註出處。
5. 問題跟時間有關（「上週新增什麼」）→ 用 `modifiedTime` 或 `createdTime` 限定查詢。
6. 只查 Google Docs、Sheets、Slides、PDF 和文字檔；其他類型（圖片、影片）只列出檔名，不要假裝讀過內容。

### 都沒命中

換同義詞或上位詞再搜一輪。仍沒有就直說「三個資料夾都沒有相關文件」，列出查了哪些，再用 AskUserQuestion 問「上網查（Recommended）／不用」；不要自己用網路結果冒充文件內容。

## Step 4：回答

- 繁體中文、精簡、先講答案。
- 每個重點標來源：`[Google]` `[Meta]` `[Claude]`。
- 同一主題多個來源講法不同 → 明確指出差異，不要自己挑一個默默合併。
- 文件裡標註未驗證、示意數字、或明顯有誤的內容（例：與已知事實衝突）→ 保留並註明，不當成定論。
- 結尾列「來源」：文件標題 + Drive 連結（`viewUrl`），不貼原始內容。
- 只是查詢，不修改、不刪除、不分享任何 Drive 檔案；使用者要求補寫時再另外處理。
