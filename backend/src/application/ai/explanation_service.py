from typing import List, Dict, Any, Optional
import structlog
from src.application.symbolic.proof_generator import ProofGenerator
from src.application.neuro_symbolic.hybrid_reasoner import ReasoningResult
from src.application.ai.model_service import ContinualModelService

logger = structlog.get_logger()

from src.infrastructure.knowledge_graph.graph_service import GraphService, EdgeType

class ExplanationService:
    """
    Unified Neuro-Symbolic Explanation Framework.
    Aggregates Neural, Symbolic, and Graph evidence.
    Supports Counterfactual analysis.
    """
    def __init__(self, proof_generator: ProofGenerator, model_service: ContinualModelService, graph_service: Optional[GraphService] = None):
        self.proof_generator = proof_generator
        self.model_service = model_service
        self.graph_service = graph_service

    async def generate_explanation(self, reasoning_result: ReasoningResult, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate detailed explanation for a decision.
        """
        # 1. Base Proof (Symbolic/Graph/Neural steps)
        proof = self.proof_generator.generate_proof(reasoning_result)
        
        # 2. Add Counterfactuals (if applicable for Neural)
        counterfactuals = []
        if reasoning_result.source == "neural" and reasoning_result.confidence < 0.95:
             counterfactuals = await self.generate_counterfactuals(transaction_data.get("description", ""), reasoning_result.category)
            
        return {
            "decision": reasoning_result.category,
            "confidence": reasoning_result.confidence,
            "proof": {**proof, "counterfactuals": counterfactuals}, # Inject into proof object for frontend
            "counterfactuals": counterfactuals
        }

    async def generate_counterfactuals(self, description: str, current_category: str) -> List[str]:
        """
        Explore what-if scenarios using Graph Neighbors and Model perturbation.
        """
        results = []
        
        # 1. Graph Perturbation
        if self.graph_service:
            # Find similar merchants
            neighbors = await self.graph_service.get_neighbors(description, EdgeType.SIMILAR_TO)
            for neighbor in neighbors[:3]: # Limit to 3
                # Check neighbor's probable category
                cat, _ = await self.graph_service.infer_category(neighbor)
                if cat and cat != current_category:
                    results.append(f"If merchant was '{neighbor}', category would be '{cat}' (Graph)")

        # 2. Model Perturbation (Keywords)
        keywords = ["Restaurant", "Fuel", "Rent", "Subscription"]
        
        for k in keywords:
            if k.lower() in description.lower(): continue
            
            modified = f"{description} {k}"
            cat, conf, _ = self.model_service.predict_proba(modified)
            if cat != current_category:
                results.append(f"If description contained '{k}', category would be '{cat}' ({conf:.2f})")
                
        return results
