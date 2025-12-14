from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict
import os
import json

from src.application.ai_chat_service import AIChatService
from src.infrastructure.db import get_session
from src.interface.dependencies import get_current_user
from src.interface.envelope import ResponseEnvelope
from src.domain.user import User
from src.infrastructure.llm.gemini_adapter import GeminiAdapter

router = APIRouter()

class AIChatRequest(BaseModel):
    message: str
    context: dict = {}
    conversation_history: List[Dict[str, str]] = []

class AIChatResponse(BaseModel):
    response: str

@router.post("/ai/chat", response_model=ResponseEnvelope[AIChatResponse])
async def chat_with_ai(
    request: AIChatRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    # Initialize LLM Adapter if key is present
    api_key = os.getenv("GEMINI_API_KEY")
    llm_provider = None
    
    if api_key:
        try:
            llm_provider = GeminiAdapter(api_key)
        except Exception as e:
            # Fallback to heuristic if init fails
            pass

    # Instantiate Service
    service = AIChatService(session, user, llm_provider)
    
    # Generate Response
    response = await service.generate_response(request.message, request.conversation_history)
    
    return ResponseEnvelope.success(data=AIChatResponse(response=response))

@router.post("/ai/chat/stream")
async def chat_with_ai_stream(
    request: AIChatRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Streaming endpoint for AI chat. Returns Server-Sent Events (SSE) format.
    Each token is sent as: data: <token>\n\n
    """
    # Initialize LLM Adapter if key is present
    api_key = os.getenv("GEMINI_API_KEY")
    llm_provider = None
    
    if api_key:
        try:
            llm_provider = GeminiAdapter(api_key)
        except Exception as e:
            # Fallback to heuristic if init fails
            pass

    # Instantiate Service
    service = AIChatService(session, user, llm_provider)
    
    async def generate():
        """Generator function that yields SSE-formatted tokens."""
        try:
            async for token in service.generate_response_stream(request.message, request.conversation_history):
                # SSE format: data: <content>\n\n
                # We encode the token as JSON to handle special characters
                encoded_token = json.dumps(token)
                yield f"data: {encoded_token}\n\n"
        except Exception as e:
            # Send error in SSE format
            error_msg = json.dumps(f"Error: {str(e)}")
            yield f"data: {error_msg}\n\n"
        finally:
            # Send end marker
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )