import os
import shutil
import streamlit as st
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
                return True, f"Database at {self.db_path} has been cleared."
            except Exception as e:
                return False, f"Error clearing database: {e}"
        else:
            return True, "No database found to clear."

    def load_documents(self):
        """Load all supported documents from the data directory."""
        documents = []
        if not os.path.exists(self.data_dir):
            return []

        for filename in os.listdir(self.data_dir):
            file_path = os.path.join(self.data_dir, filename)
            if filename.endswith(".pdf"):
                loader = PyPDFLoader(file_path)
                documents.extend(loader.load())
            elif filename.endswith(".docx"):
                loader = Docx2txtLoader(file_path)
                documents.extend(loader.load())
        
        self.documents = documents
        return documents

    def initialize_vector_store(self):
        """Check if vector store exists, if not, create it from documents."""
        if os.path.exists(self.db_path) and os.listdir(self.db_path):
            self.vector_store = Chroma(persist_directory=self.db_path, embedding_function=self.embeddings)
            return "Loaded existing vector store."
        else:
            # 1. Load Documents
            docs = self.load_documents()
            if not docs:
                return "No documents found to index."

            # 2. Split Text
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            splits = text_splitter.split_documents(docs)

            # 3. Create Vector Store
            self.vector_store = Chroma.from_documents(
                documents=splits, 
                embedding=self.embeddings, 
                persist_directory=self.db_path
            )
            return f"Created new vector store with {len(splits)} chunks."

    def get_page_content(self, page_numbers):
        """Retrieve content for specific pages (1-indexed)."""
        if not self.documents:
            self.load_documents()
        
        results = {}
        page_map = {}
        for i, doc in enumerate(self.documents):
            p_num = doc.metadata.get("page", i)
            if isinstance(p_num, int):
                p_num += 1 
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

    def query(self, question):
        """Query the RAG system."""
        if not self.vector_store:
            self.initialize_vector_store()

        retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
        llm = ChatOllama(model=self.model_name, base_url="http://localhost:11434")

        system_prompt = (
            "You are an assistant for question-answering tasks. "
            "Use the following pieces of retrieved context to answer "
            "the question. If you don't know the answer, say that you "
            "don't know. Use three sentences maximum and keep the "
            "answer concise."
            "\n\n"
            "{context}"
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{input}"),
            ]
        )

        question_answer_chain = create_stuff_documents_chain(llm, prompt)
        rag_chain = create_retrieval_chain(retriever, question_answer_chain)
        response = rag_chain.invoke({"input": question})
        
        sources = []
        if "context" in response:
            for doc in response["context"]:
                page = doc.metadata.get("page", None)
                source_file = os.path.basename(doc.metadata.get("source", "Unknown"))
                
                if page is not None and isinstance(page, int):
                    sources.append(f"{source_file} (Page {page + 1})")
                else:
                    sources.append(f"{source_file}")
        
        unique_sources = sorted(list(set(sources)))
        
        return {
            "answer": response["answer"],
            "sources": unique_sources
        }

# Streamlit App
def main():
    st.set_page_config(page_title="RAG Ollama Assistant", layout="wide")
    
    st.title("🤖 RAG Ollama Assistant")
    
    # Initialize Session State
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "app_instance" not in st.session_state:
        st.session_state.app_instance = RAGOllamaApp()
        with st.spinner("Initializing RAG System..."):
            status = st.session_state.app_instance.initialize_vector_store()
            st.toast(status)

    app = st.session_state.app_instance

    # Sidebar
    with st.sidebar:
        st.header("Configuration")
        st.write(f"**Model:** {MODEL_NAME}")
        st.write(f"**Embedding:** {EMBEDDING_MODEL}")
        
        st.divider()
        
        st.header("Database Management")
        if st.button("Re-index / Reset Database"):
            with st.spinner("Clearing and Re-indexing..."):
                app.clear_database()
                status = app.initialize_vector_store()
                st.success(status)
                st.session_state.messages = [] # Clear chat on reset
        
        st.divider()
        
        st.header("Indexed Files")
        if os.path.exists(DATA_DIR):
            files = os.listdir(DATA_DIR)
            for f in files:
                if f.endswith(('.pdf', '.docx')):
                    st.text(f"📄 {f}")
        else:
            st.warning("Data directory not found!")

        st.divider()
        st.header("Page Inspector")
        page_num_input = st.number_input("Page Number", min_value=1, value=1)
        if st.button("View & Explain Page"):
            with st.spinner(f"Analyzing Page {page_num_input}..."):
                contents = app.get_page_content([page_num_input])
                content = contents.get(page_num_input, "Page not found")
                
                st.subheader(f"Page {page_num_input} Content")
                st.text_area("Raw Text", content, height=200)
                
                st.subheader("Explanation / Translation")
                summary = app.summarize_text(content)
                st.markdown(summary)

    # Chat Interface
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a question about your documents..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Handle "page" commands in chat for backward compatibility
        if prompt.lower().startswith("page"):
            with st.chat_message("assistant"):
                try:
                    import re
                    page_nums = [int(n) for n in re.findall(r'\d+', prompt)]
                    
                    keywords = ["explain", "translate", "翻譯", "解釋"]
                    do_translate = any(k in prompt.lower() for k in keywords)

                    if page_nums:
                        contents = app.get_page_content(page_nums)
                        response_text = ""
                        for p_num, content in contents.items():
                            response_text += f"**--- Page {p_num} ---**\n\n"
                            if do_translate and len(content) > 500:
                                response_text += content[:500] + "... (truncated)\n\n"
                            else:
                                response_text += content + "\n\n"
                            
                            if do_translate:
                                with st.spinner(f"Translating Page {p_num}..."):
                                    summary = app.summarize_text(content)
                                    response_text += f"**[中文摘要/翻譯]:**\n{summary}\n\n"
                        
                        st.markdown(response_text)
                        st.session_state.messages.append({"role": "assistant", "content": response_text})
                    else:
                        msg = "Usage: page <number> [explain/translate]"
                        st.markdown(msg)
                        st.session_state.messages.append({"role": "assistant", "content": msg})
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            # Standard RAG Query
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    result = app.query(prompt)
                    answer = result["answer"]
                    sources = result["sources"]
                    
                    full_response = f"{answer}\n\n"
                    if sources:
                        full_response += f"**Sources:** {', '.join(sources)}"
                    
                    st.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})

if __name__ == "__main__":
    main()
