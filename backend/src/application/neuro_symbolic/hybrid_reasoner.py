from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import structlog
from src.application.ai.model_service import ContinualModelService
from src.infrastructure.knowledge_graph.graph_service import GraphService
from src.infrastructure.knowledge_graph.gnn_service import GNNService

logger = structlog.get_logger()

class ReasoningResult(BaseModel):
    category: str
    confidence: float
    source: str  # "neural", "symbolic_override", "graph_inference"
    is_verified: bool
    graph_path: List[str] = []

class HybridReasoner:
    """
    Neuro-Symbolic Hybrid Reasoner.
    Orchestrates the loop: Neural Suggests -> Symbolic Verifies -> Graph Refines.
    """
    def __init__(self, model_service: ContinualModelService, graph_service: Optional[GraphService] = None, gnn_service: Optional[GNNService] = None):
        self.model_service = model_service
        self.graph_service = graph_service
        self.gnn_service = gnn_service

    async def refine_prediction(self, description: str, rules: List[Dict[str, Any]], threshold: float = 0.8) -> ReasoningResult:
        """
        Refine the category prediction using symbolic verification and graph inference.
        """
        # 1. Neural Prediction (Calibrated)
        pred_category, confidence, _ = self.model_service.predict_proba(description)
        
        # 2. Symbolic Verification (Rule Check)
        # Check if any strict rule contradicts or overrides this
        # Simple Logic: If a rule matches the pattern, it MUST be that category.
        # If the neural prediction differs, the rule wins.
        
        matched_rule_category = None
        for rule in rules:
            pattern = rule.get("pattern", "")
            if pattern and pattern.lower() in description.lower(): # Simple substring match as proxy for rule engine
                matched_rule_category = rule.get("category")
                break
        
        if matched_rule_category:
            if matched_rule_category != pred_category:
                logger.info("symbolic_override", description=description, neural=pred_category, rule=matched_rule_category)
                return ReasoningResult(
                    category=matched_rule_category,
                    confidence=1.0,
                    source="symbolic_override",
                    is_verified=True
                )
            else:
                # Neural matched the rule, so it's verified
                return ReasoningResult(
                    category=pred_category,
                    confidence=1.0, # Boost to 1.0 since it matches rule
                    source="neural",
                    is_verified=True
                )

        # 3. Graph Refinement (Low Confidence Fallback)
        if confidence < threshold and self.graph_service:
            inferred_cat, path = await self.graph_service.infer_category(description)
            if inferred_cat:
                logger.info("graph_inference_refinement", description=description, original=pred_category, inferred=inferred_cat)
                return ReasoningResult(
                    category=inferred_cat,
                    confidence=max(confidence, 0.7), # Boost confidence slightly for graph
                    source="graph_inference",
                    is_verified=False, # Graph is heuristic, not strict proof
                    graph_path=path
                )
        
            # 3b. GNN Prediction (Node Classification)
            if self.gnn_service:
                gnn_cat = await self.gnn_service.predict_category(description)
                if gnn_cat:
                    logger.info("gnn_inference_refinement", description=description, original=pred_category, inferred=gnn_cat)
                    return ReasoningResult(
                        category=gnn_cat,
                        confidence=0.65,
                        source="gnn_inference",
                        is_verified=False
                    )

        # 4. Final Result (Neural)
        return ReasoningResult(
            category=pred_category,
            confidence=confidence,
            source="neural",
            is_verified=False
        )

    async def validate_claim_plausibility(self, entity: str, context_text: str) -> float:
        """
        Validate if an entity is plausibly associated with the context.
        Uses GNN service via graph_service or model embeddings.
        """
        # 1. Direct Graph Check
        if self.graph_service:
            # Check if node exists and has edges related to context keywords
            # Mocking the actual specific query for now, assuming graph_service has relevance check
            pass
            
        # 2. Neural Embedding Check (Model Service)
        # Does the entity embedding align with the context embedding?
        if self.model_service and self.model_service.embedding_service:
            emb = self.model_service.embedding_service
            entity_vec = emb.encode(entity)
            context_vec = emb.encode(context_text)
            sim = emb.similarity(entity_vec, context_vec)
            return sim
            
        return 0.5 # Default neutral if no services
