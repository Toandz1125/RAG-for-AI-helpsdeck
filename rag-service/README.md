# RAG Service

Minimal RAG API built with FastAPI. It provides endpoints to ingest plain-text files, store embeddings, and retrieve relevant chunks.

## Prerequisites
- Python 3.10+ (tested on Windows, CPU only)
- Pip
- (Optional) Docker

## Setup & Run (local Python, no virtualenv)
```powershell
Set-Location D:\Workspace\AI_midterm\rag-service\rag-service
pip install -r requirements.txt
python main.py
```
The server starts on `http://127.0.0.1:8000`.

## Quick Health Check
```powershell
Invoke-RestMethod -Method GET http://127.0.0.1:8000/health
```

## Ingest Data
Use the provided sample file `data1.txt` or any `.txt` file.
```powershell
Invoke-RestMethod -Method GET "http://127.0.0.1:8000/ingest-txt?path=D:\Workspace\AI_midterm\rag-service\rag-service\data1.txt"
```

## Retrieve / Search
Retrieve top-k chunks and optionally include a prompt.
```powershell
Invoke-RestMethod -Method POST http://127.0.0.1:8000/retrieve `
  -Body (@{query="your question"; top_k=3; include_prompt=$false} | ConvertTo-Json) `
  -ContentType "application/json"
```
Or get aggregated context:
```powershell
Invoke-RestMethod -Method POST http://127.0.0.1:8000/search `
  -Body (@{query="your question"; top_k=3} | ConvertTo-Json) `
  -ContentType "application/json"
```

## Run with Docker (optional)
```powershell
Set-Location D:\Workspace\AI_midterm\rag-service\rag-service
docker build -t rag-service .
docker run -p 8000:8000 -v "$PWD/data:/app/data" rag-service
```
Health check: `http://localhost:8000/health`

## Notes
- Embedding model: `all-MiniLM-L6-v2` (sentence-transformers).
- Vector DB persisted at `data/vector_store.pkl` (also a human-readable `vector_store.txt`).
- Console Gemini demo: set `GOOGLE_API_KEY` env and run `python run_console.py`.
