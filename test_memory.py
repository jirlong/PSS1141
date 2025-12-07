import sys
import os

# Add the current directory to sys.path so we can import rag_ollama
sys.path.append(os.getcwd())

from rag_ollama import RAGOllamaApp

def test_memory():
    print("Initializing RAG App...")
    app = RAGOllamaApp()
    
    # Mock history
    history = [
        ("human", "My name is Jirlong."),
        ("ai", "Hello Jirlong! How can I help you today?")
    ]
    
    print("\n--- Testing Query with History ---")
    question = "What is my name?"
    print(f"Question: {question}")
    print(f"History: {history}")
    
    # We expect the model to know the name from history, even if it's not in the documents.
    # Note: The system prompt instructs to use *retrieved context*. 
    # If the model follows instructions strictly, it might say "I don't know" if it's not in the docs.
    # However, usually models will pick up on the conversation history.
    # Let's see how it behaves. If it fails, we might need to adjust the system prompt 
    # to allow using conversation history as context as well.
    
    try:
        result = app.query(question, history=history)
        print(f"\nAnswer: {result['answer']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_memory()
