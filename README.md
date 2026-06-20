# RAG LangGraph Test Generation Platform

This project generates automation test scripts from natural language using:

- FastAPI
- LangChain
- LangGraph
- ChromaDB
- Transformers / SentenceTransformers
- Ollama local LLMs
- Robot Framework / Python / Playwright

## Architecture

User Prompt
→ FastAPI
→ LangGraph workflow
→ LangChain retriever
→ ChromaDB vector database
→ HuggingFace embeddings
→ Ollama local LLM
→ Validator
→ Final generated automation code

## Create Virtual Environment

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Optional: Install Ollama Model

```bash
ollama pull qwen2.5-coder:7b
```

or:

```bash
ollama pull deepseek-coder:6.7b
```

## Run Backend

```bash
uvicorn app.main:app --reload
```

## Open Swagger

```text
http://localhost:8000/docs
```

## Health Check

```bash
curl http://localhost:8000/health
```

## Ingest Sample Repo

```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "repo_path": "./sample_repos",
    "framework": "generic"
  }'
```

## Search Existing Automation Code

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "create venue on ruckus cloud",
    "framework": "robot",
    "top_k": 3
  }'
```

## Generate Code Using LangGraph Workflow

```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create venue on Ruckus Cloud from login to verification",
    "framework": "robot",
    "top_k": 3
  }'
```

## Run Tests

```bash
pytest -v
```

## Run With Docker

```bash
docker compose up --build
```# RAG LangGraph Test Generation Platform

This project generates automation test scripts from natural language using:

- FastAPI
- LangChain
- LangGraph
- ChromaDB
- Transformers / SentenceTransformers
- Ollama local LLMs
- Robot Framework / Python / Playwright

## Architecture

User Prompt
→ FastAPI
→ LangGraph workflow
→ LangChain retriever
→ ChromaDB vector database
→ HuggingFace embeddings
→ Ollama local LLM
→ Validator
→ Final generated automation code

## Create Virtual Environment

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Optional: Install Ollama Model

```bash
ollama pull qwen2.5-coder:7b
```

or:

```bash
ollama pull deepseek-coder:6.7b
```

## Run Backend

```bash
uvicorn app.main:app --reload
```

## Open Swagger

```text
http://localhost:8000/docs
```

## Health Check

```bash
curl http://localhost:8000/health
```

## Ingest Sample Repo

```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "repo_path": "./sample_repos",
    "framework": "generic"
  }'
```

## Search Existing Automation Code

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "create venue on ruckus cloud",
    "framework": "robot",
    "top_k": 3
  }'
```

## Generate Code Using LangGraph Workflow

```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create venue on Ruckus Cloud from login to verification",
    "framework": "robot",
    "top_k": 3
  }'
```

## Run Tests

```bash
pytest -v
```

## Run With Docker

```bash
docker compose up --build
```