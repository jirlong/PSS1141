from openai import OpenAI
from pydantic import BaseModel
import json

OPENAI_API_KEY = ""
client = OpenAI(api_key=OPENAI_API_KEY)


# 定義 5W1H 的 JSON Schema
class News5W1H(BaseModel):
    who: str      # 誰 - 新聞主角
    what: str     # 什麼事 - 發生的事件
    when: str     # 何時 - 時間
    where: str    # 何地 - 地點
    why: str      # 為何 - 原因
    how: str      # 如何 - 方法或過程


def ask(input_text, model="gpt-5-nano", instructions="You are a helpful assistant."):
    """
    通用的問答函式
    
    參數:
        input_text (str): 輸入的問題或提示
        model (str): 使用的模型,預設為 "gpt-5-nano"
        instructions (str): 系統指示,預設為 "You are a helpful assistant."
    
    回傳:
        str: AI 的回應
    """
    response = client.responses.create(
        model=model,
        instructions=instructions,
        input=input_text
    )
    return response.output_text


def news_5w1h_summarizer(news_text, model="gpt-5-nano"):
    """
    新聞 5W1H 摘要函式
    從新聞內容中提取 Who, What, When, Where, Why, How 資訊
    
    參數:
        news_text (str): 新聞內容文字
        model (str): 使用的模型,預設為 "gpt-4o-2024-08-06" (支援 structured output)
    
    回傳:
        dict: 包含 5W1H 資訊的字典
    """
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
    
    # 取得結構化的輸出
    result = response.output_parsed
    return result.model_dump()


def translator(text, model="gpt-5-nano"):
    """
    智能翻譯函式:自動判斷語言並翻譯
    - 輸入繁體中文 → 翻譯成英文
    - 輸入英文 → 翻譯成繁體中文
    
    參數:
        text (str): 要翻譯的文字
        model (str): 使用的模型,預設為 "gpt-5-nano"
    
    回傳:
        str: 翻譯結果
    """
    def _ask(text, model="gpt-5-nano"):
        instructions = """You are a professional translator.
        If the input text is in Traditional Chinese (繁體中文), translate it to English.
        If the input text is in English, translate it to Traditional Chinese (繁體中文).
        Only return the translated text, nothing else."""
        
        response = client.responses.create(
            model=model,
            instructions=instructions,
            input=text
        )
        return response.output_text
    translated_text = _ask(text, model=model)
    return {"original": text, "translated": translated_text}

    
def create_story(topic, model="gpt-5-nano", 
                 instructions="Tell the story like 村上春樹", 
                 word_count=100):
    """
    根據主題創作床邊故事
    
    參數:
        topic (str): 故事主題
        model (str): 使用的模型,預設為 "gpt-5-nano"
        instructions (str): 寫作風格指示,預設為 "Tell the story like 村上春樹"
        word_count (int): 故事字數,預設為 100
    
    回傳:
        str: 生成的故事內容
    """
    response = client.responses.create(
        model=model,
        instructions=instructions,
        input=f"寫一個跟{topic}有關的床邊故事，近{word_count}字的段落即可"
    )
    return response.output_text


def task_dispatcher(user_request, model="gpt-5-nano"):
    """
    任務分派器:根據使用者請求自動分派到適當的函式
    
    支援的任務類型:
    1. translator - 翻譯任務
    2. news_summarizer - 新聞摘要(5W1H)
    3. story_creator - 故事創作
    4. general_question - 一般問答
    
    參數:
        user_request (str): 使用者的請求內容
        model (str): 使用的模型,預設為 "gpt-5-nano"
    
    回傳:
        根據任務類型回傳不同格式的結果
    """
    # 使用 AI 判斷任務類型
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
    
    print(f"🔍 偵測到的任務類型: {function_name}")
    print(f"📝 處理請求: {user_request}")
    print("-" * 60)
    
    # 根據判斷結果分派任務
    if "translator" in function_name:
        # 提取要翻譯的文字
        extract_prompt = f"從以下請求中提取需要翻譯的文字內容,只回傳要翻譯的文字:\n{user_request}"
        text_to_translate = ask(extract_prompt, model=model, instructions="Extract only the text to translate.").strip()
        result = translator(text_to_translate, model=model)
        print(f"原文: {result['original']}")
        print(f"譯文: {result['translated']}")
        return result
    
    elif "news_summarizer" in function_name or "news" in function_name:
        # 提取新聞內容
        extract_prompt = f"從以下請求中提取新聞內容文字,只回傳新聞文字本身:\n{user_request}"
        news_content = ask(extract_prompt, model=model, instructions="Extract only the news content.").strip()
        result = news_5w1h_summarizer(news_content, model=model)
        print("新聞 5W1H 摘要:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result
    
    elif "story" in function_name:
        # 提取故事主題
        extract_prompt = f"從以下請求中提取故事主題,只回傳主題關鍵詞:\n{user_request}"
        topic = ask(extract_prompt, model=model, instructions="Extract only the story topic.").strip()
        result = create_story(topic, model=model)
        print(f"故事主題: {topic}")
        print(f"故事內容:\n{result}")
        return result
    
    else:  # general_question
        result = ask(user_request, model=model)
        print(f"回答: {result}")
        return result


# 使用範例
if __name__ == "__main__":
    print("=" * 60)
    print("任務分派器測試")
    print("=" * 60)
    print()
    
    # 測試 1: 翻譯任務
    print("【測試 1】翻譯任務")
    task_dispatcher("請幫我翻譯: Hello, how are you today?")
    print("\n" + "=" * 60 + "\n")
    
    # 測試 2: 新聞摘要任務
    print("【測試 2】新聞摘要任務")
    task_dispatcher("""請分析這則新聞的5W1H:
    台北市長蔣萬安今天(17日)上午在市政府宣布,台北市將在明年1月開始實施新的垃圾減量政策。
    這項政策是為了因應日益嚴重的垃圾問題,透過提高垃圾處理費和加強資源回收來達成減量目標。
    市府預計透過這項措施,在未來三年內將垃圾量減少30%。
    """)
    print("\n" + "=" * 60 + "\n")
    
    # 測試 3: 故事創作任務
    print("【測試 3】故事創作任務")
    task_dispatcher("請寫一個關於友誼的床邊故事")
    print("\n" + "=" * 60 + "\n")
    
    # 測試 4: 一般問答任務
    print("【測試 4】一般問答任務")
    task_dispatcher("什麼是人工智慧?")
    print("\n" + "=" * 60 + "\n")