from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Dict
from src.interface.dependencies import get_db, get_current_user
from src.domain.user import User
from src.application.ai_chat_service import AIChatService

router = APIRouter(tags=["AI Chat"])

class ChatRequest(BaseModel):
    message: str
    conversation_history: List[Dict[str, str]] = []

class ChatResponse(BaseModel):
    response: str

@router.post("/ai/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    AI Chat endpoint that provides contextually aware responses about user's budget data.
    """
    try:
        service = AIChatService(db, user)
        response = await service.generate_response(
            request.message,
            request.conversation_history
        )
        return ChatResponse(response=response)
    except Exception as e:
        import structlog
        logger = structlog.get_logger()
        logger.exception("ai_chat_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate AI response: {str(e)}")

