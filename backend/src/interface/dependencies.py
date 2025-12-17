from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.db import get_session
from src.application.auth_service import AuthService
from src.application.context import set_tenant_id, set_user_id
from src.domain.user import User
from functools import lru_cache
from src.application.ai.embedding_service import EmbeddingService
from src.infrastructure.llm.scenario_store import ScenarioStore
from src.application.ai.simulator_ai import SimulatorAI
from src.application.ai.scenario_planner import ScenarioPlanner
from src.application.ai.model_service import ContinualModelService
from src.application.ai.calibration_service import CalibrationService
from src.application.symbolic.proof_generator import ProofGenerator
from src.application.ai.explanation_service import ExplanationService
from src.infrastructure.knowledge_graph.graph_service import GraphService
from src.infrastructure.knowledge_graph.graph_provider import get_graph_provider
from src.infrastructure.knowledge_graph.gnn_service import GNNService
from src.infrastructure.knowledge_graph.gnn_service import GNNService
from src.application.neuro_symbolic.hybrid_reasoner import HybridReasoner
from src.application.ai.response_verifier import ResponseVerifier

# Standard naming convention alias
get_db = get_session

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    service = AuthService(db)
    service = AuthService(db)
    user = await service.get_user_by_session(session_id)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired or invalid")

    # Set Context for Repositories
    set_tenant_id(user.tenant_id)
    set_user_id(user.id)
    
    return user

@lru_cache()
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()

@lru_cache()
def get_scenario_store() -> ScenarioStore:
    # Requires embedding service
    emb_service = get_embedding_service()
    return ScenarioStore(embedding_service=emb_service)

@lru_cache()
def get_simulator_ai() -> SimulatorAI:
    store = get_scenario_store()
    import os
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    return SimulatorAI(api_key=api_key, scenario_store=store)

@lru_cache()
def get_scenario_planner() -> ScenarioPlanner:
    sim_ai = get_simulator_ai()
    emb = get_embedding_service()
    return ScenarioPlanner(simulator_ai=sim_ai, embedding_service=emb)

@lru_cache()
def get_calibration_service() -> CalibrationService:
    return CalibrationService()

@lru_cache()
def get_continual_model_service() -> ContinualModelService:
    emb_service = get_embedding_service()
    cal_service = get_calibration_service()
    return ContinualModelService(embedding_service=emb_service, calibration_service=cal_service)

@lru_cache()
def get_proof_generator() -> ProofGenerator:
    return ProofGenerator()

@lru_cache()
def get_explanation_service() -> ExplanationService:
    proof_gen = get_proof_generator()
    model_service = get_continual_model_service()
    return ExplanationService(proof_generator=proof_gen, model_service=model_service)

@lru_cache()
def get_graph_service() -> GraphService:
    # Use factory or default
    provider = get_graph_provider()
    return GraphService(provider=provider)

@lru_cache()
def get_gnn_service() -> GNNService:
    graph_service = get_graph_service()
    return GNNService(graph_service=graph_service)

@lru_cache()
def get_hybrid_reasoner() -> HybridReasoner:
    model_service = get_continual_model_service()
    graph_service = get_graph_service()
    gnn_service = get_gnn_service()
    return HybridReasoner(model_service=model_service, graph_service=graph_service, gnn_service=gnn_service)

@lru_cache()
def get_response_verifier() -> ResponseVerifier:
    emb = get_embedding_service()
    reasoner = get_hybrid_reasoner()
    return ResponseVerifier(embedding_service=emb, hybrid_reasoner=reasoner)

# Alias for route protection
RequireAuth = Depends(get_current_user)
