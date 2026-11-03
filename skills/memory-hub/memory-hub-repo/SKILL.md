---
name: memory-hub-repo
description: "查看或修改這個對話的 Memory Hub 記憶塊綁定了哪些 repo（mem: repo、mem: repo add、mem: repo rm）。觸發：使用者的訊息裡有 mem: repo 但沒被 hook 攔下（例如前面多了 -、引號、其他文字，或所在工具沒有這個 hook），或用一般說法要求「把 X 加到記憶塊」「從記憶塊拿掉 X」「這個記憶塊綁了哪些 repo」。"
---

# Memory Hub repo 綁定

Claude Code 和 Codex 的 UserPromptSubmit hook（`memory-command.mjs`）會攔下以 `mem:` 開頭的訊息並直接回覆。
**訊息會送到你這邊，就表示 hook 沒比對到**（或你在 Antigravity，它沒有這個 hook）。
這時不要叫使用者重送，直接用下面的方法替他執行。

綁定存在 MemoryCore 伺服器上（記憶塊的 metadata 和 binding），本機的
`~/.memory-tdai/*/sessions/<id>.json` 只是快取，改它沒有作用。一律透過 `memory-command.mjs` 修改。

## 指令

| 意圖 | 指令文字 |
|---|---|
| 查看目前綁定 | `mem: repo` |
| 加入 repo | `mem: repo add <路徑或已有記憶的 repo 名稱>` |
| 移除 repo | `mem: repo rm <repo 名稱或 hash 前綴>` |

## 這個對話的 session id

依你所在的工具取用，**不要混用**（從某個工具啟動另一個工具時，環境變數會被繼承，例如 Codex 裡也看得到 `CLAUDE_CODE_SESSION_ID`）：

| 工具 | session id |
|---|---|
| Claude Code | 環境變數 `CLAUDE_CODE_SESSION_ID` |
| Codex | 環境變數 `CODEX_THREAD_ID` |
| Antigravity | 這個對話的 conversation id，也就是你的 artifact 資料夾 `~/.gemini/antigravity/brain/<id>/` 的名稱 |

取不到或不確定時，不要猜，告訴使用者改用 Memory Hub 面板調整。

## 執行方式

由 node 把 hook 腳本、session id、指令文字以參數接收，自己組 JSON 並啟動 hook。不要手寫 JSON
（Windows 路徑的反斜線會被吃掉），也不要用 shell 的管線把 JSON 傳給 hook（PowerShell 5.1 會在前面加 BOM，
hook 解析失敗就默默結束、沒有輸出）。下面的 JS 只用反引號，在 Bash 和 PowerShell 的單引號字串裡都不必跳脫。

Bash：

```bash
HUB="${PERSONAL_MEMORY_HUB_DIR:-$HOME/personal-memory-hub}"
SID="$CLAUDE_CODE_SESSION_ID"   # Codex: $CODEX_THREAD_ID；Antigravity: conversation id
node -e 'const [hook,session_id,prompt]=process.argv.slice(1);const r=require(`child_process`).spawnSync(process.execPath,[hook],{input:JSON.stringify({session_id,cwd:process.cwd(),prompt}),encoding:`utf8`});process.stdout.write(r.stdout||r.stderr||`(no output)`)' \
  "$HUB/agents/claude-code/hooks/memory-command.mjs" "$SID" "mem: repo add ai-usage-monitor"
```

PowerShell：

```powershell
$hub = if ($env:PERSONAL_MEMORY_HUB_DIR) { $env:PERSONAL_MEMORY_HUB_DIR } else { "$HOME\personal-memory-hub" }
$sid = $env:CODEX_THREAD_ID   # Claude Code: $env:CLAUDE_CODE_SESSION_ID；Antigravity: conversation id
$js = 'const [hook,session_id,prompt]=process.argv.slice(1);const r=require(`child_process`).spawnSync(process.execPath,[hook],{input:JSON.stringify({session_id,cwd:process.cwd(),prompt}),encoding:`utf8`});process.stdout.write(r.stdout||r.stderr||`(no output)`)'
node -e $js "$hub\agents\claude-code\hooks\memory-command.mjs" $sid "mem: repo add ai-usage-monitor"
```

- 輸出是 `{"decision":"block","reason":"…"}`，把 `reason` 原文告訴使用者，例如
  `🧠 記憶塊 d421a1be → ai-usage-monitor (f716b9e) · llm-gateway (4f98fc7)`。
- `(no output)`：指令文字不是以 `mem: repo` 開頭，或 session id 是空的；檢查後重試。
- `reason` 是錯誤訊息（例如找不到 repo）：照實告訴使用者。用名稱找不到時，改用完整路徑再試一次
  （repo 名稱只對已經有記憶的 repo 有效）；路徑有空白時整段指令文字要加引號。

## 規則

- 只執行使用者要求的動作。只要求查看時只跑 `mem: repo`，不要順手 add 或 rm。
- `rm` 會讓那個 repo 不再被自動加回，執行前確認使用者指的是哪個 repo；名稱不明確時先跑 `mem: repo` 列出來讓使用者選。
- 修改會立即寫到伺服器；之後每一輪的 hook 都會沿用，不會被改回。Claude Code 和 Codex 的 Stop hook 會在下一輪結束時再印一次綁定。
