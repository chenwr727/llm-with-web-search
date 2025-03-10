from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from api.dependencies import get_chat_service
from api.models import ChatRequest
from api.services import ChatService
from utils.logger import logger

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "healthy"}


@router.post("/chat")
async def chat(request: ChatRequest, chat_service: ChatService = Depends(get_chat_service)):
    try:
        return StreamingResponse(
            chat_service.stream_response(request.messages, request.needs_crawler, request.needs_filter),
            media_type="text/plain",
        )
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
