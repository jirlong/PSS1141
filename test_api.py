"""
測試 AI Web Service API 的範例程式
"""

import requests
import json

# API 基礎 URL (使用 5001 連接埠避免衝突)
BASE_URL = "http://localhost:5001"


def test_ask():
    """測試一般問答 API"""
    print("\n" + "=" * 60)
    print("測試 1: 一般問答 API")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/ask"
    data = {
        "input_text": "什麼是人工智慧?",
        "model": "gpt-5-nano"
    }
    
    response = requests.post(url, json=data)
    result = response.json()
    
    print(f"問題: {data['input_text']}")
    print(f"回答: {result.get('output', result.get('error'))}")


def test_translate():
    """測試翻譯 API"""
    print("\n" + "=" * 60)
    print("測試 2: 翻譯 API")
    print("=" * 60)
    
    # 測試英翻中
    url = f"{BASE_URL}/api/translate"
    data = {
        "text": "Hello, how are you today?",
        "model": "gpt-5-nano"
    }
    
    response = requests.post(url, json=data)
    result = response.json()
    
    print(f"原文: {result.get('original')}")
    print(f"譯文: {result.get('translated')}")
    
    # 測試中翻英
    data2 = {
        "text": "你好，今天天氣很好",
        "model": "gpt-5-nano"
    }
    
    response2 = requests.post(url, json=data2)
    result2 = response2.json()
    
    print(f"\n原文: {result2.get('original')}")
    print(f"譯文: {result2.get('translated')}")


def test_news_summary():
    """測試新聞摘要 API"""
    print("\n" + "=" * 60)
    print("測試 3: 新聞摘要 API")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/news-summary"
    data = {
        "news_text": """
        台北市長蔣萬安今天(17日)上午在市政府宣布,台北市將在明年1月開始實施新的垃圾減量政策。
        這項政策是為了因應日益嚴重的垃圾問題,透過提高垃圾處理費和加強資源回收來達成減量目標。
        市府預計透過這項措施,在未來三年內將垃圾量減少30%。
        """,
        "model": "gpt-5-nano"
    }
    
    response = requests.post(url, json=data)
    result = response.json()
    
    print("新聞 5W1H 摘要:")
    print(json.dumps(result.get('summary', result.get('error')), indent=2, ensure_ascii=False))


def test_create_story():
    """測試故事創作 API"""
    print("\n" + "=" * 60)
    print("測試 4: 故事創作 API")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/create-story"
    data = {
        "topic": "友誼",
        "word_count": 100,
        "model": "gpt-5-nano"
    }
    
    response = requests.post(url, json=data)
    result = response.json()
    
    print(f"主題: {result.get('topic')}")
    print(f"故事:\n{result.get('story', result.get('error'))}")


def test_dispatch():
    """測試任務分派器 API"""
    print("\n" + "=" * 60)
    print("測試 5: 任務分派器 API")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/dispatch"
    
    # 測試翻譯任務
    test_cases = [
        "請幫我翻譯: Hello World",
        "請分析這則新聞: 台北市長今天宣布新政策",
        "請寫一個關於勇氣的故事",
        "什麼是機器學習?"
    ]
    
    for user_request in test_cases:
        data = {
            "user_request": user_request,
            "model": "gpt-5-nano"
        }
        
        response = requests.post(url, json=data)
        result = response.json()
        
        print(f"\n請求: {user_request}")
        print(f"任務類型: {result.get('task_type')}")
        print(f"結果: {json.dumps(result.get('result'), ensure_ascii=False)[:200]}...")


def test_health():
    """測試健康檢查 API"""
    print("\n" + "=" * 60)
    print("測試: 健康檢查")
    print("=" * 60)
    
    url = f"{BASE_URL}/health"
    response = requests.get(url)
    result = response.json()
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 AI Web Service API 測試")
    print("=" * 60)
    print("⚠️  請確保 Flask 服務已經啟動 (python ai03-app.py)")
    print("=" * 60)
    
    try:
        # 測試健康檢查
        test_health()
        
        # 測試各個 API
        test_ask()
        test_translate()
        test_news_summary()
        test_create_story()
        test_dispatch()
        
        print("\n" + "=" * 60)
        print("✅ 所有測試完成!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 錯誤: 無法連接到服務")
        print("請確保 Flask 服務已經啟動:")
        print("  python ai03-app.py")
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {str(e)}")
