from fastapi import FastAPI
from pydantic import BaseModel
from app.llm import get_llm_client
from app.config import settings
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException


class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    # local test
    allow_origins=[settings.frontend_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    llm = get_llm_client()
    user_messages = [{"role": "user", "content": request.message}]
    try:
        response = llm.complete(user_messages)
    except Exception as e:
        # Bad gateway exception
        raise HTTPException(status_code=502, detail="LLM request failed") from e
    return {"reply": response}
