# Flask Web Service 快速啟動指南

## 🚀 快速開始

### 1. 安裝套件
```bash
pip install flask openai pydantic python-dotenv
```

### 2. 啟動 Flask 服務
```bash
python flask_app.py
```

服務將在 http://localhost:5001 啟動

### 3. 開啟瀏覽器查看 API 文件
```
http://localhost:5001
```

### 4. 測試 API (另開終端機)
```bash
python test_api.py
```

## 📡 快速測試

```bash
# 測試問答
curl -X POST http://localhost:5001/api/ask \
  -H "Content-Type: application/json" \
  -d '{"input_text": "什麼是人工智慧?"}'

# 測試翻譯
curl -X POST http://localhost:5001/api/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello World"}'
```

## 📚 完整文件
查看 README_FLASK.md 獲取完整的 API 文件。
