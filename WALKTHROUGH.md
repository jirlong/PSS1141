# RAG Ollama Application Walkthrough

This guide explains how to set up and use the Local RAG (Retrieval-Augmented Generation) application. This system allows you to chat with your PDF and DOCX documents using local LLMs via Ollama.

## 1. Prerequisites

Before running the application, ensure you have the following installed:

*   **Python 3.10+**
*   **Ollama**: Download and install from [ollama.com](https://ollama.com/).

### 1.1 Pull Required Models
The application uses specific models for text generation and embeddings. Run these commands in your terminal:

```bash
# Pull the main LLM (currently configured to gemma3:12b)
ollama pull gemma3:12b

# Pull the embedding model
ollama pull all-minilm
```

## 2. Installation

1.  Navigate to the project directory.
2.  Install the required Python packages:

```bash
pip install -r requirements_rag.txt
```

## 3. Setup Documents

1.  Ensure there is a folder named `rag_data` in the project root.
2.  Place your PDF (`.pdf`) and Word (`.docx`) files into the `rag_data/` folder.
    *   *Example: `rag_data/consultation.pdf`, `rag_data/notes.docx`*

## 4. Usage: Web Interface (Streamlit)

This is the recommended way to interact with the system.

### 4.1 Run the App
```bash
streamlit run rag_ollama_app.py
```
This will open the application in your default web browser (usually at `http://localhost:8501`).

### 4.2 Features
*   **Chat**: Type your questions in the input box at the bottom. The AI will answer based *only* on the content of your documents.
*   **Sources**: Every answer includes citations (filenames and page numbers) at the bottom.
*   **Sidebar Controls**:
    *   **Re-index / Reset Database**: Click this if you have added new files to `rag_data` and want to update the system.
    *   **Indexed Files**: Shows a list of all documents currently being used.
    *   **Page Inspector**: Enter a page number and click "View & Explain Page" to see the raw text and get a translated summary of that specific page.

## 5. Usage: Command Line Interface (CLI)

If you prefer using the terminal, you can use the CLI version.

### 5.1 Run the App
```bash
python rag_ollama.py
```

### 5.2 Commands
Once the app is running, you can type:

*   **Ask a question**: Just type your query (e.g., "What is the main topic?").
*   **`page <n>`**: View the raw content of a specific page (e.g., `page 5`).
*   **`page <n> explain`** (or `translate`/`翻譯`): View the content of a page *and* get a summary/translation in Traditional Chinese (e.g., `page 5 翻譯`).
*   **`clear_db`**: Clear the database and force a re-index on the next query.
*   **`exit`** / **`quit`**: Close the application.

### 5.3 CLI Arguments
You can also run the script with flags:

*   `python rag_ollama.py --reindex`: Force a re-index immediately upon startup.
*   `python rag_ollama.py --clear`: Clear the database and exit.

## 6. Troubleshooting

*   **"No documents found to index"**: Make sure your files are in the `rag_data` folder and have `.pdf` or `.docx` extensions.
*   **Model not found**: Ensure you have run `ollama pull gemma3:12b` and `ollama pull all-minilm`.
*   **Database errors**: Try clicking "Re-index / Reset Database" in the web app or running `python rag_ollama.py --clear` in the terminal.
