"""
Streamlit App for OpenAI API Functions
Based on ai01-using-openAI.py

Run with: streamlit run ai03-app.py
"""

import streamlit as st
import json
from openai import OpenAI
from pydantic import BaseModel

# OpenAI API Key
OPENAI_API_KEY = "your-openai-api-key-here"  # Replace with your actual OpenAI API key

client = OpenAI(api_key=OPENAI_API_KEY)

# ==================== Functions from ai01-using-openAI.py ====================

def ask_question(question, model="gpt-4.1-mini", instructions="You are a helpful assistant.", temperature=0.7):
    """
    General purpose function to ask a question and get a response from OpenAI API.
    """
    response = client.responses.create(
        model=model,
        instructions=instructions,
        input=question,
        temperature=temperature
    )
    return response.output_text


def research_topic(topic, model="gpt-4.1-mini", 
                   instructions="You are a research assistant. Read the user's topic and return a concise summary of recent and reliable information in one paragraph. Include sources when relevant.", 
                   input_template="Can you help me research {topic} and summarize the latest findings?", 
                   temperature=0.0):
    """
    Research a topic and provide a summary.
    """
    response = client.responses.create(
        model=model,
        instructions=instructions,
        input=input_template.format(topic=topic),
        temperature=temperature
    )
    return response.output_text


def translator(text, model="gpt-4.1-mini", temperature=0.3):
    """
    Translate text between Traditional Chinese and English automatically.
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
    
    result = response.output_parsed
    return result.model_dump()


# ==================== Streamlit App ====================

def main():
    st.set_page_config(
        page_title="AI Assistant App",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 AI Assistant Application")
    st.markdown("使用 OpenAI API 進行各種 AI 任務")
    
    # Sidebar for function selection
    st.sidebar.header("選擇功能")
    function_choice = st.sidebar.selectbox(
        "請選擇要使用的功能：",
        [
            "一般問答 (Ask Question)",
            "主題研究 (Research Topic)",
            "翻譯 (Translator)",
            "新聞摘要 5W1H (News Summary)"
        ]
    )
    
    # Model selection
    st.sidebar.header("模型設定")
    
    # Main content area
    st.markdown("---")
    
    if function_choice == "一般問答 (Ask Question)":
        st.header("💬 一般問答")
        st.markdown("向 AI 提出任何問題，獲得回答。")
        
        model = st.sidebar.selectbox(
            "選擇模型：",
            ["gpt-4.1-mini", "gpt-5-nano", "gpt-5-mini", "gpt-4.1-nano"],
            index=0
        )
        temperature = st.sidebar.slider("Temperature (創造力):", 0.0, 1.0, 0.7, 0.1)
        
        question = st.text_area("請輸入您的問題：", height=100, placeholder="例如：什麼是人工智慧？")
        
        if st.button("🚀 提交問題", type="primary"):
            if question:
                with st.spinner("AI 正在思考..."):
                    try:
                        result = ask_question(question, model=model, temperature=temperature)
                        st.success("✅ 回答完成！")
                        st.markdown("### 回答：")
                        st.write(result)
                    except Exception as e:
                        st.error(f"❌ 發生錯誤：{str(e)}")
            else:
                st.warning("⚠️ 請輸入問題！")
    
    elif function_choice == "主題研究 (Research Topic)":
        st.header("🔍 主題研究")
        st.markdown("輸入研究主題，AI 將提供詳細的摘要和資訊。")
        
        model = st.sidebar.selectbox(
            "選擇模型：",
            ["gpt-4.1-mini", "gpt-5-nano", "gpt-5-mini", "gpt-4.1-nano"],
            index=0
        )
        
        topic = st.text_input("請輸入研究主題：", placeholder="例如：Echo chambers in social media")
        
        col1, col2 = st.columns(2)
        with col1:
            custom_instructions = st.checkbox("自訂指示")
        with col2:
            custom_template = st.checkbox("自訂提問模板")
        
        instructions = None
        input_template = None
        
        if custom_instructions:
            instructions = st.text_area(
                "系統指示：",
                value="You are a research assistant. Read the user's topic and return a concise summary of recent and reliable information in one paragraph. Include sources when relevant.",
                height=100
            )
        
        if custom_template:
            input_template = st.text_input(
                "提問模板 (使用 {topic} 作為佔位符)：",
                value="Can you help me research {topic} and summarize the latest findings?"
            )
        
        if st.button("🚀 開始研究", type="primary"):
            if topic:
                with st.spinner("AI 正在研究中..."):
                    try:
                        kwargs = {"topic": topic, "model": model, "temperature": 0.0}
                        if instructions:
                            kwargs["instructions"] = instructions
                        if input_template:
                            kwargs["input_template"] = input_template
                        
                        result = research_topic(**kwargs)
                        st.success("✅ 研究完成！")
                        st.markdown("### 研究結果：")
                        st.write(result)
                    except Exception as e:
                        st.error(f"❌ 發生錯誤：{str(e)}")
            else:
                st.warning("⚠️ 請輸入研究主題！")
    
    elif function_choice == "翻譯 (Translator)":
        st.header("🌐 翻譯")
        st.markdown("自動偵測語言並進行中英文互譯。")
        
        model = st.sidebar.selectbox(
            "選擇模型：",
            ["gpt-4.1-mini", "gpt-5-nano", "gpt-5-mini", "gpt-4.1-nano"],
            index=0
        )
        temperature = st.sidebar.slider("Temperature:", 0.0, 1.0, 0.3, 0.1)
        
        text = st.text_area("請輸入要翻譯的文字：", height=150, placeholder="例如：Hello, how are you today?")
        
        if st.button("🚀 開始翻譯", type="primary"):
            if text:
                with st.spinner("翻譯中..."):
                    try:
                        result = translator(text, model=model, temperature=temperature)
                        st.success("✅ 翻譯完成！")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("### 原文：")
                            st.info(text)
                        with col2:
                            st.markdown("### 譯文：")
                            st.success(result)
                    except Exception as e:
                        st.error(f"❌ 發生錯誤：{str(e)}")
            else:
                st.warning("⚠️ 請輸入要翻譯的文字！")
    
    elif function_choice == "新聞摘要 5W1H (News Summary)":
        st.header("📰 新聞摘要 5W1H")
        st.markdown("提取新聞中的 5W1H 資訊（Who, What, When, Where, Why, How）")
        
        st.sidebar.info("此功能使用 gpt-4o-2024-08-06 模型以支援結構化輸出")
        temperature = st.sidebar.slider("Temperature:", 0.0, 1.0, 0.2, 0.1)
        
        news_text = st.text_area(
            "請輸入新聞內容：",
            height=200,
            placeholder="例如：Tesla CEO Elon Musk announced on Tuesday that the company will open a new Gigafactory in Austin, Texas next month..."
        )
        
        if st.button("🚀 開始分析", type="primary"):
            if news_text:
                with st.spinner("分析中..."):
                    try:
                        result = news_5w1h_summarize(news_text, temperature=temperature)
                        st.success("✅ 分析完成！")
                        
                        st.markdown("### 5W1H 分析結果：")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**👤 Who (誰):**")
                            st.info(result['who'])
                            
                            st.markdown("**📅 When (何時):**")
                            st.info(result['when'])
                            
                            st.markdown("**❓ Why (為何):**")
                            st.info(result['why'])
                        
                        with col2:
                            st.markdown("**📝 What (什麼):**")
                            st.info(result['what'])
                            
                            st.markdown("**📍 Where (何地):**")
                            st.info(result['where'])
                            
                            st.markdown("**🔧 How (如何):**")
                            st.info(result['how'])
                        
                        # JSON output
                        with st.expander("查看 JSON 格式"):
                            st.json(result)
                            
                    except Exception as e:
                        st.error(f"❌ 發生錯誤：{str(e)}")
            else:
                st.warning("⚠️ 請輸入新聞內容！")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
        Built with Streamlit and OpenAI API | 2025
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
