import os
import shutil
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

class RAGSystem:
    def __init__(self, data_dir="rag_data", db_path="rag_data/chroma_db_v2", model_name="gemma3:4b", embedding_model="all-minilm"):
        self.data_dir = data_dir
        self.db_path = db_path
        self.model_name = model_name
        self.embedding_model = embedding_model
        self.embeddings = OllamaEmbeddings(model=embedding_model, base_url="http://localhost:11434")
        self.vector_store = None
        
        # Initialize vector store if it exists
        if os.path.exists(self.db_path) and os.listdir(self.db_path):
            try:
                self.vector_store = Chroma(persist_directory=self.db_path, embedding_function=self.embeddings)
            except Exception as e:
                print(f"Error loading existing vector store: {e}")

    def clear_index(self):
        if os.path.exists(self.db_path):
            try:
                shutil.rmtree(self.db_path)
            except Exception as e:
                return f"Error clearing index: {e}"
        self.vector_store = None
        return "Index cleared."

    def load_and_index(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            return "Created data directory. Please add files."
            
        documents = []
        files_found = []
        
        # Check if directory is empty
        if not os.listdir(self.data_dir):
            return "rag_data directory is empty."

        for filename in os.listdir(self.data_dir):
            file_path = os.path.join(self.data_dir, filename)
            try:
                if filename.endswith(".pdf"):
                    loader = PyPDFLoader(file_path)
                    documents.extend(loader.load())
                    files_found.append(filename)
                elif filename.endswith(".docx"):
                    loader = Docx2txtLoader(file_path)
                    documents.extend(loader.load())
                    files_found.append(filename)
            except Exception as e:
                print(f"Error loading {filename}: {e}")
        
        if not documents:
            return "No supported documents (PDF/DOCX) found in rag_data."

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(documents)
        
        self.vector_store = Chroma.from_documents(
            documents=splits, 
            embedding=self.embeddings, 
            persist_directory=self.db_path
        )
        
        return f"Indexed {len(documents)} pages/chunks from {len(files_found)} files."

    def query(self, question):
        if not self.vector_store:
            return {"answer": "Please index the documents first.", "sources": []}
            
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
        llm = ChatOllama(model=self.model_name, base_url="http://localhost:11434")
        
        system_prompt = (
            "You are a helpful AI assistant for Question-Answering tasks. "
            "Use the following pieces of retrieved context to answer the question. "
            "If you don't know the answer, say that you don't know. "
            "Keep the answer concise."
            "\n\n"
            "{context}"
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])
        
        question_answer_chain = create_stuff_documents_chain(llm, prompt)
        rag_chain = create_retrieval_chain(retriever, question_answer_chain)
        
        response = rag_chain.invoke({"input": question})
        
        sources = []
        if "context" in response:
            for doc in response["context"]:
                source = doc.metadata.get("source", "Unknown")
                page = doc.metadata.get("page", None)
                if page is not None:
                    sources.append(f"{os.path.basename(source)} (Page {page+1})")
                else:
                    sources.append(os.path.basename(source))
        
        return {
            "answer": response["answer"],
            "sources": sorted(list(set(sources)))
        }
