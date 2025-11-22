# AI Assistant Apps

This workspace contains example Flask and Streamlit apps that use either OpenAI or Ollama as backends.

Files of interest
- `flask_app.py` - Flask app using OpenAI (port 5001)
- `flask_ollama_app.py` - Flask app using Ollama (port 5002)
- `ai01-using-openAI.py` - OpenAI usage examples and helper functions
- `ai02-use-ollama.py` - Ollama usage examples and helper functions
- `ai03-app.py` - Streamlit front-end example using OpenAI helper functions
- `templates/index.html` and `static/*` - Front-end UI used by the Flask apps

Quick start

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the OpenAI Flask app:

```bash
# make sure OPENAI_API_KEY is exported if required by your code
python flask_app.py
# default port: 5001
```

3. Run the Ollama Flask app (requires Ollama installed and daemon running):

```bash
# ensure Ollama daemon is running locally and python ollama client is available
python flask_ollama_app.py
# default port: 5002
```

4. Run the Streamlit app (OpenAI example):

```bash
streamlit run ai03-app.py
```

Notes
- The front-end will attempt to call `/api/models` and `/api/service-info` on whichever backend you run. Each Flask app now exposes these endpoints so the UI can populate model dropdowns and show which backend is active.
- If your environment doesn't have the `ollama` python package, `flask_ollama_app.py` expects the `ollama` local client to be available; install or adapt as necessary.

If you want, I can:
- Add a small health-check page that shows available endpoints
- Add automated tests for endpoints
- Wire both Flask apps to run under a single reverse-proxy for easier switching
