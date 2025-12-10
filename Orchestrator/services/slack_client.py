import hashlib
import hmac
from typing import Optional

import httpx
from fastapi import HTTPException

from config import SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET


def verify_slack_request(request_body: bytes, timestamp: Optional[str], signature: Optional[str]) -> None:
    """
    Validate Slack request using signing secret.
    Raises HTTPException on failure.
    """
    if not timestamp or not signature:
        raise HTTPException(status_code=400, detail="Missing Slack request headers")

    if not SLACK_SIGNING_SECRET:
        raise HTTPException(status_code=500, detail="Slack signing secret is not configured.")

    req = f"v0:{timestamp}:{request_body.decode()}".encode()
    hash_value = "v0=" + hmac.new(SLACK_SIGNING_SECRET.encode(), req, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(hash_value, signature):
        raise HTTPException(status_code=400, detail="Invalid Slack signature")


async def send_to_slack(channel: str, text: str) -> None:
    """
    Send a message to a Slack channel.
    """
    if not SLACK_BOT_TOKEN:
        raise HTTPException(status_code=500, detail="Slack bot token is not configured.")

    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"channel": channel, "text": text}

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, headers=headers, timeout=10)
            resp.raise_for_status()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Error sending message to Slack: {exc}") from exc



