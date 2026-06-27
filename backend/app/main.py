import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import settings
from app.llm import get_llm_client

logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    content: str | None


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    user_messages = [{"role": "user", "content": request.message}]
    try:
        llm = get_llm_client()
    except ValueError as e:
        # API key missing
        logger.error("LLM client init failed", exc_info=True)
        raise HTTPException(500, "Server is misconfigured") from e

    try:
        response = llm.complete(user_messages)
    except Exception as e:
        # LLM/network issue
        logger.error("LLM request failed", exc_info=True)
        raise HTTPException(502, "LLM request failed") from e
    return {"content": response.content}
