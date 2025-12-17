import structlog
from typing import Optional
from src.infrastructure.knowledge_graph.graph_service import GraphService, NodeType, EdgeType

logger = structlog.get_logger()

class ContinualLearningService:
    """
    Service to handle online learning from user feedback.
    Updates the Knowledge Graph to reflect verified truths.
    """
    
    def __init__(self, graph_service: GraphService):
        self.graph = graph_service
        
    async def learn_feedback(self, description: str, corrected_category: str):
        """
        Ingest user feedback for a transaction description.
        
        Args:
            description: The transaction description (e.g., "Netflix")
            corrected_category: The user-verified category (e.g., "Entertainment")
        """
        # Normalize
        merchant_name = description.strip() 
        category_name = corrected_category.strip()
        
        if not merchant_name or not category_name:
            return

        logger.info("processing_feedback", merchant=merchant_name, category=category_name)
        
        # 1. Ensure Nodes Exist
        # GraphService doesn't have has_node, use get_node
        if not await self.graph.get_node(merchant_name):
            await self.graph.add_node(merchant_name, NodeType.MERCHANT)
            
        if not await self.graph.get_node(category_name):
            await self.graph.add_node(category_name, NodeType.CATEGORY)
            
        # 2. Add/Update Edge (BELONGS_TO)
        # We give user feedback high weight/confidence
        # Check if edge exists to log change?
        
        await self.graph.add_edge(
            merchant_name, 
            category_name, 
            EdgeType.BELONGS_TO, 
            weight=10.0 # High weight for explicit user feedback
        )
        
        # 3. (Future) Trigger asynchronous fine-tuning logic here
        # e.g. append to a "golden dataset" CSV for next training run
