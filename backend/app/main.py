from fastapi import FastAPI
from pydantic import BaseModel
from app.llm import get_llm_client

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

app = FastAPI()

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    llm = get_llm_client()
    user_messages = [{"role": "user", "content": request.message}]
    response = llm.complete(user_messages)
    return {"reply": response}
