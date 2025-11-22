# OpenAI 問答範例程式

這是一個使用 OpenAI API 來回答問題的 Python 範例程式。

## 功能特色

- ✅ 簡單問答
- ✅ 根據上下文回答問題
- ✅ 多輪對話
- ✅ 互動式問答模式
- ✅ 完整的錯誤處理

## 安裝步驟

### 1. 安裝所需套件

```bash
pip install -r requirements.txt
```

或手動安裝:

```bash
pip install openai python-dotenv
```

### 2. 設定 OpenAI API Key

#### 方法一:使用環境變數 (推薦)

在終端機中設定:

```bash
export OPENAI_API_KEY='your-api-key-here'
```

或建立 `.env` 檔案:

```bash
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

#### 方法二:直接在程式中設定

編輯 `ai01.py`,將以下這行:

```python
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")
```

改為:

```python
OPENAI_API_KEY = "your-actual-api-key-here"
```

**注意:** 方法二僅適合測試使用,請勿將含有真實 API Key 的程式碼上傳到公開的版本控制系統。

### 3. 取得 OpenAI API Key

1. 前往 [OpenAI Platform](https://platform.openai.com/)
2. 註冊/登入帳號
3. 進入 [API Keys](https://platform.openai.com/api-keys) 頁面
4. 點擊 "Create new secret key" 建立新的 API Key
5. 複製 API Key (只會顯示一次)

## 使用方法

### 執行範例程式

```bash
python ai01.py
```

程式會依序執行以下範例:

1. **簡單問答** - 詢問「什麼是人工智慧?」
2. **根據上下文回答** - 提供台灣相關資訊,詢問首都位置
3. **多輪對話** - 展示連續對話的能力
4. **互動式問答** - 可以自由輸入問題,輸入 `quit` 或 `exit` 結束

### 在自己的程式中使用

```python
from openai import OpenAI
import os

# 建立客戶端
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 簡單問答
def ask_question(question):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "你是一個有幫助的助理。"},
            {"role": "user", "content": question}
        ]
    )
    return response.choices[0].message.content

# 使用範例
answer = ask_question("Python 是什麼?")
print(answer)
```

## 函式說明

### `ask_question(question, model="gpt-4o-mini", temperature=0.7)`

使用 OpenAI API 來回答單一問題。

**參數:**
- `question` (str): 要問的問題
- `model` (str): 使用的模型,預設為 "gpt-4o-mini"
- `temperature` (float): 創造性程度 (0.0-1.0),預設 0.7

**回傳:**
- `str`: AI 的回答

### `ask_question_with_context(question, context, model="gpt-4o-mini", temperature=0.7)`

根據提供的上下文資訊回答問題。

**參數:**
- `question` (str): 要問的問題
- `context` (str): 相關的上下文資訊
- `model` (str): 使用的模型
- `temperature` (float): 創造性程度

**回傳:**
- `str`: AI 的回答

### `chat_conversation(messages, model="gpt-4o-mini", temperature=0.7)`

進行多輪對話。

**參數:**
- `messages` (list): 對話訊息列表,格式為 `[{"role": "user", "content": "..."}, ...]`
- `model` (str): 使用的模型
- `temperature` (float): 創造性程度

**回傳:**
- `str`: AI 的回答

## 模型選擇

常用的 OpenAI 模型:

| 模型 | 說明 | 適用場景 |
|------|------|----------|
| `gpt-4o-mini` | 快速且經濟實惠 | 一般問答、對話 |
| `gpt-4o` | 更強大的能力 | 複雜推理、分析 |
| `gpt-4-turbo` | 平衡效能與成本 | 專業用途 |

## Temperature 參數說明

- **0.0 - 0.3**: 保守、一致性高,適合事實性問答
- **0.4 - 0.7**: 平衡創造性與一致性,適合一般對話
- **0.8 - 1.0**: 創意性高、多樣性高,適合創作內容

## 注意事項

1. **API Key 安全性**: 請勿將 API Key 上傳到公開的程式碼庫
2. **使用限制**: OpenAI API 是付費服務,請注意使用量
3. **速率限制**: 注意 API 的速率限制,避免過於頻繁的請求
4. **錯誤處理**: 程式已包含基本錯誤處理,但實際使用時建議加強

## 疑難排解

### 錯誤: "Import 'openai' could not be resolved"

請確認已安裝 openai 套件:

```bash
pip install openai
```

### 錯誤: "Authentication Error"

請確認:
1. API Key 是否正確設定
2. API Key 是否有效
3. 帳戶是否有足夠的額度

### 錯誤: "Rate limit exceeded"

您已超過 API 使用限制,請:
1. 稍後再試
2. 減少請求頻率
3. 升級您的 OpenAI 計畫

## 相關資源

- [OpenAI API 文件](https://platform.openai.com/docs/)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [快速入門指南](https://platform.openai.com/docs/quickstart)
- [定價資訊](https://openai.com/pricing)

## 授權

本範例程式僅供學習使用。
