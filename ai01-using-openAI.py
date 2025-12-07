"""
Allowed models for OpenAI API interactions
- gpt-4.1-mini
- gpt-5-nano
- gpt-5-mini (Good balance between speed and capability)
- gpt-4.1-nano

Visit quick start guide at: https://platform.openai.com/docs/quickstart

"""




# get api key from environment variable
# OPENAI_API_KEY="your-openai-api-key-here"  # Replace with your actual OpenAI API key
import os 
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # OR, get from environment variable if set

from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

"""
Basic example
"""

# response = client.responses.create(
#     model="gpt-4.1-mini",
#     instructions="You are a research assistant. Read the user's topic and return a concise summary of recent and reliable information in one paragraph. Include sources when relevant.",
#     input="Can you help me research filter bubble and summarize the latest findings?",
#     temperature=0.0     # Creativity level (0.0 = least creative, 1.0 = most creative)
#                         # Temperature is not supported for gpt-5x models
                        

#     # The example above is roughly equivalent to using the following input messages in the array:                        
#     # input=[
#     #     {
#     #         "role": "developer",
#     #         "content": "You are a helpful assistant that writes bedtime stories for children."
#     #     },
#     #     {
#     #         "role": "user",
#     #         "content": "Write a 5-sentence bedtime story about a unicorn."
#     #     }
#     # ]
# )

# print(response.output_text)



"""
Ask with placeholder example
"""
# topic = "filter bubble"
# response = client.responses.create(
#     model="gpt-4.1-mini",
#     instructions="You are a research assistant. Read the user's topic and return a concise summary of recent and reliable information in one paragraph. Include sources when relevant.",
#     input=f"Can you help me research {topic} and summarize the latest findings?",
#     temperature=0.0
# )

# print(response.output_text)



"""
Wrap up example to a function
"""
def research_topic(topic, model="gpt-4.1-mini", 
                   instructions="You are a research assistant. Read the user's topic and return a concise summary of recent and reliable information in one paragraph. Include sources when relevant.", 
                   input_template="Can you help me research {topic} and summarize the latest findings?", 
                   temperature=0.0):
    response = client.responses.create(
        model=model,
        instructions=instructions,
        input=input_template.format(topic=topic),
        temperature=temperature
    )
    return response.output_text

# Example usage
# result = research_topic("Echo chambers in social media")
# print(result)
 
 
"""
General purpose function - ask question and get response
"""
def ask_question(question, model="gpt-4.1-mini", instructions="You are a helpful assistant.", temperature=0.7):
    """
    General purpose function to ask a question and get a response from OpenAI API.
    
    Args:
        question (str): The question or prompt to send to the AI
        model (str): The OpenAI model to use (default: "gpt-4.1-mini")
        instructions (str): System instructions for the AI (default: "You are a helpful assistant.")
        temperature (float): Creativity level 0.0-1.0 (default: 0.7)
    
    Returns:
        str: The AI's response
    """
    response = client.responses.create(
        model=model,
        instructions=instructions,
        input=question,
        temperature=temperature
    )
    return response.output_text

# Example usage
# answer = ask_question("What is the capital of France?")
# print(answer) 
 
 
"""
Translator function - translate between Chinese and English
"""
def translator(text, model="gpt-4.1-mini", temperature=0.3):
    def _ask(text, model="gpt-4.1-mini", temperature=0.3):
        """
        Translate text between Traditional Chinese and English automatically.
        If input is Traditional Chinese, translate to English. If input is English, translate to Traditional Chinese.
        
        Args:
            text (str): The text to translate (Traditional Chinese or English)
            model (str): The OpenAI model to use (default: "gpt-4.1-mini")
            temperature (float): Creativity level 0.0-1.0 (default: 0.3)
        
        Returns:
            str: Formatted output with original text and translated text
        """
        instructions = """You are a professional translator. 
        If the input is in Traditional Chinese, translate it to English.
        If the input is in English, translate it to Traditional Chinese.
        
        Please structure your response in exactly this format:
        [translated text here]"""
        
        response = client.responses.create(
            model=model,
            instructions=instructions,
            input=text,
            temperature=temperature
        )
        return response.output_text
    result = _ask(text, model=model, temperature=temperature)
    print(text)
    print(result)
    return result

# Example usage
# result1 = translator("Hello, how are you today?")
# 
# print("\n" + "="*50 + "\n")

# result2 = translator("你好,今天天氣很好")


"""
News 5W1H summarization example
"""
import json
from pydantic import BaseModel

class News5W1H(BaseModel):
    who: str
    what: str
    when: str
    where: str
    why: str
    how: str

def news_5w1h_summarize(news_text, model="gpt-4.1-mini", temperature=0.2):
    """
    Extract 5W1H (Who, What, When, Where, Why, How) from news text with structured output.
    
    Args:
        news_text (str): The news article text to analyze
        model (str): The OpenAI model to use (default: "gpt-4o-2024-08-06")
        temperature (float): Creativity level 0.0-1.0 (default: 0.2)
    
    Returns:
        dict: A dictionary containing 5W1H information
    """
    
    response = client.responses.parse(
        model=model,
        input=[
            {
                "role": "system",
                "content": """You are a professional news analyst. Extract the 5W1H information from the given news article.
                Analyze carefully and provide concise but complete information for each element:
                - who: Main people, organizations, or entities involved
                - what: The main event or action that occurred
                - when: Time information (date, time, or period)
                - where: Location or place where the event occurred
                - why: Reasons, causes, or motivations behind the event
                - how: Methods, processes, or manner in which it happened
                
                If any information is not explicitly mentioned in the text, write "Not specified" for that field."""
            },
            {
                "role": "user",
                "content": news_text
            }
        ],
        temperature=temperature,
        text_format=News5W1H
    )
    
    # Get the parsed output
    result = response.output_parsed
    return result.model_dump()

# Example usage
sample_news = """
Tesla CEO Elon Musk announced on Tuesday that the company will open a new Gigafactory 
in Austin, Texas next month. The facility will manufacture electric vehicles and battery 
packs to meet growing demand in North America. Musk explained that the decision was made 
to reduce logistics costs and improve delivery times for customers in the region. The 
factory will employ over 5,000 workers and use advanced automation technology.
"""

# result = news_5w1h_summarize(sample_news)
# print(json.dumps(result, indent=2, ensure_ascii=False))


"""
Task dispatcher
"""
def task_dispatcher(user_request):
    """
    Intelligent task dispatcher that analyzes user request and routes to appropriate function.
    
    Args:
        user_request (str): The user's request in natural language
    
    Returns:
        str: The result from the appropriate function
    """
    # Use ask_question to classify the task
    classification_prompt = f"""Analyze the following user request and determine which function should handle it.

User request: "{user_request}"

Available functions:
1. translator - For translation requests between Chinese and English (keywords: 翻譯, translate, 中文, 英文, English, Chinese)
2. news_5w1h_summarize - For news analysis and extracting 5W1H information (keywords: 新聞, news, 5W1H, 分析, analyze, 摘要, summarize)
3. research_topic - For research and information gathering on topics (keywords: 研究, research, 查詢, 調查, investigate, 資料, information)
4. ask_question - For general questions and conversations (default for everything else)

Respond with ONLY the function name, nothing else."""

    function_name = ask_question(
        classification_prompt, 
        model="gpt-4.1-mini",
        instructions="You are a task classifier. Return only the function name.",
        temperature=0.0
    ).strip()
    
    print(f"🔍 Detected function: {function_name}")
    print(f"📝 Processing request: {user_request}\n")
    
    # Route to appropriate function
    if "translator" in function_name.lower():
        return translator(user_request)
    
    elif "news_5w1h_summarize" in function_name.lower():
        result = news_5w1h_summarize(user_request)
        return json.dumps(result, indent=2, ensure_ascii=False)
    
    elif "research_topic" in function_name.lower():
        # Extract topic from request
        topic_prompt = f"Extract the main topic to research from this request: '{user_request}'. Return only the topic, nothing else."
        topic = ask_question(topic_prompt, temperature=0.0).strip()
        return research_topic(topic)
    
    else:  # Default to ask_question
        return ask_question(user_request)

# Example usage
print("="*60)
print("Example 1: Translation request")
print("="*60)
result1 = task_dispatcher("請幫我翻譯 Hello World")
print()

print("="*60)
print("Example 2: General question")
print("="*60)
result2 = task_dispatcher("What is the capital of Japan?")
print(result2)
print()

print("="*60)
print("Example 3: Research request")
print("="*60)
result3 = task_dispatcher("Can you research artificial intelligence for me?")
print(result3)


print("="*60)
print("Example 4: News summary request")
print("="*60)
result4 = task_dispatcher(f"請摘要這篇新聞:{sample_news}")
print(result4)