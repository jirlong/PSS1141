import os
import json
import re
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Type, Union
from pydantic import BaseModel

# Imports for providers
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import ollama
except ImportError:
    ollama = None

try:
    import anthropic
except ImportError:
    anthropic = None

# Pydantic model for structured output (OpenAI)
class News5W1H(BaseModel):
    who: str
    what: str
    when: str
    where: str
    why: str
    how: str


# ==========================================
# Strategy Interface & Concrete Strategies
# ==========================================

class LLMProvider(ABC):
    """Abstract Strategy for LLM Providers"""
    
    def __init__(self, model: str, api_key: str = None):
        self.default_model = model
        self.api_key = api_key

    @abstractmethod
    def generate_text(self, prompt: str, system_prompt: str, temperature: float, model: str = None) -> str:
        pass

    @abstractmethod
    def generate_structured(self, prompt: str, system_prompt: str, schema: Type[BaseModel], model: str = None) -> dict:
        pass

    def _get_model(self, override_model: str = None) -> str:
        return override_model or self.default_model


class OpenAIProvider(LLMProvider):
    def __init__(self, model: str = "gpt-4.1-mini", api_key: str = None):
        super().__init__(model, api_key)
        if OpenAI is None:
            raise ImportError("OpenAI package not installed.")
        key = self.api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            print("Warning: No OpenAI API key provided.")
        self.client = OpenAI(api_key=key)

    def generate_text(self, prompt: str, system_prompt: str, temperature: float, model: str = None) -> str:
        response = self.client.responses.create(
            model=self._get_model(model),
            instructions=system_prompt,
            input=prompt,
            temperature=temperature
        )
        return response.output_text

    def generate_structured(self, prompt: str, system_prompt: str, schema: Type[BaseModel], model: str = None) -> dict:
        response = self.client.responses.parse(
            model=self._get_model(model),
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2, # Generally low temp for structured
            text_format=schema
        )
        return response.output_parsed.model_dump()


class OllamaProvider(LLMProvider):
    def __init__(self, model: str = "gemma3:1b", api_key: str = None):
        super().__init__(model, api_key)
        if ollama is None:
            raise ImportError("Ollama package not installed.")
        self.client = ollama

    def generate_text(self, prompt: str, system_prompt: str, temperature: float, model: str = None) -> str:
        response = self.client.chat(
            model=self._get_model(model),
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ],
            # Note: Ollama python lib options might need 'options' dict for temp, 
            # but sticking to simple chat interface as requested.
        )
        return response['message']['content']

    def generate_structured(self, prompt: str, system_prompt: str, schema: Type[BaseModel], model: str = None) -> dict:
        # Fallback logic for providers without native structured output
        # Get schema fields to instruct the model
        fields = schema.model_fields.keys()
        json_instruction = f"""
        Return the result in valid JSON format with these exact keys: {', '.join([f'"{f}"' for f in fields])}.
        If information is missing, use "Not specified".
        """
        
        full_system_prompt = f"{system_prompt}\n{json_instruction}"
        
        raw_response = self.generate_text(prompt, full_system_prompt, temperature=0.2, model=model)
        
        return self._parse_json_fallback(raw_response)

    def _parse_json_fallback(self, text: str) -> dict:
        try:
            json_match = re.search(r"\{[\s\S]*\}", text)
            if json_match:
                return json.loads(json_match.group(0))
            return {"error": "Could not parse JSON", "raw_output": text}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON returned", "raw_output": text}


class AnthropicProvider(LLMProvider):
    def __init__(self, model: str = "claude-sonnet-4-5", api_key: str = None):
        super().__init__(model, api_key)
        if anthropic is None:
            raise ImportError("Anthropic package not installed.")
        key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not key:
            print("Warning: No Anthropic API key provided.")
        self.client = anthropic.Anthropic(api_key=key)

    def generate_text(self, prompt: str, system_prompt: str, temperature: float, model: str = None) -> str:
        response = self.client.messages.create(
            model=self._get_model(model),
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=temperature
        )
        return response.content[0].text

    def generate_structured(self, prompt: str, system_prompt: str, schema: Type[BaseModel], model: str = None) -> dict:
        # Reuse fallback logic similar to Ollama
        fields = schema.model_fields.keys()
        json_instruction = f"""
        Return the result in valid JSON format with these exact keys: {', '.join([f'"{f}"' for f in fields])}.
        If information is missing, use "Not specified".
        """
        full_system_prompt = f"{system_prompt}\n{json_instruction}"
        
        raw_response = self.generate_text(prompt, full_system_prompt, temperature=0.2, model=model)
        
        # Reuse the parsing logic (could be shared in base class, but kept here for now)
        try:
            json_match = re.search(r"\{[\s\S]*\}", raw_response)
            if json_match:
                return json.loads(json_match.group(0))
            return {"error": "Could not parse JSON", "raw_output": raw_response}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON returned", "raw_output": raw_response}


# RAG Imports
try:
    from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.embeddings import OllamaEmbeddings
    from langchain_chroma import Chroma
    HAS_RAG_LIBS = True
except ImportError:
    HAS_RAG_LIBS = False


# ==========================================
# RAG Engine (Local Retrieval)
# ==========================================

class RAGEngine:
    def __init__(self, data_dir="rag_data", db_path="rag_data/chroma_db", embedding_model="all-minilm"):
        self.data_dir = data_dir
        self.db_path = db_path
        self.embedding_model = embedding_model
        self.vector_store = None
        self._embeddings = None

    @property
    def embeddings(self):
        if not self._embeddings:
            if not HAS_RAG_LIBS:
                raise ImportError("RAG libraries (langchain, chroma) not installed.")
            self._embeddings = OllamaEmbeddings(model=self.embedding_model, base_url="http://localhost:11434")
        return self._embeddings

    def initialize_vector_store(self):
        """Initialize or Create Vector Store"""
        if not HAS_RAG_LIBS:
            print("❌ RAG libraries missing. Cannot initialize vector store.")
            return

        if os.path.exists(self.db_path) and os.listdir(self.db_path):
            self.vector_store = Chroma(persist_directory=self.db_path, embedding_function=self.embeddings)
        else:
            self._create_index()

    def _create_index(self):
        print(f"Creating new vector store from {self.data_dir}...")
        docs = []
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir, exist_ok=True)
            print(f"Created directory {self.data_dir}. Please put PDF/DOCX files there.")
            return

        for filename in os.listdir(self.data_dir):
            file_path = os.path.join(self.data_dir, filename)
            try:
                if filename.endswith(".pdf"):
                    loader = PyPDFLoader(file_path)
                    docs.extend(loader.load())
                elif filename.endswith(".docx"):
                    loader = Docx2txtLoader(file_path)
                    docs.extend(loader.load())
            except Exception as e:
                print(f"Error loading {filename}: {e}")
        
        if not docs:
            print("No documents found to index.")
            return

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)
        
        self.vector_store = Chroma.from_documents(
            documents=splits, 
            embedding=self.embeddings, 
            persist_directory=self.db_path
        )
        print("Vector store created.")

    def retrieve(self, query: str, k: int = 3) -> str:
        if not HAS_RAG_LIBS:
            return "Error: RAG libraries not installed."
        
        if not self.vector_store:
            self.initialize_vector_store()
            
        if not self.vector_store:
            return "Error: No documents indexed."

        results = self.vector_store.similarity_search(query, k=k)
        return "\n\n".join([doc.page_content for doc in results])


# ==========================================
# Main Factory / Context Class
# ==========================================

class LLM:
    """
    Unified LLM Interface.
    Delegates actual work to the underlying Provider Strategy.
    """

    def __init__(self, provider: str = "openai", model: str = None, api_key: str = None):
        self.provider_name = provider.lower()
        self.provider = self._create_provider(self.provider_name, model, api_key)
        self.rag_engine = RAGEngine() # Initialize RAG Engine

    def _create_provider(self, provider_name: str, model: str, api_key: str) -> LLMProvider:
        if provider_name == "openai":
            return OpenAIProvider(model=model or "gpt-5-mini", api_key=api_key)
        elif provider_name == "ollama":
            return OllamaProvider(model=model or "gemma3:1b", api_key=api_key)
        elif provider_name == "anthropic":
            return AnthropicProvider(model=model or "claude-sonnet-4-5", api_key=api_key)
        else:
            raise ValueError(f"Unknown provider: {provider_name}")

    def ask_question(self, question: str, instructions: str = "You are a helpful assistant.", temperature: float = 0.7, model: str = None) -> str:
        """General purpose Question & Answering."""
        return self.provider.generate_text(
            prompt=question, 
            system_prompt=instructions, 
            temperature=temperature, 
            model=model
        )

    def translator(self, text: str, model: str = None) -> str:
        """Translate between Chinese and English."""
        instructions = """You are a professional translator. 
        If the input is in Traditional Chinese, translate it to English.
        If the input is in English, translate it to Traditional Chinese.
        Only return the translated text."""
        
        return self.ask_question(text, instructions=instructions, temperature=0.3, model=model)

    def story_teller(self, topic: str, model: str = None) -> str:
        """Tell a bedside story about the topic."""
        instructions = "You are a creative storyteller. Write a short bedtime story (approx 100 words)."
        prompt = f"Write a bedtime story about {topic}."
        
        return self.ask_question(prompt, instructions=instructions, temperature=0.9, model=model)

    def news_5w1h(self, news_text: str, model: str = None) -> Dict[str, Any]:
        """Extract 5W1H from news text."""
        system_prompt = "You are a professional news analyst. Extract the 5W1H information."
        return self.provider.generate_structured(
            prompt=news_text,
            system_prompt=system_prompt,
            schema=News5W1H,
            model=model
        )

    def dispatcher(self, user_request: str, model: str = None) -> Any:
        """
        Intelligent task dispatcher. 
        """
        classification_prompt = f"""Analyze the user request and determine which function to use.
        
        Request: "{user_request}"
        
        Functions:
        1. translator - For translation (keywords: translate, 翻譯, Chinese, English)
        2. news_5w1h - For news analysis (keywords: news, 5W1H, summarize news, 分析新聞)
        3. story_teller - For stories (keywords: story, tell me a story, 故事)
        4. ask_question - General questions (everything else)
        
        Respond ONLY with the function name: 'translator', 'news_5w1h', 'story_teller', or 'ask_question'."""
        
        # Self-delegation for classification
        func_name = self.ask_question(classification_prompt, temperature=0.0, model=model).strip().lower()
        
        print(f"[{self.provider_name}] Dispatcher routing to: {func_name}")

        if "translator" in func_name:
            extract_prompt = f"Extract only the text content that needs to be translated from this request: '{user_request}'. Return only the content."
            content = self.ask_question(extract_prompt, model=model).strip()
            if not content: content = user_request
            return self.translator(content, model=model)
            
        elif "news_5w1h" in func_name:
            extract_prompt = f"Extract only the news article text from this request: '{user_request}'. Return only the content."
            content = self.ask_question(extract_prompt, model=model).strip()
            return self.news_5w1h(content, model=model)
            
        elif "story_teller" in func_name:
            extract_prompt = f"Extract the main topic for the story from this request: '{user_request}'. Return only the topic."
            topic = self.ask_question(extract_prompt, model=model).strip()
            return self.story_teller(topic, model=model)
            
        else:
            return self.ask_question(user_request, model=model)

    def rag_query(self, question: str, model: str = None) -> str:
        """
        RAG Query:
        1. Retrieve context from local RAGEngine.
        2. Generate answer using active LLM Provider.
        """
        context = self.rag_engine.retrieve(question)
        
        if context.startswith("Error:"):
            print(f"RAG Warning: {context}")
            # Fallback to basic answer without context
            return self.ask_question(question, model=model)

        system_prompt = (
            "You are a helpful assistant. Use the following retrieved context to answer the user's question. "
            "If the answer is not in the context, say you don't know."
            "\n\n"
            f"Context:\n{context}"
        )
        
        return self.ask_question(question, instructions=system_prompt, model=model)


# Example Usage & Testing
if __name__ == "__main__":
    def run_tests():
        print("="*60)
        print("🧪 LLM Unified Interface - Comprehensive Test Suite")
        print("="*60)
        
        if not HAS_RAG_LIBS:
            print("⚠️  RAG libraries (langchain, chroma) are missing. RAG features will be disabled.\n")

        providers_to_test = [
            {"name": "openai", "key_env": "OPENAI_API_KEY"},
            {"name": "ollama", "key_env": None},      # No key needed
            {"name": "anthropic", "key_env": "ANTHROPIC_API_KEY"},
        ]

        news_sample = "Apple announced yesterday that it will release a new foldable iPhone next year in Cupertino."

        for p in providers_to_test:
            provider_name = p["name"]
            key_env = p["key_env"]
            
            print(f"\n[{provider_name.upper()}] Checking availability...")
            
            # Check API keys for cloud providers
            api_key = None
            if key_env:
                api_key = os.getenv(key_env)
                if not api_key:
                    print(f"⚠️  Skipping {provider_name}: {key_env} not found in environment.")
                    continue
            
            # Attempt initialization
            try:
                llm = LLM(provider=provider_name, api_key=api_key)
                print(f"✅ Initialized {provider_name}.")
            except ImportError as e:
                print(f"❌ Skipping {provider_name}: Library not installed ({e}).")
                continue
            except Exception as e:
                print(f"❌ Skipping {provider_name}: Initialization error ({e}).")
                continue

            print(f"🚀 Running 6 Missions for {provider_name}...")
            
            try:
                # Mission 1: Ask Question
                print(f"  1. [Ask] What is 1+1? -> ", end="", flush=True)
                res = llm.ask_question("What is 1+1? Answer briefly.")
                print(f"{res.strip()[:50]}...")

                # Mission 2: Translator
                print(f"  2. [Translate] 'Hello' -> ", end="", flush=True)
                res = llm.translator("Hello")
                print(f"{res.strip()[:50]}...")

                # Mission 3: Story Teller
                print(f"  3. [Story] Topic 'Coffee' -> ", end="", flush=True)
                res = llm.story_teller("Coffee")
                print(f"(Length: {len(res)} chars)")

                # Mission 4: News 5W1H
                print(f"  4. [News] Analyzing Apple news... -> ", end="", flush=True)
                res = llm.news_5w1h(news_sample)
                print(f"Success (Who: {res.get('who', 'Unknown')})")

                # Mission 5: Dispatcher
                print(f"  5. [Dispatch] 'Tell me a story about a cat' -> ", end="", flush=True)
                res = llm.dispatcher("Tell me a story about a cat")
                if isinstance(res, str):
                    print(f"Routed to Story (Length: {len(res)} chars)")
                else: 
                    print(f"Result type: {type(res)}")
                
                # Mission 6: RAG
                print(f"  6. [RAG] Querying 'What is in the context?' -> ", end="", flush=True)
                # Note: This might fail gracefully if no docs, but verifies method exists
                res = llm.rag_query("What is mentioned in the documents?")
                print(f"{res.strip()[:50]}...")

            except Exception as e:
                print(f"\n❌ Error during execution: {e}")

            print("-" * 60)

    run_tests()
