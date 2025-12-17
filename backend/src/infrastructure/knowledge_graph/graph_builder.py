from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
from typing import List, Dict, Any

from src.infrastructure.knowledge_graph.graph_service import GraphService
from src.infrastructure.knowledge_graph.schema import NodeType, EdgeType

logger = structlog.get_logger()

class GraphBuilder:
    """
    Builds and synchronizes the Knowledge Graph from the SQL Database.
    """
    def __init__(self, session: AsyncSession, graph_service: GraphService):
        self.session = session
        self.graph_service = graph_service

    async def build_initial_graph(self):
        """
        Loads all transactions and builds the base graph:
        Merchant -> BELONGS_TO -> Category
        """
        logger.info("starting_graph_build")
        
        # 1. Fetch distinct Merchant -> Category mappings from approved transactions
        # usage of "transactions" table assumed
        query = text("""
            SELECT DISTINCT merchant, category 
            FROM transactions 
            WHERE category IS NOT NULL 
            AND merchant IS NOT NULL
        """)
        
        result = await self.session.execute(query)
        rows = result.fetchall()
        
        count = 0
        for row in rows:
            merchant = row[0]
            category = row[1]
            
            # Add Merchant Node
            await self.graph_service.add_node(
                name=merchant, 
                type=NodeType.MERCHANT, 
                source="sql_history"
            )
            
            # Add Category Node
            await self.graph_service.add_node(
                name=category, 
                type=NodeType.CATEGORY,
                source="sql_history"
            )
            
            # Add Edge
            await self.graph_service.add_edge(
                u=merchant, 
                v=category, 
                type=EdgeType.BELONGS_TO,
                weight=1.0
            )
            count += 1
            
        logger.info("graph_build_complete", imported_relations=count)

    async def sync_transaction(self, merchant: str, category: str):
        """
        Incremental update when a new transaction is categorized.
        """
        if not merchant or not category:
            return
            
        await self.graph_service.add_node(merchant, NodeType.MERCHANT)
        await self.graph_service.add_node(category, NodeType.CATEGORY)
        await self.graph_service.add_edge(merchant, category, EdgeType.BELONGS_TO)
