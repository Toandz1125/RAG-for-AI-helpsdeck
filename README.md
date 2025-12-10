# RAG for AI Helpdesk

This repository bundles two main services:

- **rag-service**: FastAPI REST API that performs retrieval-augmented generation (RAG) to search and summarize content.
- **Orchestrator**: FastAPI gateway that receives user questions, calls rag-service for context, and uses Google Gemini to respond (with Slack support).

## Key Features

- Automated TXT ingestion pipeline: read files, split chunks, embed with `all-MiniLM-L6-v2`, and persist vectors via pickle.
- Optimized search/retrieve APIs plus a context aggregation endpoint ready for LLM prompts.
- Orchestrator unifies Slack Events, RAG, and Gemini with Slack event deduplication and Gemini quota fallback.
- Web crawler that scrapes `vju.vnu.edu.vn` to produce sample data.
- Console demo that interacts with Gemini using strict system instructions.

## Folder Structure

| Path               | Description                                                       |
| ------------------ | ----------------------------------------------------------------- |
| `rag-service/`     | FastAPI RAG backend plus crawler and sample data                  |
| `rag-service/rag/` | Core modules: loader, chunker, embedder, vector store, RAG engine |
| `Orchestrator/`    | FastAPI gateway integrating Gemini and Slack                      |

## System Requirements

- Python 3.10+, pip
- HuggingFace cache downloads the embedding model on first run (CPU friendly)
- Google AI account with a Gemini API key
- Slack App with Bot Token and Signing Secret (if Slack support is required)

## Required Environment Variables

Create a `.env` file inside `Orchestrator/`:

```
RAG_URL=http://127.0.0.1:8000
GEMINI_API_KEY=sk-...
GEMINI_MODEL=gemini-2.5-flash
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
DIFY_API_KEY=...   # optional, kept for compatibility
```

Optional for `rag-service`:

```
DEFAULT_DATA_PATH=data1.txt  # auto-ingest this file on startup if the vector DB is empty
```

## Setup and Run

### 1. rag-service

```powershell
Set-Location .\rag-service
pip install -r requirements.txt
python main.py
```

The server runs at `http://127.0.0.1:8000`.

#### Ingest Data

- Default sample: `python main.py` auto-ingests `data1.txt` if the vector DB is empty.
- Or trigger ingestion via GET from PowerShell:

```powershell
Invoke-RestMethod -Method GET "http://127.0.0.1:8000/ingest-txt?path=C:\duongdan\file.txt"
```

- Or POST JSON `{"file_path": "..."}` to `/ingest`.

#### Health / Retrieval

```powershell
Invoke-RestMethod -Method GET http://127.0.0.1:8000/health
Invoke-RestMethod -Method POST http://127.0.0.1:8000/retrieve `
  -Body (@{query="your question"; top_k=3; include_prompt=$true} | ConvertTo-Json) `
  -ContentType "application/json"
```

- Endpoint `/search` returns an aggregated context string for clarity.

### 2. Orchestrator

```powershell
Set-Location .\Orchestrator
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 9000 --reload
```

- Ensure `rag-service` is running and `RAG_URL` points to the correct host/port.
- `POST /ask` accepts `{"question": "..."}` and returns JSON including the final prompt and Gemini answer.
- `POST /promt` (typo kept) reveals the final prompt for debugging.

## Slack Integration

1. Create a Slack App and enable Event Subscriptions.
2. Point the Request URL to `https://<orchestrator-host>/slack/events`.
3. Grant scopes `app_mentions:read`, `channels:history`, `chat:write`.
4. Populate `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET` in `.env`.
5. When users mention or DM the bot, the system calls `/search` on rag-service to build context, then crafts a bilingual prompt (English instruction + context) → Gemini → posts back to Slack.

## Utility Scripts

- `rag-service/crawler.py`: scrape VJU website content into `data1.txt` (adjust `BASE_URL`, `MAX_PAGES` as needed).
- `rag-service/run_console.py`: interactive Gemini Q&A demo (update the API key inside before running).

## Testing and Validation

- `rag-service/test.py` (extend with your own cases) plus `pytest` in the requirements make it easy to grow automated coverage.
- Recommended scenarios: ingest empty files, query when the DB is empty, duplicate Slack events.

## Maintenance Notes

- Vector DB stored at `rag-service/data/vector_store.pkl` plus a readable dump `vector_store.txt` for debugging.
- `rag-service` downloads the SentenceTransformer model on first run, so internet access is required once.
- `Orchestrator/services/llm_client.py` is generic and can target other LLM providers by changing the base URL and payload format.
- `Reranker` can be upgraded with a CrossEncoder if higher accuracy is needed.
