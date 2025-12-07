import os
import sys
import argparse
import shutil
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_ollama import ChatOllama
from langchain_chroma import Chroma
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# Configuration
DATA_DIR = "rag_data"
DB_PATH = "rag_data/chroma_db"
MODEL_NAME = "gemma3:12b"
EMBEDDING_MODEL = "all-minilm"

class RAGOllamaApp:
    def __init__(self, data_dir=DATA_DIR, db_path=DB_PATH, model_name=MODEL_NAME, embedding_model=EMBEDDING_MODEL):
        self.data_dir = data_dir
        self.db_path = db_path
        self.model_name = model_name
        self.embedding_model = embedding_model
        self.embeddings = OllamaEmbeddings(model=embedding_model, base_url="http://localhost:11434")
        self.vector_store = None
        self.documents = None

    def clear_database(self):
        """Clear the existing vector store."""
        self.vector_store = None
        if os.path.exists(self.db_path):
            try:
                shutil.rmtree(self.db_path)
                print(f"Database at {self.db_path} has been cleared.")
            except Exception as e:
                print(f"Error clearing database: {e}")
        else:
            print("No database found to clear.")

    def load_documents(self):
        """Load all supported documents from the data directory."""
        documents = []
        if not os.path.exists(self.data_dir):
            print(f"Data directory {self.data_dir} not found.")
            return []

        for filename in os.listdir(self.data_dir):
            file_path = os.path.join(self.data_dir, filename)
            if filename.endswith(".pdf"):
                print(f"Loading PDF: {filename}...")
                loader = PyPDFLoader(file_path)
                documents.extend(loader.load())
            elif filename.endswith(".docx"):
                print(f"Loading DOCX: {filename}...")
                loader = Docx2txtLoader(file_path)
                documents.extend(loader.load())
        
        self.documents = documents
        return documents

    def initialize_vector_store(self):
        """Check if vector store exists, if not, create it from documents."""
        if os.path.exists(self.db_path) and os.listdir(self.db_path):
            print(f"Loading existing vector store from {self.db_path}...")
            self.vector_store = Chroma(persist_directory=self.db_path, embedding_function=self.embeddings)
        else:
            print(f"Creating new vector store from {self.data_dir}...")
            
            # 1. Load Documents
            docs = self.load_documents()
            if not docs:
                print("No documents found to index.")
                return

            print(f"Loaded {len(docs)} document chunks/pages.")

            # 2. Split Text
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            splits = text_splitter.split_documents(docs)
            print(f"Split into {len(splits)} chunks.")

            # 3. Create Vector Store
            self.vector_store = Chroma.from_documents(
                documents=splits, 
                embedding=self.embeddings, 
                persist_directory=self.db_path
            )
            print("Vector store created and persisted.")

    def get_page_content(self, page_numbers):
        """Retrieve content for specific pages (1-indexed).
        Note: This works best for PDFs where 'page' metadata exists.
        For DOCX, it might treat the whole doc as one 'page' or index differently.
        """
        if not self.documents:
            print("Loading documents for lookup...")
            self.load_documents()
        
        results = {}
        # Create a map of page number to document content
        # This assumes self.documents is a flat list of pages/chunks with metadata
        
        # Filter for documents that actually have page numbers (PDFs)
        # or map index to "page" for others if needed.
        # For now, we'll stick to the existing logic but handle missing 'page' metadata
        
        page_map = {}
        for i, doc in enumerate(self.documents):
            # Try to get page number from metadata, default to list index + 1 if missing
            p_num = doc.metadata.get("page", i)
            if isinstance(p_num, int):
                p_num += 1 # 0-indexed to 1-indexed
            page_map[p_num] = doc.page_content

        for page_num in page_numbers:
            if page_num in page_map:
                results[page_num] = page_map[page_num]
            else:
                results[page_num] = f"Page/Chunk {page_num} not found."
        return results

    def summarize_text(self, text):
        """Summarize and translate text to Traditional Chinese."""
        prompt = (
            "You are a helpful assistant. Please translate the following text to "
            "Traditional Chinese (繁體中文) and provide a concise summary.\n\n"
            f"Text:\n{text}"
        )
        llm = ChatOllama(model=self.model_name, base_url="http://localhost:11434")
        response = llm.invoke(prompt)
        return response.content

    def query(self, question, history=None):
        """Query the RAG system."""
        if not self.vector_store:
            self.initialize_vector_store()

        # 1. Create Retriever
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})

        # 2. Create LLM
        llm = ChatOllama(model=self.model_name, base_url="http://localhost:11434")

        # 3. Create Prompt
        # Strict prompt to only use context
        system_prompt = (
            "You are an assistant for question-answering tasks. "
            "Use the following pieces of retrieved context to answer "
            "the question. If you don't know the answer, say that you "
            "don't know. Use three sentences maximum and keep the "
            "answer concise."
            "\n\n"
            "{context}"
        )

        messages = [("system", system_prompt)]
        
        if history:
            for role, content in history:
                messages.append((role, content))
        
        messages.append(("human", "{input}"))

        prompt = ChatPromptTemplate.from_messages(messages)

        # 4. Create Chain
        question_answer_chain = create_stuff_documents_chain(llm, prompt)
        rag_chain = create_retrieval_chain(retriever, question_answer_chain)

        # 5. Invoke
        response = rag_chain.invoke({"input": question})
        
        # Extract sources
        sources = []
        if "context" in response:
            for doc in response["context"]:
                # Try to get page number
                page = doc.metadata.get("page", None)
                source_file = os.path.basename(doc.metadata.get("source", "Unknown"))
                
                if page is not None and isinstance(page, int):
                    sources.append(f"{source_file} (Page {page + 1})")
                else:
                    sources.append(f"{source_file}")
        
        # Deduplicate sources
        unique_sources = sorted(list(set(sources)))
        
        return {
            "answer": response["answer"],
            "sources": unique_sources
        }

def main():
    parser = argparse.ArgumentParser(description="RAG App using Ollama and local PDF")
    parser.add_argument("--reindex", action="store_true", help="Force re-indexing of the PDF")
    parser.add_argument("--clear", action="store_true", help="Clear the existing database and exit")
    args = parser.parse_args()

    app = RAGOllamaApp()

    if args.clear:
        app.clear_database()
        return

    if args.reindex:
        app.clear_database()
        print("Re-indexing requested...")

    try:
        app.initialize_vector_store()
    except Exception as e:
        print(f"Error initializing: {e}")
        return

    print("\n=== RAG System Ready (Type 'exit' to quit) ===")
    print(f"Model: {MODEL_NAME}")
    print(f"Data Directory: {DATA_DIR}\n")
    print("Commands:")
    print("  - Ask a question")
    print("  - 'page <n>' to view raw page content")
    print("  - 'page <n> explain' (or translate/翻譯) to view and translate page content")
    print("  - 'clear_db' to clear the database")

    while True:
        try:
            user_input = input("Question: ")
            if user_input.lower() in ['exit', 'quit', 'q']:
                break
            
            if not user_input.strip():
                continue

            # Check for clear command
            if user_input.lower() in ['clear_db', 'reset_db', 'clean_db']:
                app.clear_database()
                print("Database cleared. It will be re-created on the next query.")
                continue

            # Check for page lookup command (e.g., "page 10" or "page 10, 12")
            if user_input.lower().startswith("page"):
                try:
                    # Extract numbers from the input string
                    import re
                    page_nums = [int(n) for n in re.findall(r'\d+', user_input)]
                    
                    # Check if translation/explanation is requested
                    keywords = ["explain", "translate", "翻譯", "解釋"]
                    do_translate = any(k in user_input.lower() for k in keywords)

                    if page_nums:
                        contents = app.get_page_content(page_nums)
                        for p_num, content in contents.items():
                            print(f"\n--- Page {p_num} ---")
                            # Limit raw output if it's too long and we are going to translate
                            if do_translate and len(content) > 500:
                                print(content[:500] + "... (truncated for translation)")
                            else:
                                print(content.strip())
                            print("------------------")
                            
                            if do_translate:
                                print(f"\nTranslating/Summarizing Page {p_num}...")
                                summary = app.summarize_text(content)
                                print(f"\n[中文摘要/翻譯]:\n{summary}\n")
                                print("------------------")

                        print()
                        continue
                    else:
                        print("Usage: page <number> [explain/translate] (e.g., 'page 5 explain')")
                        continue
                except Exception as e:
                    print(f"Error parsing page command: {e}")
                    continue

            print("Thinking...", end="", flush=True)
            result = app.query(user_input)
            
            print(f"\rAnswer: {result['answer']}")
            if result['sources']:
                print(f"Sources: {', '.join(result['sources'])}")
            print()
            
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    main()
