from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict
import os
import json

from src.application.ai_chat_service import AIChatService
from src.application.ai.simulator_ai import SimulatorAI, SimulatorAction
from src.infrastructure.db import get_session
from src.interface.dependencies import get_current_user, get_scenario_planner
from src.interface.envelope import ResponseEnvelope
from src.domain.user import User
from src.infrastructure.llm.gemini_adapter import GeminiAdapter
from src.application.ai.scenario_planner import ScenarioPlanner, ScenarioPlan
from src.application.ai.explanation_service import ExplanationService
from src.application.neuro_symbolic.hybrid_reasoner import HybridReasoner
from src.application.neuro_symbolic.hybrid_reasoner import HybridReasoner
from src.interface.dependencies import get_explanation_service, get_continual_model_service, get_hybrid_reasoner, get_response_verifier
from src.application.ai.response_verifier import ResponseVerifier

router = APIRouter()

class AIChatRequest(BaseModel):
    message: str
    context: dict = {}
    conversation_history: List[Dict[str, str]] = []

class AIChatResponse(BaseModel):
    response: str
    explanation: str | None = None

@router.post("/ai/chat", response_model=ResponseEnvelope[AIChatResponse])
async def chat_with_ai(
    request: AIChatRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    response_verifier: ResponseVerifier = Depends(get_response_verifier)
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
    service = AIChatService(session, user, llm_provider, response_verifier=response_verifier)
    
    # Generate Response
    content, explanation = await service.generate_response(request.message, request.conversation_history)
    
    return ResponseEnvelope.success(data=AIChatResponse(response=content, explanation=explanation))

@router.post("/ai/chat/stream")
async def chat_stream(
    request: AIChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
    explanation_service: ExplanationService = Depends(get_explanation_service),
    hybrid_reasoner: HybridReasoner = Depends(get_hybrid_reasoner)
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
    service = AIChatService(
        session=db, 
        user=user, 
        llm_provider=llm_provider,
        explanation_service=explanation_service,
        hybrid_reasoner=hybrid_reasoner
    )
    
    async def generate():
        """Generator function that yields SSE-formatted tokens."""
        try:
            # Use the meta-aware stream method
            async for item in service.generate_response_stream_with_meta(request.message, request.conversation_history):
                # SSE format: data: <json_content>\n\n
                encoded_item = json.dumps(item)
                yield f"data: {encoded_item}\n\n"
        except Exception as e:
            # Send error in SSE format
            error_msg = json.dumps({"type": "error", "content": str(e)})
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

class SimulatorRequest(BaseModel):
    scenario: str

@router.post("/ai/simulator/parse", response_model=ResponseEnvelope[SimulatorAction])
async def parse_simulation_scenario(
    request: SimulatorRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Parses a natural language scenario into a structured simulation action using LLM.
    """
    # Initialize SimulatorAI (Reuse API key from env)
    # In production, this should be a singleton or dependency
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        raise HTTPException(status_code=503, detail="AI Service Config Missing")
        
    simulator = SimulatorAI(api_key=api_key)
    
    action = await simulator.parse_scenario(request.scenario)
    
    if not action:
        raise HTTPException(status_code=422, detail="Failed to parse scenario")
        
    return ResponseEnvelope.success(data=action)

@router.post("/ai/simulator/plan", response_model=ResponseEnvelope[ScenarioPlan])
async def plan_simulation_scenario(
    request: SimulatorRequest,
    planner: ScenarioPlanner = Depends(get_scenario_planner),
    user: User = Depends(get_current_user)
):
    """
    Decomposes a scenario into a multi-step plan.
    """
    plan = await planner.generate_plan(request.scenario)
    
    if not plan:
        raise HTTPException(status_code=422, detail="Failed to generate plan")
        
    return ResponseEnvelope.success(data=plan)

class ExplainRequest(BaseModel):
    description: str

@router.post("/ai/explain/classify")
async def explain_classification(
    request: ExplainRequest,
    explanation_service: ExplanationService = Depends(get_explanation_service),
    hybrid_reasoner: HybridReasoner = Depends(get_hybrid_reasoner),
    user: User = Depends(get_current_user)
):
    """
    Explain the classification of a transaction description.
    """
    # 1. Run Hybrid Reasoning
    # We pass empty rules list for now, or fetch from DB (RuleRepository)
    # Ideally inject RuleRepository iterate rules. For V1 assume no strict rules or fetch simple.
    # To keep it simple: pass empty rules, so we rely on Neural + Graph (which is what we want to explain mostly)
    
    result = await hybrid_reasoner.refine_prediction(request.description, rules=[])
    
    # 2. Generate Explanation
    # We construct a mock transaction data dict if needed by explanation service
    # Or update explanation service to accept just description
    
    explanation = await explanation_service.generate_explanation(result, {"description": request.description})
    
    return ResponseEnvelope.success(data=explanation)