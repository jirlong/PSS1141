from flask import Flask, request, abort
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
import os
import requests
import json

app = Flask(__name__)

# LINE Bot 設定
# 請確保您已設定這些環境變數，或直接填入您的 Token 與 Secret
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "YOUR_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "YOUR_CHANNEL_SECRET")

# AI Service 設定
AI_SERVICE_URL = "http://localhost:5002/api/dispatch" # 指向 flask_ollama_app.py 的位址
DEFAULT_MODEL = "gemma3:1b"

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


def call_ai_service(user_text):
    """呼叫後端 AI 服務"""
    try:
        payload = {
            "user_request": user_text,
            "model": DEFAULT_MODEL
        }
        response = requests.post(AI_SERVICE_URL, json=payload)
        response.raise_for_status() # 檢查 HTTP 錯誤
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling AI service: {e}")
        return {"error": str(e)}


def format_result_for_line(task_result):
    """將 AI 服務回傳的 JSON 結果格式化為 LINE 訊息文字"""
    
    # 檢查是否發生錯誤
    if "error" in task_result:
        return f"抱歉，AI 服務暫時無法使用。\n錯誤訊息: {task_result['error']}"

    task_type = task_result.get("task_type")
    result = task_result.get("result")

    if not task_type or not result:
        return "無法解析 AI 回應。"

    if task_type == "translator":
        return f"【翻譯結果】\n原文: {result.get('original', '')}\n\n翻譯: {result.get('translated', '')}"
    
    elif task_type == "news_summarizer":
        # 處理可能的回傳結構差異
        if isinstance(result, dict):
            return (f"【新聞 5W1H 分析】\n"
                    f"Who: {result.get('who', '未提及')}\n"
                    f"What: {result.get('what', '未提及')}\n"
                    f"When: {result.get('when', '未提及')}\n"
                    f"Where: {result.get('where', '未提及')}\n"
                    f"Why: {result.get('why', '未提及')}\n"
                    f"How: {result.get('how', '未提及')}")
        else:
            return str(result)
    
    elif task_type == "story_creator":
        topic = result.get('topic', '未知主題')
        story = result.get('story', '')
        return f"【床邊故事: {topic}】\n\n{story}"
    
    else: # general_question
        return str(result)


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
    
    # 呼叫 AI 服務
    ai_response = call_ai_service(user_text)
    
    # 格式化回應
    reply_text = format_result_for_line(ai_response)
    
    # 回覆 LINE
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )


if __name__ == "__main__":
    PORT = 5003 # 使用不同於 AI Service (5002) 的連接埠
    print("=" * 60)
    print("🤖 LINE Bot Service 啟動中...")
    print("=" * 60)
    print(f"📍 服務位址: http://localhost:{PORT}")
    print(f"🔗 連接 AI 服務: {AI_SERVICE_URL}")
    print("=" * 60)
    app.run(host="0.0.0.0", port=PORT, debug=True)
