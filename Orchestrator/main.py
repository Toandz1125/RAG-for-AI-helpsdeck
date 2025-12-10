import logging

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from google.api_core import exceptions as google_exceptions

from config import GEMINI_API_KEY, GEMINI_MODEL, RAG_URL
from services.gemini_client import GeminiClient
from services.llm_client import LLMClient
from services.rag_client import RagClient
from services.slack_client import send_to_slack, verify_slack_request


app = FastAPI(title="AI Orchestrator")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

rag_client = RagClient(RAG_URL)
gemini = GeminiClient(GEMINI_API_KEY, GEMINI_MODEL)

# Cache để tránh xử lý lại cùng một event (deduplication)
processed_events = set()


# ---- REQUEST MODEL ----
class UserQuery(BaseModel):
    question: str


def build_prompt(question: str, context: str) -> str:
    return f"""
bạn đang là một trợ lý AI 

Hãy trả lời câu hỏi:
{question}

Ngữ cảnh:
{context}

Hãy trở lời dựa trên ngữ cảnh và câu hỏi ở trên .
"""


@app.post("/promt")
def get_promt(query: UserQuery):
    # 1. Lấy context từ RAG
    rag_result = rag_client.retrieve(query.question)

    # Context từ RAG đã là tổng hợp của các chunk rồi
    context = rag_result.get("context", "")

    # 2. Build final prompt
    final_prompt = f"""
You are an AI assistant.

User question:
{query.question}

Relevant context:
{context}

Please answer clearly based on the context.
"""
    return final_prompt

@app.post("/ask")
def ask_ai(query: UserQuery):
    # 1. Lấy context từ RAG
    rag_result = rag_client.retrieve(query.question)

    # Context từ RAG đã là tổng hợp của các chunk rồi
    context = rag_result.get("context", "")

    final_prompt = build_prompt(query.question, context)

    # 3. Gọi LLM Worker
    llm_answer = gemini.generate(final_prompt)

    # 4. Trả kết quả
    return {
        "finalpromt": final_prompt,
        "answer": llm_answer,
    }


@app.post("/slack/events")
async def slack_events(request: Request):
    raw_body = await request.body()
    headers = {
        "X-Slack-Request-Timestamp": request.headers.get("X-Slack-Request-Timestamp"),
        "X-Slack-Signature": request.headers.get("X-Slack-Signature"),
        "Content-Type": request.headers.get("Content-Type"),
    }
    try:
        payload = await request.json()
    except Exception as exc:  # pragma: no cover - debug logging path
        logger.error("Slack payload parse error: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Slack URL verification: respond with challenge before signature checks
    if payload.get("type") == "url_verification":
        logger.info("Slack url_verification received")
        return {"challenge": payload.get("challenge")}

    timestamp = headers["X-Slack-Request-Timestamp"]
    signature = headers["X-Slack-Signature"]

    try:
        verify_slack_request(raw_body, timestamp, signature)
    except HTTPException as exc:
        logger.error(
            "Slack signature verification failed: %s | headers=%s | body=%s",
            exc.detail,
            headers,
            raw_body.decode(errors="replace"),
        )
        raise

    event = payload.get("event", {})
    logger.info("Slack event received: type=%s subtype=%s", event.get("type"), event.get("subtype"))

    event_type = event.get("type")
    bot_id = event.get("bot_id")

    if event_type in {"message", "app_mention"} and not bot_id:
        # Deduplication: Check if we've already processed this event
        event_id = event.get("client_msg_id") or event.get("event_ts")
        if event_id:
            if event_id in processed_events:
                logger.info("Duplicate event ignored: event_id=%s", event_id)
                return {"ok": True}
            # Mark event as processed immediately to prevent race condition
            processed_events.add(event_id)
            # Cleanup old events (keep last 1000 events to prevent memory leak)
            if len(processed_events) > 1000:
                processed_events.clear()
                logger.info("Cleared processed_events cache")
        
        channel = event.get("channel")
        raw_text = event.get("text", "")
        # Remove leading bot mention if any (for app_mention events)
        text = raw_text
        if event_type == "app_mention":
            text = " ".join(part for part in raw_text.split() if not part.startswith("<@") and part != "")
            text = text.strip()

        if not channel:
            raise HTTPException(status_code=400, detail="Missing Slack channel")

        logger.info("Calling RAG at %s/search with query=%s", RAG_URL, text)
        rag_result = rag_client.retrieve(text)
        logger.info("RAG response: %s", rag_result)
        # Context từ RAG đã là tổng hợp của các chunk rồi, không cần join lại
        context = rag_result.get("context", "")

        final_prompt = build_prompt(text, context)
        try:
            llm_answer = gemini.generate(final_prompt)
        except google_exceptions.ResourceExhausted as exc:
            logger.warning("Gemini quota exceeded, fallback to RAG context: %s", exc)
            llm_answer = f"Dựa trên thông tin có sẵn:\n\n{context}" if context else "Xin lỗi, hệ thống đang tạm thời quá tải. Vui lòng thử lại sau."
        except Exception as exc:
            logger.error("Gemini error, fallback to RAG context: %s", exc, exc_info=True)
            llm_answer = f"Dựa trên thông tin có sẵn:\n\n{context}" if context else "Xin lỗi, đã xảy ra lỗi khi xử lý câu hỏi. Vui lòng thử lại sau."

        logger.info("Sending answer back to Slack channel=%s", channel)
        await send_to_slack(channel, llm_answer)
        logger.info("Sent to Slack successfully")
    else:
        logger.info("Ignored Slack event (not a user message)")

    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=9000, reload=True)
