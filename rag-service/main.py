import os
from fastapi import FastAPI, HTTPException
from fastapi import Query
from pydantic import BaseModel
from rag.rag_engine import RagEngine

app = FastAPI(title="RAG Service")

# Khởi tạo RagEngine khi ứng dụng start
rag_engine: RagEngine | None = None


@app.on_event("startup")
def startup_event():
    global rag_engine
    try:
        rag_engine = RagEngine()
        # Auto-ingest a default dataset if vector DB is empty
        if not rag_engine.vector_store.data.get("vectors"):
            default_data_path = os.getenv("DEFAULT_DATA_PATH", "data1.txt")
            abs_path = os.path.abspath(default_data_path)
            if os.path.exists(abs_path):
                try:
                    print(f"[INFO] Auto-ingest from {abs_path}")
                    rag_engine.vector_store.reset()  # đảm bảo sạch trước khi ingest mặc định
                    rag_engine.ingest(abs_path)
                except Exception as e:
                    print(f"[WARN] Auto-ingest failed: {e}")
            else:
                print(f"[INFO] Skip auto-ingest: file not found {abs_path}")
        else:
            print("[INFO] Vector DB already loaded, skip auto-ingest")
    except Exception as e:
        # Để app vẫn khởi động (có thể ingest sau), log lỗi khởi tạo nếu có
        print(f"RagEngine init failed: {e}")
        rag_engine = RagEngine()  # thử khởi tạo lại tối thiểu


class IngestRequest(BaseModel):
    file_path: str


class RetrieveRequest(BaseModel):
    query: str
    top_k: int = 1
    include_prompt: bool = False


@app.post("/ingest")
def ingest(request: IngestRequest):
    if rag_engine is None:
        raise HTTPException(status_code=500, detail="RAG Engine not initialized")
    try:
        rag_engine.ingest(request.file_path)
        return {"status": "ok"}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint tiện dụng: ingest qua query string để tránh lỗi JSON escape trên Windows
@app.get("/ingest-txt")
def ingest_txt(path: str = Query(..., description="Đường dẫn file .txt")):
    if rag_engine is None:
        raise HTTPException(status_code=500, detail="RAG Engine not initialized")
    try:
        rag_engine.ingest(path)
        return {"status": "ok", "path": path}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/retrieve")
def retrieve(request: RetrieveRequest):
    if rag_engine is None:
        raise HTTPException(status_code=500, detail="RAG Engine not initialized")
    try:
        results = rag_engine.retrieve(request.query, top_k=request.top_k)
        response = {"results": results}
        if request.include_prompt:
            prompt = rag_engine.generate_prompt(request.query, results)
            response["prompt"] = prompt
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class SearchRequest(BaseModel):
    query: str
    top_k: int = 1


class SearchResponse(BaseModel):
    context: str
    results: list


@app.post("/search", response_model=SearchResponse)
def search(request: SearchRequest):
    if rag_engine is None:
        raise HTTPException(status_code=500, detail="RAG Engine not initialized")
    try:
        results = rag_engine.retrieve(request.query, top_k=request.top_k)
        context_text = "\n\n".join([r.get("chunk", "") for r in results])
        return {"context": context_text, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)