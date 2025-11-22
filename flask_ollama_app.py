from flask import Flask, request, jsonify, render_template
import ollama
import json
import re

app = Flask(__name__)

# ==================== Ollama-based helper functions (adapted from ai02-use-ollama.py) ====================

def ask(input_text, model="gemma3:1b", instructions="You are a helpful assistant."):
    """通用問答 (使用 Ollama)"""
    messages = [
        {"role": "system", "content": instructions},
        {"role": "user", "content": input_text},
    ]
    resp = ollama.chat(model=model, messages=messages)
    return resp.get("message", {}).get("content")


def translator(text, model="gemma3:1b"):
    """翻譯 (使用 Ollama) - 回傳原文與譯文"""
    instructions = ("You are a professional translator.\n"
                    "If the input text is in Traditional Chinese (繁體中文), translate it to English.\n"
                    "If the input text is in English, translate it to Traditional Chinese (繁體中文).\n"
                    "Only return the translated text, nothing else.")
    messages = [
        {"role": "system", "content": instructions},
        {"role": "user", "content": text},
    ]
    resp = ollama.chat(model=model, messages=messages)
    translated = resp.get("message", {}).get("content")
    return {"original": text, "translated": translated}


def news_5w1h_summarizer(news_text, model="gemma3:1b"):
    """使用 Ollama 提取 5W1H，並嘗試解析回傳的 JSON。"""
    system_prompt = (
        "你是一位專業的新聞分析師。請從新聞內容中提取 5W1H 資訊，並以 JSON 格式回傳。" 
        "結果格式範例：{" + '"who": "...", "what": "...", "when": "...", "where": "...", "why": "...", "how": "..."' + "}." 
        "請用繁體中文填值，如果某項資訊未提及，請填寫「未提及」。"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": news_text}
    ]
    resp = ollama.chat(model=model, messages=messages)
    content = resp.get("message", {}).get("content", "")

    # Try to parse JSON directly
    try:
        parsed = json.loads(content)
        return parsed
    except Exception:
        # Try to extract JSON substring using regex
        m = re.search(r"\{[\s\S]*\}", content)
        if m:
            try:
                parsed = json.loads(m.group(0))
                return parsed
            except Exception:
                pass
    # Fallback: return content as 'raw' field and mark other fields as '未提及'
    return {
        "who": "未提及",
        "what": "未提及",
        "when": "未提及",
        "where": "未提及",
        "why": "未提及",
        "how": "未提及",
        "raw": content
    }


def create_story(topic, model="gemma3:1b", instructions="Tell the story like 村上春樹", word_count=100):
    prompt = f"寫一個跟 {topic} 有關的床邊故事，約 {word_count} 字的段落。請用中文。"
    messages = [
        {"role": "system", "content": instructions},
        {"role": "user", "content": prompt}
    ]
    resp = ollama.chat(model=model, messages=messages)
    return resp.get("message", {}).get("content")


def task_dispatcher(user_request, model="gemma3:1b"):
    """簡單的任務分派器，使用 ask 進行分類並呼叫對應函式"""
    classification_prompt = f"分析以下使用者請求並回傳要使用的函式名稱：translator, news_summarizer, story_creator, general_question\n使用者請求: {user_request}"
    function_name = ask(classification_prompt, model=model, instructions="You are a task classifier. Return only the function name.").strip().lower()

    if "translator" in function_name:
        # Extract text to translate
        extract_prompt = f"從以下請求中提取需要翻譯的文字內容, 只回傳要翻譯的文字:\n{user_request}"
        text_to_translate = ask(extract_prompt, model=model, instructions="Extract only the text to translate.")
        return {"task_type": "translator", "result": translator(text_to_translate, model=model)}
    elif "news" in function_name or "news_summarizer" in function_name:
        extract_prompt = f"從以下請求中提取新聞內容文字, 只回傳新聞文字本身:\n{user_request}"
        news_content = ask(extract_prompt, model=model, instructions="Extract only the news content.")
        return {"task_type": "news_summarizer", "result": news_5w1h_summarizer(news_content, model=model)}
    elif "story" in function_name or "story_creator" in function_name:
        extract_prompt = f"從以下請求中提取故事主題, 只回傳主題關鍵詞:\n{user_request}"
        topic = ask(extract_prompt, model=model, instructions="Extract only the story topic.")
        return {"task_type": "story_creator", "result": {"topic": topic, "story": create_story(topic, model=model)}}
    else:
        return {"task_type": "general_question", "result": ask(user_request, model=model)}


# ==================== Web Service API Endpoints (Flask) ====================

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/ask', methods=['POST'])
def api_ask():
    try:
        data = request.get_json()
        input_text = data.get('input_text', '')
        model = data.get('model', 'gemma3:1b')
        instructions = data.get('instructions', 'You are a helpful assistant.')

        if not input_text:
            return jsonify({'error': '缺少 input_text 參數'}), 400

        result = ask(input_text, model=model, instructions=instructions)
        return jsonify({'success': True, 'input': input_text, 'output': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/translate', methods=['POST'])
def api_translate():
    try:
        data = request.get_json()
        text = data.get('text', '')
        model = data.get('model', 'gemma3:1b')

        if not text:
            return jsonify({'error': '缺少 text 參數'}), 400

        result = translator(text, model=model)
        return jsonify({'success': True, 'original': result['original'], 'translated': result['translated']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/news-summary', methods=['POST'])
def api_news_summary():
    try:
        data = request.get_json()
        news_text = data.get('news_text', '')
        model = data.get('model', 'gemma3:1b')

        if not news_text:
            return jsonify({'error': '缺少 news_text 參數'}), 400

        result = news_5w1h_summarizer(news_text, model=model)
        return jsonify({'success': True, 'summary': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/create-story', methods=['POST'])
def api_create_story():
    try:
        data = request.get_json()
        topic = data.get('topic', '')
        model = data.get('model', 'gemma3:1b')
        word_count = data.get('word_count', 100)
        instructions = data.get('instructions', 'Tell the story like 村上春樹')

        if not topic:
            return jsonify({'error': '缺少 topic 參數'}), 400

        result = create_story(topic, model=model, instructions=instructions, word_count=word_count)
        return jsonify({'success': True, 'topic': topic, 'story': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dispatch', methods=['POST'])
def api_dispatch():
    try:
        data = request.get_json()
        user_request = data.get('user_request', '')
        model = data.get('model', 'gemma3:1b')

        if not user_request:
            return jsonify({'error': '缺少 user_request 參數'}), 400

        result = task_dispatcher(user_request, model=model)
        return jsonify({'success': True, 'task_type': result['task_type'], 'result': result['result']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'Ollama AI Web Service', 'version': '1.0.0'})


@app.route('/api/models', methods=['GET'])
def api_models():
    """Return available models for this Ollama-based service.
    Attempts to query the `ollama` client for available models; falls back to a sensible default list.
    """
    try:
        models = []
        try:
            if hasattr(ollama, 'models'):
                resp = ollama.models()
                # resp might be a list of model names or dicts
                if isinstance(resp, list):
                    for m in resp:
                        if isinstance(m, dict) and 'name' in m:
                            models.append(m['name'])
                        elif isinstance(m, str):
                            models.append(m)
        except Exception:
            # ignore and fallback
            pass

        if not models:
            models = ['gemma3:1b', 'gemma3:12b']

        return jsonify({'success': True, 'models': models})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/service-info', methods=['GET'])
def api_service_info():
    """Return basic service info for the current backend (ollama)."""
    try:
        return jsonify({'success': True, 'service': 'ollama', 'service_label': 'Ollama'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    PORT = 5002
    print('=' * 60)
    print('🚀 Ollama AI Web Service 啟動中...')
    print('=' * 60)
    print(f'📍 服務位址: http://localhost:{PORT}')
    print('=' * 60)
    app.run(debug=True, host='0.0.0.0', port=PORT)
