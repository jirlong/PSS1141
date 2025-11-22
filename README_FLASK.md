# AI Web Service - Flask API 文件

這是一個基於 Flask 的 AI 服務 Web API,提供問答、翻譯、新聞摘要和故事創作等功能。

## 🚀 快速開始

### 1. 安裝相依套件

```bash
pip install -r requirements.txt
```

### 2. 設定環境變數

```bash
export OPENAI_API_KEY='your-api-key-here'
```

### 3. 啟動服務

```bash
python ai03-app.py
```

服務將在 `http://localhost:5000` 啟動。

### 4. 測試 API

開啟瀏覽器訪問: http://localhost:5000

或使用測試腳本:

```bash
python test_api.py
```

## 📡 API 端點說明

### 1. 一般問答 `/api/ask`

**方法:** POST

**請求範例:**
```json
{
  "input_text": "什麼是人工智慧?",
  "model": "gpt-5-nano",
  "instructions": "You are a helpful assistant."
}
```

**回應範例:**
```json
{
  "success": true,
  "input": "什麼是人工智慧?",
  "output": "人工智慧(AI)是指讓機器能夠模擬人類智能..."
}
```

**cURL 範例:**
```bash
curl -X POST http://localhost:5000/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "input_text": "什麼是人工智慧?",
    "model": "gpt-5-nano"
  }'
```

---

### 2. 翻譯服務 `/api/translate`

**方法:** POST

**功能:** 自動判斷語言,中英互譯

**請求範例:**
```json
{
  "text": "Hello, how are you?",
  "model": "gpt-5-nano"
}
```

**回應範例:**
```json
{
  "success": true,
  "original": "Hello, how are you?",
  "translated": "你好,你好嗎?"
}
```

**cURL 範例:**
```bash
curl -X POST http://localhost:5000/api/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, how are you?",
    "model": "gpt-5-nano"
  }'
```

---

### 3. 新聞摘要 `/api/news-summary`

**方法:** POST

**功能:** 提取新聞的 5W1H (Who, What, When, Where, Why, How)

**請求範例:**
```json
{
  "news_text": "台北市長蔣萬安今天宣布...",
  "model": "gpt-5-nano"
}
```

**回應範例:**
```json
{
  "success": true,
  "summary": {
    "who": "台北市長蔣萬安",
    "what": "宣布新的垃圾減量政策",
    "when": "今天(17日)上午",
    "where": "台北市政府",
    "why": "因應日益嚴重的垃圾問題",
    "how": "透過提高垃圾處理費和加強資源回收"
  }
}
```

**cURL 範例:**
```bash
curl -X POST http://localhost:5000/api/news-summary \
  -H "Content-Type: application/json" \
  -d '{
    "news_text": "台北市長蔣萬安今天宣布新政策..."
  }'
```

---

### 4. 故事創作 `/api/create-story`

**方法:** POST

**請求範例:**
```json
{
  "topic": "友誼",
  "word_count": 100,
  "model": "gpt-5-nano",
  "instructions": "Tell the story like 村上春樹"
}
```

**回應範例:**
```json
{
  "success": true,
  "topic": "友誼",
  "story": "在某個秋天的午後,我在咖啡廳遇見了多年未見的朋友..."
}
```

**cURL 範例:**
```bash
curl -X POST http://localhost:5000/api/create-story \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "友誼",
    "word_count": 100
  }'
```

---

### 5. 智能任務分派 `/api/dispatch`

**方法:** POST

**功能:** 自動判斷使用者意圖並分派到對應的功能

**請求範例:**
```json
{
  "user_request": "請幫我翻譯 Hello World",
  "model": "gpt-5-nano"
}
```

**回應範例:**
```json
{
  "success": true,
  "task_type": "translator",
  "result": {
    "original": "Hello World",
    "translated": "你好,世界"
  }
}
```

**支援的任務類型:**
- `translator` - 翻譯任務
- `news_summarizer` - 新聞摘要
- `story_creator` - 故事創作
- `general_question` - 一般問答

**cURL 範例:**
```bash
curl -X POST http://localhost:5000/api/dispatch \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "請幫我翻譯 Hello World"
  }'
```

---

### 6. 健康檢查 `/health`

**方法:** GET

**回應範例:**
```json
{
  "status": "healthy",
  "service": "AI Web Service",
  "version": "1.0.0"
}
```

**cURL 範例:**
```bash
curl http://localhost:5000/health
```

---

## 🧪 使用 Python Requests 測試

```python
import requests
import json

# 一般問答
response = requests.post(
    'http://localhost:5000/api/ask',
    json={'input_text': '什麼是人工智慧?'}
)
print(response.json())

# 翻譯
response = requests.post(
    'http://localhost:5000/api/translate',
    json={'text': 'Hello World'}
)
print(response.json())

# 新聞摘要
response = requests.post(
    'http://localhost:5000/api/news-summary',
    json={'news_text': '台北市長今天宣布...'}
)
print(response.json())

# 故事創作
response = requests.post(
    'http://localhost:5000/api/create-story',
    json={'topic': '友誼', 'word_count': 100}
)
print(response.json())

# 智能分派
response = requests.post(
    'http://localhost:5000/api/dispatch',
    json={'user_request': '請幫我翻譯 Hello'}
)
print(response.json())
```

---

## 🔧 設定選項

### 模型選擇

所有 API 都支援 `model` 參數,可選擇的模型:
- `gpt-5-nano` (預設,快速)
- `gpt-5-mini` (平衡)
- `gpt-4o-mini` (標準 OpenAI 模型)
- `gpt-4o` (更強大)

### 伺服器設定

修改 `ai03-app.py` 中的設定:

```python
# 修改 host 和 port
app.run(debug=True, host='0.0.0.0', port=5000)
```

- `host='0.0.0.0'` - 允許外部訪問
- `port=5000` - 修改連接埠
- `debug=True` - 開發模式(自動重載)

---

## 📝 錯誤處理

所有 API 在發生錯誤時會回傳:

```json
{
  "error": "錯誤訊息描述"
}
```

常見錯誤:
- `400` - 缺少必要參數
- `500` - 伺服器內部錯誤(通常是 API Key 問題)

---

## 🔐 安全性建議

1. **不要將 API Key 硬編碼** - 使用環境變數
2. **生產環境** - 使用 HTTPS
3. **限制存取** - 加入認證機制
4. **速率限制** - 防止濫用

---

## 📊 效能優化

1. 使用 `gpt-5-nano` 或 `gpt-5-mini` 獲得更快回應
2. 考慮加入快取機制
3. 使用 Gunicorn 或 uWSGI 部署到生產環境

---

## 🐛 疑難排解

### 無法啟動服務

```bash
# 檢查 Flask 是否安裝
pip install flask

# 檢查連接埠是否被占用
lsof -i :5000
```

### API Key 錯誤

```bash
# 確認環境變數已設定
echo $OPENAI_API_KEY

# 重新設定
export OPENAI_API_KEY='your-key'
```

### 連線錯誤

確保防火牆允許 5000 連接埠,或修改 host 設定。

---

## 📦 部署建議

### 使用 Gunicorn (生產環境)

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 ai03-app:app
```

### 使用 Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY ai03-app.py .
ENV OPENAI_API_KEY=""
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "ai03-app:app"]
```

---

## 📄 授權

本專案僅供學習使用。
