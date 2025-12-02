
# QA-Agent — Automated Testcase & Selenium Script Generator


Demo Video: https://drive.google.com/file/d/1Qys6bH2C3qYUlLxHS5qXCpp3Iba1_-9-/view?usp=sharingv

**Created by:** Rupsa Nanda

QA-Agent is an intelligent automated QA workflow tool that reads project documents and generates structured testcases. It also converts selected testcases into Selenium scripts for browser-based automation. The system builds a searchable knowledge base using ChromaDB and sentence-transformer-based embeddings.

---

## Table of Contents
- Project overview
- Features
- Tech stack
- Quick start
- Folder architecture
- How to use
- Notes & tips
- Contributing
 
---

## Project Overview
This repository contains a simple backend (FastAPI) and a Streamlit frontend used for uploading project documents, generating an internal knowledge base (KB) using ChromaDB, and automatically creating structured testcases and corresponding Selenium scripts.

## Features
- Upload and manage project/support documents
- Build a searchable KB with ChromaDB
- Generate structured testcases from documents
- View and export generated testcases
- Convert selected testcases to Selenium scripts

---

## Tech Stack
- Python 3.10+
- FastAPI (backend)
- Streamlit (UI)
- ChromaDB (vector store)
- SentenceTransformers (embeddings)
- Selenium WebDriver (script execution)
- Uvicorn (asgi server)

---

## Quick Start
1. Install dependencies (recommended to use a venv):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate; pip install -r requirements.txt
```

2. Run the backend (in one terminal):

```powershell
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

3. Run the Streamlit UI (in another terminal):

```powershell
cd ui
streamlit run app.py
```

Open the UI at: http://localhost:8501 and the API docs at: http://127.0.0.1:8000/docs

---

## Folder Architecture
Below is the primary folder structure of the project along with brief descriptions of the important files and directories.

```
QA-AGENT/
├── agents/                    # Automation agents: testcase & Selenium script generators
│   ├── seleniumAgent.py       # Generates Selenium scripts from testcases
│   ├── testcaseAgent.py       # Generates testcases from KB or requirements
│   └── __pycache__/
├── assets/                    # Reference and input documents used across the app
│   ├── api_endpoints.json
│   ├── faq.json
│   ├── notes.md
│   ├── product_specs.md
│   └── ui_ux_guide.txt
├── backend/                   # FastAPI backend, retriever, and API logic
│   ├── main.py                # FastAPI app entrypoint
│   ├── retriever.py           # Vector DB query helper for the KB
│   ├── requirements.txt
│   └── __init__.py
├── chroma_db/                 # Persisted ChromaDB files and data
│   └── chroma.sqlite3
├── ingest/                    # Ingestion pipeline & embedding utilities
│   ├── ingest.py
│   ├── chunkSave.py
│   ├── embedChunks.py
│   ├── chunks.json
│   └── embeddings_meta.json
├── ui/                        # Streamlit UI
│   └── app.py                 # Streamlit front end
├── selenium_scripts/          # Example Selenium test scripts
│   └── test_case_1.py
├── selenium_debug/            # Debug files useful for testing Selenium behavior
│   └── page_source.html
├── uploaded_assets/           # Uploaded sample assets used by the UI
├── uploaded_docs/             # Uploaded sample documents used to build KB
├── tests/                     # Test suites (if present)
├── generated_testcases.json   # Output of testcase generation
├── README.md                  # Project documentation (this file)
└── requirements.txt           # Central requirements file for developer convenience
```

### Folder & File Descriptions
- agents: Scripts that act as automation/agent modules which generate testcases and Selenium scripts from test definitions.
- backend: FastAPI server that accepts uploads, builds the KB and exposes endpoints used by the UI.
- ui: The Streamlit front end that allows users to upload documents and trigger generation workflows.
- ingest: Code for splitting documents into chunks, generating embeddings, and storing them into ChromaDB.
- chroma_db: Local persistence files for the vector DB — used by retriever for semantic search.
- selenium_scripts: Example Selenium scripts generated from selected testcases.
- tests: Unit tests and test runners for different parts of the project (if present).

---

## How to Use QA-Agent (High-level)
1. Open the Streamlit UI: http://localhost:8501
2. Upload one or more documents (PDFs, Markdown, etc.)
3. Click "Build KB" to create or update the knowledge base
4. Provide a short requirement or test objective in the UI
5. Click "Generate Testcases" to produce structured testcases
6. Refresh the testcase panel to load the generated items
7. Select a testcase and click "Generate Selenium Script" to generate an automation script

---

## Notes & Tips
- The project stores generated testcases in `generated_testcases.json` by default.
- ChromaDB files are stored inside `chroma_db/`.
- Selenium scripts and debug artifacts are in `selenium_scripts/` and `selenium_debug/`.
- If you plan to run the Selenium tests locally, make sure you have the proper WebDriver installed (e.g., Chromedriver, Geckodriver) and that it matches your browser version.

---

## Troubleshooting
- If the backend can't start, check that dependencies are installed and that Python 3.10+ is used.
- If the Streamlit UI doesn't load, check for port conflicts on 8501 and try running on a different port using `streamlit run app.py --server.port 8502`.

---

## Deploying to Render (or any similar platform)

If you're deploying this project to Render (or a similar PaaS), here are recommended steps to ensure the service binds to the correct port and the platform detects the open port:

1. Ensure the platform runs a Web Service (not a worker) and that the **Start Command** is set.
2. Use the platform-provided port env var (Render uses `$PORT`). Example start command (recommended):

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT --log-level info
```

Alternatively, our `backend/run.py` already respects the `PORT` environment variable and will bind to it, so if you must start with the Python file the command can be:

```bash
python backend/run.py
```

3. Set the Health Check Path to `/` or `/health` so Render can verify the app started. The backend includes `/health` and `/` endpoints.
4. If startup takes longer than platform timeout (e.g., model loading or other heavy init), increase the service start timeout in Render settings or ensure lazy-loading of heavy modules.
5. If the Deploy logs say `No open ports detected`, verify the start command is using `$PORT`, the service is a Web Service, and there are no firewall blocks.

PowerShell local test commands (Windows):

```powershell
# test local run with explicit port set
$env:PORT = "10000"; python backend/run.py

# curl to check health (run in another shell)
curl http://localhost:10000/health
```

If you still see `No open ports detected` on your Render deployment despite Uvicorn printing something like `Uvicorn running on http://0.0.0.0:10000`, try setting the start command in Render to use uvicorn directly (first option above) and a health-check path of `/health`.


## Contributing
Please open issues or PRs if you'd like to fix bugs or add features. If you submit a PR, include tests when possible and follow the existing code style.

---




