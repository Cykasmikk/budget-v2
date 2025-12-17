from typing import List, Any, Optional, Set
from pydantic import BaseModel
import structlog
from src.infrastructure.knowledge_graph.graph_service import GraphService, EdgeType
from src.application.ai.model_service import ContinualModelService

logger = structlog.get_logger()

class PatternMatch(BaseModel):
    transaction: Any # Duck-typed transaction object
    score: float
    source: str # "vector", "graph", "hybrid"

class PatternDetector:
    """
    Hybrid Neuro-Symbolic Pattern Detector.
    Combines Vector Search (Embeddings) with Knowledge Graph connections.
    """
    def __init__(self, embedding_service, model_service: ContinualModelService, graph_service: Optional[GraphService] = None):
        self.embedding_service = embedding_service
        self.model_service = model_service
        self.graph_service = graph_service

    async def detect_patterns(self, query: str, transactions: List[Any], threshold: float = 0.5) -> List[PatternMatch]:
        """
        Find patterns in transactions that match the query.
        Uses Hybrid Search: Result = Vector Similarity + Graph Boost.
        """
        query_vec = self.embedding_service.encode(query)
        matches = []
        
        # 0. Expand Query via Graph (Hybrid)
        graph_related_terms: Set[str] = set()
        if self.graph_service:
            # Get direct synonyms/similars
            neighbors = await self.graph_service.get_neighbors(query, EdgeType.SIMILAR_TO)
            graph_related_terms.update(neighbors)
            
            # Get Sibling merchants (Same Category)
            # This handles "Netflix" -> Category "Streaming" -> "Hulu"
            # So searching for "Netflix" could potentially find "Hulu" if we want that, 
            # OR searching for "Streaming" finds both.
            # Assuming query might be a Category name.
            # Check if query is a category node?
            # For now, simple neighbor check is safer to strictly boost.
        
        for tx in transactions:
            description = getattr(tx, "description", "")
            if not description: continue
            
            # 1. Vector Score
            tx_vec = self.embedding_service.encode(description) 
            vector_score = self.embedding_service.similarity(query_vec, tx_vec)
            
            # 2. Graph Boost
            graph_boost = 0.0
            source = "vector"
            
            # Check literal overlap with graph terms
            # Simple containment check
            if any(term.lower() in description.lower() for term in graph_related_terms):
                graph_boost = 0.25
                source = "hybrid"
            
            # Check if description ITSELF is in the graph as a node related to query
            if self.graph_service:
                # Direct check: is there a path?
                # This is expensive for all pairs.
                # Optimization: Check if tx description is a neighbor of query
                if description in graph_related_terms: # Exact match
                     graph_boost = 0.3
                
            # 3. Model Probability (Posterior)
            # We check P(category | description) - if high confidence, boost matching
            _, model_conf, _ = self.model_service.predict_proba(description)
            model_boost = model_conf * 0.2
            
            # Dynamic weights
            final_score = (vector_score * 0.6) + graph_boost + model_boost
            
            if final_score >= threshold:
                matches.append(PatternMatch(
                    transaction=tx,
                    score=final_score,
                    source=source
                ))
        
        # Sort by score descending
        matches.sort(key=lambda x: x.score, reverse=True)
        return matches
