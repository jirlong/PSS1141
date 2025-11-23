# 實戰教學：打造微服務架構的 AI LINE Bot

本教學將帶領學生建立一個現代化的 AI LINE Bot。我們將採用**微服務 (Microservices)** 的概念，將系統拆分為兩個獨立的服務：
1. **AI 腦袋 (Backend)**：負責處理邏輯、呼叫 LLM (Ollama)。
2. **LINE 介面 (Frontend)**：負責接收使用者訊息、轉發請求、回覆訊息。

這種架構優點在於解耦，AI 服務可以同時被網頁、App 或其他 Bot 共用，而不僅限於 LINE。

---

## 1. 系統架構圖

```mermaid
graph LR
    User((使用者)) -- LINE App --> LINE_Server[LINE 平台]
    LINE_Server -- Webhook (Port 5003) --> Ngrok[Ngrok 隧道]
    Ngrok --> LineBot[line_bot.py (介面層)]
    LineBot -- REST API (Port 5002) --> AI_Service[flask_ollama_app.py (AI 腦袋)]
    AI_Service -- 本地呼叫 --> Ollama[Ollama 模型 (Gemma/Llama)]
```

---

## 2. 環境準備與套件安裝

在開始寫程式碼之前，我們需要安裝必要的 Python 套件。

### 安裝指令
請在終端機 (Terminal) 執行：

```bash
pip install flask line-bot-sdk requests ollama
```

### 套件說明
*   **flask**: 建立 Web Server，用來提供 API 介面。
*   **line-bot-sdk**: LINE 官方提供的開發套件，簡化簽章驗證與訊息傳送。
*   **requests**: 用來從 LINE Bot 程式發送 HTTP 請求給 AI 服務。
*   **ollama**: 用來與本地運行的 Ollama 模型溝通。

---

## 3. 建立核心檔案

我們需要建立兩個主要的 Python 檔案。

### (A) AI 服務端：`flask_ollama_app.py`
這是系統的「大腦」。它不關心訊息是從 LINE 還是網頁來的，它只負責接收文字、執行 AI 任務、回傳結果。

**主要功能：**
*   啟動於 `http://localhost:5002`。
*   提供 `/api/dispatch` 接口，接收 JSON 格式的請求。
*   內建 `task_dispatcher` 函式，能自動判斷使用者意圖（翻譯、新聞摘要、寫故事、閒聊）。

### (B) LINE Bot 介面端：`line_bot.py`
這是系統的「櫃檯」。它負責接待 LINE 的使用者。

**主要功能：**
*   啟動於 `http://localhost:5003`。
*   提供 `/callback` 接口，接收 LINE 平台的 Webhook 事件。
*   **關鍵動作**：收到訊息後，使用 `requests.post()` 將內容轉發給 `flask_ollama_app.py`，拿到 AI 回應後，再透過 LINE SDK 回傳給使用者。

---

## 4. LINE Developer Console 設定

要讓程式能與 LINE 溝通，你需要先申請一個機器人帳號。

1.  前往 [LINE Developers Console](https://developers.line.biz/) 並登入。
2.  建立一個 **Provider** (專案提供者)。
3.  建立一個 **Messaging API Channel**。
4.  **取得關鍵憑證**：
    *   **Channel Secret**: 在 "Basic settings" 頁籤中。
    *   **Channel Access Token**: 在 "Messaging API" 頁籤中（需點擊 Issue 按鈕產生）。
5.  **設定 Webhook** (稍後在步驟 5 填入)。

---

## 5. 啟動系統 (三個終端機視窗)

這是一個分散式系統，我們需要開啟 **三個** 不同的終端機視窗來分別執行不同的任務。

### Terminal 1: 啟動 AI 腦袋
這個視窗負責運行 AI 運算邏輯。

```bash
# 確保 Ollama 已經在背景執行，且有模型 (例如 gemma3:1b)
python flask_ollama_app.py
```
> **狀態**：服務啟動於 `http://localhost:5002`，等待被呼叫。

### Terminal 2: 啟動 LINE Bot
這個視窗負責處理 LINE 訊息。請將 `<YOUR_TOKEN>` 換成步驟 4 取得的真實資料。

```bash
# 設定環境變數 (Mac/Linux)
export LINE_CHANNEL_ACCESS_TOKEN="你的_Channel_Access_Token"
export LINE_CHANNEL_SECRET="你的_Channel_Secret"

# 啟動程式
python line_bot.py
```
> **狀態**：服務啟動於 `http://localhost:5003`，等待 ngrok 轉發流量。

### Terminal 3: 建立對外隧道 (ngrok)
由於 LINE 的伺服器在網際網路上，無法直接連線到你電腦的 `localhost`。我們需要 `ngrok` 來打通一條隧道。

**注意**：我們要將隧道連到 **LINE Bot (Port 5003)**，而不是 AI 服務。

```bash
ngrok http 5003
```

執行後，ngrok 會顯示一個 HTTPS 網址，例如：
`Forwarding https://abcd-1234.ngrok-free.app -> http://localhost:5003`

---

## 6. 最後一步：串接 Webhook

1.  複製 Terminal 3 產生的 ngrok 網址 (HTTPS 開頭)。
2.  回到 LINE Developers Console 的 "Messaging API" 設定頁。
3.  找到 **Webhook URL** 欄位，點擊 Edit。
4.  貼上網址，並在後方加上 `/callback`。
    *   範例：`https://abcd-1234.ngrok-free.app/callback`
5.  點擊 **Update**，然後點擊 **Verify**。
    *   如果 Terminal 2 有顯示 `200 OK`，代表連線成功！
6.  開啟 **Use webhook** 選項。

---

## 7. 測試與驗證

現在，拿起手機，加入你的 LINE Bot 好友，試著傳送訊息：

1.  **測試翻譯**：「翻譯 Apple」 -> 系統應回傳中文翻譯。
2.  **測試創作**：「寫一個關於太空人的故事」 -> 系統應回傳故事內容。
3.  **觀察 Terminal**：
    *   **Terminal 3 (ngrok)**：會看到 LINE 的 POST 請求進來。
    *   **Terminal 2 (line_bot)**：會看到接收到訊息，並顯示 `Request body...`。
    *   **Terminal 1 (AI Service)**：會看到 `/api/dispatch` 被呼叫，並顯示 AI 處理日誌。

這就是一個完整的微服務 AI Bot 開發流程！
