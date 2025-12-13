from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from src.application.ai_chat_service import AIChatService
from src.infrastructure.repository import SQLBudgetRepository
from src.infrastructure.db import get_session
from sqlalchemy.ext.asyncio import AsyncSession

from src.interface.dependencies import get_current_user
from src.interface.envelope import ResponseEnvelope

router = APIRouter()

class AIChatRequest(BaseModel):
    message: str
    context: dict = {}

class AIChatResponse(BaseModel):
    response: str

async def get_ai_service(session: AsyncSession = Depends(get_session)):
    repo = SQLBudgetRepository(session)
    return AIChatService(repo)

@router.post("/ai/chat", response_model=ResponseEnvelope[AIChatResponse])
async def chat_with_ai(
    request: AIChatRequest,
    service: AIChatService = Depends(get_ai_service),
    user: dict = Depends(get_current_user)
):
    response = await service.process_message(request.message, request.context)
    return ResponseEnvelope.success(data=AIChatResponse(response=response))

