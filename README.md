# 🏎️ 跑跑卡丁車官網公告監控 - Discord 即時通知機器人

自動定期抓取 [跑跑卡丁車官方網站 (popkart.tiancity.com)](https://popkart.tiancity.com/homepage/v3/) 的最新公告與新聞，當有新公告發布時，第一時間在 Discord 頻道發送精美的 Rich Embed 卡片通知！

---

## ✨ 功能特色

- **完整監控**：涵蓋「系統公告」、「遊戲新聞」、「活動公告」、「賽事專題」全類別。
- **精美卡片**：使用 Discord Rich Embed 排版，按公告類別區分邊框顏色（紅/藍/橙/紫），顯示發布日期、分類標籤、官網直達連結。
- **內文摘要**：自動爬取公告內文的前 250 字摘要，讓你在 Discord 不開網頁就能掌握公告重點。
- **防重複推播**：本地記錄已發布歷史，第一次啟動自動登記既有公告，避免重啟時被舊文章洗版。
- **身分組標記**：支援設定 `@everyone`、`@here` 或指定身分組 ID，重大公告不漏接。
- **雙執行模式**：支援持續輪詢背景運行，或配合 Windows 工作排程器單次檢查退出 (`--once`)。

---

## 🚀 快速開始 (只需 3 步驟)

### 步驟 1：建立 Discord Webhook
1. 打開 Discord，進入你想接收通知的文字頻道。
2. 點擊頻道名稱旁的 **「編輯頻道 (齒輪圖示)」** ⚙️。
3. 點選左側選單的 **「整合 (Integrations)」** -> **「Webhook」** -> **「建立 Webhook」**。
4. 可以自定義機器人名稱（例如：`跑跑卡丁車公告`），最後點擊 **「複製 Webhook 網址」**。

### 步驟 2：設定 `config.json`
用記事本或編輯器打開目錄下的 `config.json`，將複製的網址貼在 `"discord_webhook_url"` 中：

```json
{
  "discord_webhook_url": "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL",
  "check_interval_seconds": 300,
  "fetch_article_preview": true,
  "first_run_behavior": "record_only",
  "mention_role_id": "",
  "notify_categories": [
    "系统公告",
    "游戏新闻",
    "活动公告",
    "赛事专题"
  ]
}
```

### 步驟 3：測試並啟動
1. 雙擊執行 **`test_webhook.bat`**：驗證 Discord 是否能成功收到測試訊息。
2. 雙擊執行 **`start.bat`**：立即啟動監控！程式將會常駐並依照設定的時間間隔自動檢查。

---

## ⚙️ 設定檔參數詳解 (`config.json`)

| 參數名稱 | 預設值 | 說明 |
| :--- | :--- | :--- |
| `discord_webhook_url` | `""` | 你的 Discord Webhook 網址（必填） |
| `check_interval_seconds` | `300` | 檢查頻率（秒），預設 300 秒（5 分鐘）檢查一次 |
| `fetch_article_preview` | `true` | 是否抓取公告內文前 250 字做為卡片摘要 |
| `first_run_behavior` | `"record_only"` | 首次執行行為：`"record_only"` 僅登記現有公告不發送通知；`"notify_all"` 立即推播現有所有公告 |
| `mention_role_id` | `""` | 標記對象：可填身分組 ID（如 `"123456789"`）、`"everyone"` 或 `"here"`，留空則不標記 |
| `notify_categories` | `["系统公告", ...]` | 要接收通知的分類列表，可自行刪減過濾 |

---

## 🛠️ 命令列進階用法

你可以透過命令列直接調用 `notifier.py`：

```bash
# 正常持續輪詢監控
python notifier.py

# 發送測試通知到 Discord 驗證連線
python notifier.py --test

# 單次檢查模式（檢查一次有無新文章，完成後立即退出，適合配合工作排程器）
python notifier.py --once

# 重設歷史記錄（清空 history.json）
python notifier.py --reset
```

---

## 🕒 Windows 背景定時排程（可選）

如果你希望這支程式每天自動在背景定時執行，而不需要開著黑底視窗：

1. 按鍵盤 `Win + R` 輸入 `taskschd.msc` 開啟 **工作排程器**。
2. 點擊右側 **「建立基本工作」**。
3. 名稱填寫 `PopkartNewsCheck`。
4. 觸發程序選擇「每天」或「在電腦啟動時」。
5. 動作選擇「啟動程式」：
   - **程式或指令碼**：`python`（或 python 的完整路徑）
   - **新增引數**：`notifier.py --once`
   - **開始於**：專案目錄路徑（例如：`C:\Users\user\Desktop\ide`）


## ☁️ 雲端 24 小時監控（完全免費）

GitHub Actions 每 5 分鐘自動在雲端檢查一次，**不需要電腦保持開機**！
公開儲存庫（Public Repository）每月擁有免費無上限的 Actions 標準 runner 額度。

### 涵蓋監控項目
1. **跑跑卡丁車官網** (`notifier.py`)：系統公告、遊戲新聞、活動公告、賽事專題（Rich Embed 彩色卡片排版）。
2. **Nexon 官方網站** (`抓取跑跑3公告/爬蟲.py`)：官網最新訊息公告即時推播。

---

### 🚀 雲端 24 小時部署教學

#### 步驟 1：建立 GitHub 儲存庫
1. 前往 [GitHub 建立新儲存庫](https://github.com/new)。
2. Repository name 填寫喜歡的名稱（例如：`kart-news-bot`）。
3. 選擇 **Public**（公開），**不要勾選**「Add a README file」。
4. 點擊 **Create repository**。

#### 步驟 2：推動專案到 GitHub
在專案目錄開啟 PowerShell 執行：
```bash
git init -b main
git add .
git commit -m "Initial commit: Kart announcement 24/7 monitor"
git remote add origin https://github.com/你的帳號/你的儲存庫.git
git push -u origin main
```
*(.gitignore 已自動排除本機 `config.json`，防止 Webhook 密鑰外流。)*

#### 步驟 3：設定 GitHub Secrets (Webhook 密鑰)
1. 進入你的 GitHub 儲存庫頁面。
2. 依序點擊 **Settings** → **Secrets and variables** → **Actions**。
3. 點擊 **New repository secret**：
   - **Name**：`DISCORD_WEBHOOK_URL`
   - **Secret**：貼上你的 Discord Webhook 網址
4. *(可選)* 若 Nexon 想發送到不同頻道，可再新增一個 Secret：
   - **Name**：`DISCORD_WEBHOOK_URL_NEXON`
   - **Secret**：貼上 Nexon 專用的 Webhook 網址（若無則會自動使用主要 Webhook）。

#### 步驟 4：啟用並啟動 Actions
1. 點擊儲存庫上方的 **Actions** 頁籤。
2. 若顯示提示，點選 **「I understand my workflows, go ahead and enable them」**。
3. 點選左側工作流程 **「跑跑卡丁車公告監控」**，點擊右側 **Run workflow** 即可立即手動觸發測試！
4. 之後 GitHub 就會每 5 分鐘自動排程執行一次，實現 24 小時無間斷監控。


