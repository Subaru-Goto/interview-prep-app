import logging

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypdf.errors import PdfReadError

from app.config import settings
from app.cv_parser import parse_cv
from app.input_guard import InvalidInput
from app.interview_engine import finish_interview, reply, start_interview
from app.llm import get_llm_client
from app.schemas import Scorecard
from app.session_store import SessionNotFound

logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    content: str | None


class StartRequest(BaseModel):
    cv_text: str
    jd_text: str

class StartResponse(BaseModel):
    session_id: str
    first_question: str

class FinishRequest(BaseModel):
    session_id: str

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


@app.post("/upload-cv")
async def upload_cv(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(400, "Only PDF files are accepted")

    file_contents = await file.read()
    if len(file_contents) > settings.max_cv_bytes:
        raise HTTPException(413, "File is too large")

    try:
        cv_data = parse_cv(file_contents)
        return cv_data
    except PdfReadError as e:
        logger.error("CV parsing failed", exc_info=True)
        raise HTTPException(422, "CV parsing failed") from e

@app.post("/start", response_model=StartResponse)
def start(request: StartRequest):
    try:
        session_id, question = start_interview(request.cv_text, request.jd_text)
    except InvalidInput as e:
        raise HTTPException(400, str(e)) from e
    return {"session_id": session_id, "first_question": question}


class ReplyRequest(BaseModel):
    session_id: str
    answer: str

class ReplyResponse(BaseModel):
    done: bool
    next_question: str | None

@app.post("/reply", response_model=ReplyResponse)
def submit_reply(request: ReplyRequest):
    try:
        done, question = reply(request.session_id, request.answer)
    except InvalidInput as e:
        raise HTTPException(400, str(e)) from e
    except SessionNotFound as e:
        raise HTTPException(404, str(e)) from e
    return {"done": done, "next_question": question}

@app.post("/finish", response_model=Scorecard)
def finish_and_feedback(request: FinishRequest):
    try:
        scorecard = finish_interview(request.session_id)
    except SessionNotFound as e:
        raise HTTPException(404, str(e)) from e
    except Exception as e:
        logger.error("Judge request failed", exc_info=True)
        raise HTTPException(502, "Judge failed to produce a valid scorecard") from e
    return scorecard
