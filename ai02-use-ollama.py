import ollama

def ask_question(question, model='gemma3:12b'):
    """
    General purpose function to ask a question and get a response from Ollama.
    
    Args:
        question (str): The question or prompt to send to the AI
        model (str): The Ollama model to use (default: 'gemma3:12b')
    
    Returns:
        str: The AI's response
    """
    try:
        response = ollama.chat(
            model=model,
            messages=[
                {'role': 'user', 'content': question}
            ]
        )
        return response['message']['content']
    except Exception as e:
        print("Chat failed:", e)
        return None


def translator(text, model='gemma3:12b'):
    """
    Translate text between Traditional Chinese and English automatically.
    If input is Traditional Chinese, translate to English. If input is English, translate to Traditional Chinese.
    
    Args:
        text (str): The text to translate (Traditional Chinese or English)
        model (str): The Ollama model to use (default: 'gemma3:12b')
    
    Returns:
        str: The translated text
    """
    instructions = """You are a professional translator. 
    If the input is in Traditional Chinese, translate it to English.
    If the input is in English, translate it to Traditional Chinese.
    
    Please structure your response in exactly this format:
    [translated text here]"""
    
    try:
        response = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": text}
            ]
        )
        result = response['message']['content']
        print(text)
        print(result)
        return result
    except Exception as e:
        print("Translation failed:", e)
        return None


def research_topic(topic, model='gemma3:12b', instructions="You are a research assistant. Read the user's topic and return a concise summary of recent and reliable information in one paragraph. Include sources when relevant.", input_template="Can you help me research {topic} and summarize the latest findings?"):
    """
    Research a topic and provide a summary.
    
    Args:
        topic (str): The topic to research
        model (str): The Ollama model to use (default: 'gemma3:12b')
        instructions (str): System instructions for the research assistant
        input_template (str): Template for the user input
    
    Returns:
        str: The AI's response
    """
    messages = [
        {"role": "system", "content": instructions},
        {"role": "user", "content": input_template.format(topic=topic)}
    ]
    
    try:
        response = ollama.chat(model=model, messages=messages)
        return response['message']['content']
    except Exception as e:
        print("Research failed:", e)
        return None


def main():
    # Example 1: Simple question
    print("== Example 1: ask_question ==")
    answer = ask_question('日本的首都在哪裡（簡答）？')
    print("Chat output:\n", answer)
    print()
    
    # Example 2: Research topic
    print("== Example 2: research_topic ==")
    result = research_topic("Echo chambers in social media")
    print("Research output:\n", result)
    print()
    
    # Example 3: Translator
    print("== Example 3: translator ==")
    print("\nTranslating English to Chinese:")
    translator("Hello, how are you today?")
    print("\nTranslating Chinese to English:")
    translator("你好,今天天氣很好")


if __name__ == "__main__":
    main()
