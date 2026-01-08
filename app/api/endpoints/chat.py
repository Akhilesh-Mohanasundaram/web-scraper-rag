from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.chat_service import chat_service

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

# CHANGED: 'async def' -> 'def' (Fixes blocking stream issue)
@router.post("/stream")
def chat_stream(request: ChatRequest):
    """
    Streams the chatbot response token by token.
    Runs in a threadpool to support synchronous LLM calls.
    """
    if not request.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    return StreamingResponse(
        chat_service.stream_chat(request.message),
        media_type="text/event-stream"
    )