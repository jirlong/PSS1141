from flask import Flask, request, jsonify, render_template, abort
from openai import OpenAI
from pydantic import BaseModel
import json
import os

# LINE Bot SDK Imports
from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

app = Flask(__name__)

# 設定 OpenAI API Key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "") # 建議從環境變數讀取
client = OpenAI(api_key=OPENAI_API_KEY)

# LINE Bot 設定
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "YOUR_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "YOUR_CHANNEL_SECRET")

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


# 定義 5W1H 的 JSON Schema
class News5W1H(BaseModel):
    who: str      # 誰 - 新聞主角
    what: str     # 什麼事 - 發生的事件
    when: str     # 何時 - 時間
    where: str    # 何地 - 地點
    why: str      # 為何 - 原因
    how: str      # 如何 - 方法或過程


# ==================== AI 功能函式 ====================

def ask(input_text, model="gpt-5-nano", instructions="You are a helpful assistant."):
    """通用的問答函式"""
    response = client.responses.create(
        model=model,
        instructions=instructions,
        input=input_text
    )
    return response.output_text


def translator(text, model="gpt-5-nano"):
    """智能翻譯函式"""
    instructions = """You are a professional translator.
    If the input text is in Traditional Chinese (繁體中文), translate it to English.
    If the input text is in English, translate it to Traditional Chinese (繁體中文).
    Only return the translated text, nothing else."""
    
    response = client.responses.create(
        model=model,
        instructions=instructions,
        input=text
    )
    translated_text = response.output_text
    return {"original": text, "translated": translated_text}


def news_5w1h_summarizer(news_text, model="gpt-5-nano"):
    """新聞 5W1H 摘要函式"""
    response = client.responses.parse(
        model=model,
        input=[
            {
                "role": "system",
                "content": """你是一位專業的新聞分析師。請從新聞內容中提取 5W1H 資訊:
- who: 新聞中的主要人物或組織
- what: 發生了什麼事件
- when: 事件發生的時間
- where: 事件發生的地點
- why: 事件發生的原因或動機
- how: 事件如何發生或執行的方式

請用繁體中文回答,如果某項資訊在新聞中未提及,請填寫「未提及」。"""
            },
            {
                "role": "user",
                "content": news_text
            }
        ],
        text_format=News5W1H
    )
    result = response.output_parsed
    return result.model_dump()


def create_story(topic, model="gpt-5-nano", instructions="Tell the story like 村上春樹", word_count=100):
    """根據主題創作床邊故事"""
    response = client.responses.create(
        model=model,
        instructions=instructions,
        input=f"寫一個跟{topic}有關的床邊故事，近{word_count}字的段落即可"
    )
    return response.output_text


def task_dispatcher(user_request, model="gpt-5-nano"):
    """任務分派器"""
    classification_prompt = f"""請分析以下使用者請求,判斷應該使用哪個函式處理。

使用者請求: "{user_request}"

可用的函式:
1. translator - 用於翻譯任務,關鍵詞:翻譯、translate、中翻英、英翻中
2. news_summarizer - 用於新聞分析和摘要,關鍵詞:新聞、摘要、5W1H、分析新聞
3. story_creator - 用於創作故事,關鍵詞:故事、床邊故事、創作、寫一個故事
4. general_question - 用於一般問答,其他所有情況

請只回答函式名稱,不要有其他內容。從以下選項中選一個:
translator, news_summarizer, story_creator, general_question"""

    function_name = ask(
        classification_prompt,
        model=model,
        instructions="You are a task classifier. Return only the function name."
    ).strip().lower()
    
    # 根據判斷結果分派任務
    if "translator" in function_name:
        extract_prompt = f"從以下請求中提取需要翻譯的文字內容,只回傳要翻譯的文字:\n{user_request}"
        text_to_translate = ask(extract_prompt, model=model, instructions="Extract only the text to translate.").strip()
        result = translator(text_to_translate, model=model)
        return {"task_type": "translator", "result": result}
    
    elif "news_summarizer" in function_name or "news" in function_name:
        extract_prompt = f"從以下請求中提取新聞內容文字,只回傳新聞文字本身:\n{user_request}"
        news_content = ask(extract_prompt, model=model, instructions="Extract only the news content.").strip()
        result = news_5w1h_summarizer(news_content, model=model)
        return {"task_type": "news_summarizer", "result": result}
    
    elif "story" in function_name:
        extract_prompt = f"從以下請求中提取故事主題,只回傳主題關鍵詞:\n{user_request}"
        topic = ask(extract_prompt, model=model, instructions="Extract only the story topic.").strip()
        result = create_story(topic, model=model)
        return {"task_type": "story_creator", "result": {"topic": topic, "story": result}}
    
    else:  # general_question
        result = ask(user_request, model=model)
        return {"task_type": "general_question", "result": result}


def format_result_for_line(task_result):
    """將任務結果格式化為 LINE 訊息文字"""
    task_type = task_result.get("task_type")
    result = task_result.get("result")

    if task_type == "translator":
        return f"【翻譯結果】\n原文: {result['original']}\n\n翻譯: {result['translated']}"
    
    elif task_type == "news_summarizer":
        return (f"【新聞 5W1H 分析】\n"
                f"Who: {result['who']}\n"
                f"What: {result['what']}\n"
                f"When: {result['when']}\n"
                f"Where: {result['where']}\n"
                f"Why: {result['why']}\n"
                f"How: {result['how']}")
    
    elif task_type == "story_creator":
        return f"【床邊故事: {result['topic']}】\n\n{result['story']}"
    
    else: # general_question
        return result


# ==================== Web Service API Endpoints ====================

@app.route('/')
def home():
    """首頁 - 提供互動式 Web 介面"""
    return render_template('index.html')


@app.route('/api/ask', methods=['POST'])
def api_ask():
    """一般問答 API"""
    try:
        data = request.get_json()
        input_text = data.get('input_text', '')
        model = data.get('model', 'gpt-5-nano')
        instructions = data.get('instructions', 'You are a helpful assistant.')
        
        if not input_text:
            return jsonify({'error': '缺少 input_text 參數'}), 400
        
        result = ask(input_text, model=model, instructions=instructions)
        return jsonify({
            'success': True,
            'input': input_text,
            'output': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/translate', methods=['POST'])
def api_translate():
    """翻譯 API"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        model = data.get('model', 'gpt-5-nano')
        
        if not text:
            return jsonify({'error': '缺少 text 參數'}), 400
        
        result = translator(text, model=model)
        return jsonify({
            'success': True,
            'original': result['original'],
            'translated': result['translated']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/news-summary', methods=['POST'])
def api_news_summary():
    """新聞 5W1H 摘要 API"""
    try:
        data = request.get_json()
        news_text = data.get('news_text', '')
        model = data.get('model', 'gpt-5-nano')
        
        if not news_text:
            return jsonify({'error': '缺少 news_text 參數'}), 400
        
        result = news_5w1h_summarizer(news_text, model=model)
        return jsonify({
            'success': True,
            'summary': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/create-story', methods=['POST'])
def api_create_story():
    """故事創作 API"""
    try:
        data = request.get_json()
        topic = data.get('topic', '')
        model = data.get('model', 'gpt-5-nano')
        word_count = data.get('word_count', 100)
        instructions = data.get('instructions', 'Tell the story like 村上春樹')
        
        if not topic:
            return jsonify({'error': '缺少 topic 參數'}), 400
        
        result = create_story(topic, model=model, instructions=instructions, word_count=word_count)
        return jsonify({
            'success': True,
            'topic': topic,
            'story': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dispatch', methods=['POST'])
def api_dispatch():
    """智能任務分派 API"""  
    try:
        data = request.get_json()
        user_request = data.get('user_request', '')
        model = data.get('model', 'gpt-5-nano')
        
        if not user_request:
            return jsonify({'error': '缺少 user_request 參數'}), 400
        
        result = task_dispatcher(user_request, model=model)
        return jsonify({
            'success': True,
            'task_type': result['task_type'],
            'result': result['result']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """健康檢查端點"""
    return jsonify({
        'status': 'healthy',
        'service': 'AI Web Service',
        'version': '1.0.0'
    })


@app.route('/api/models', methods=['GET'])
def api_models():
    """Return available models for the OpenAI-based service."""
    try:
        models = []
        try:
            if hasattr(client, 'models'):
                if hasattr(client.models, 'list'):
                    resp = client.models.list()
                    if isinstance(resp, dict) and 'data' in resp:
                        data = resp['data']
                    else:
                        data = resp
                    if isinstance(data, list):
                        for m in data:
                            if isinstance(m, dict) and 'id' in m:
                                models.append(m['id'])
                            elif isinstance(m, str):
                                models.append(m)
                else:
                    resp = client.models()
                    if isinstance(resp, dict) and 'data' in resp:
                        data = resp['data']
                    else:
                        data = resp
                    if isinstance(data, list):
                        for m in data:
                            if isinstance(m, dict) and 'id' in m:
                                models.append(m['id'])
                            elif isinstance(m, str):
                                models.append(m)
        except Exception:
            pass

        if not models:
            models = ["gpt-4.1-mini", "gpt-5-nano", "gpt-5-mini", "gpt-4o-2024-08-06"]

        return jsonify({'success': True, 'models': models})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/service-info', methods=['GET'])
def api_service_info():
    """Return basic service info for the current backend (openai)."""
    try:
        return jsonify({'success': True, 'service': 'openai', 'service_label': 'OpenAI'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== LINE Bot Callback ====================

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_text = event.message.text
    
    try:
        # 使用 task_dispatcher 處理使用者訊息
        # 這裡預設使用 gpt-5-nano，您可以根據需要調整
        result_dict = task_dispatcher(user_text, model="gpt-5-nano")
        
        # 格式化回覆訊息
        reply_text = format_result_for_line(result_dict)
        
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)]
                )
            )
    except Exception as e:
        print(f"Error handling message: {e}")
        # 發生錯誤時，可以選擇回覆錯誤訊息或忽略
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="抱歉，系統發生錯誤，請稍後再試。")]
                )
            )


if __name__ == '__main__':
    PORT = 5001  # 改用 5001 連接埠
    print("=" * 60)
    print("🚀 AI Web Service (with LINE Bot) 啟動中...")
    print("=" * 60)
    print(f"📍 服務位址: http://localhost:{PORT}")
    print(f"📖 API 文件: http://localhost:{PORT}")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=PORT)
