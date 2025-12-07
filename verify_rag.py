from rag_core import RAGSystem
import os

def test_backend():
    print("Initializing RAG System...")
    rag = RAGSystem()
    
    print("Clearing index...")
    print(rag.clear_index())
    
    print("Indexing documents...")
    # Ensure there is at least one file, if not create a dummy one
    if not os.path.exists("rag_data"):
        os.makedirs("rag_data")
    
    if not os.listdir("rag_data"):
        with open("rag_data/test.docx", "w") as f:
            f.write("This is a test document about Artificial Intelligence. AI is simulating human intelligence.")
        print("Created dummy test.docx")

    print(rag.load_and_index())
    
    print("Querying...")
    response = rag.query("What is AI?")
    print(f"Answer: {response['answer']}")
    print(f"Sources: {response['sources']}")

if __name__ == "__main__":
    test_backend()
