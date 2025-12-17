from typing import List, Dict, Optional, Any, Tuple
import structlog
import numpy as np
import scipy.sparse as sp
from src.infrastructure.knowledge_graph.graph_provider import GraphProvider, get_graph_provider
from src.infrastructure.knowledge_graph.schema import Node, Edge, NodeType, EdgeType

logger = structlog.get_logger()

class GraphService:
    """
    Service for managing the Neuro-Symbolic Knowledge Graph.
    Delegates to GraphProvider (Neo4j or NetworkX).
    """
    def __init__(self, provider: Optional[GraphProvider] = None):
        self.provider = provider or get_graph_provider()
        logger.info("knowledge_graph_service_initialized", provider=type(self.provider).__name__)

    async def close(self):
        await self.provider.close()

    async def add_node(self, name: str, type: NodeType, **attrs):
        """Add a node to the knowledge graph."""
        node = Node(id=name, type=type, properties=attrs)
        await self.provider.add_node(node)

    async def add_edge(self, u: str, v: str, type: EdgeType, weight: float = 1.0, **attrs):
        """Add a directed edge between nodes."""
        edge = Edge(source_id=u, target_id=v, type=type, weight=weight, properties=attrs)
        await self.provider.add_edge(edge)

    async def get_node(self, name: str) -> Optional[Node]:
        return await self.provider.get_node(name)

    async def get_neighbors(self, node: str, edge_type: Optional[EdgeType] = None) -> List[str]:
        """Get neighbor IDs connected by a specific edge type."""
        neighbors = await self.provider.get_neighbors(node, edge_type)
        return [n.id for _, n in neighbors]

    async def get_categories_for_merchant(self, merchant: str) -> List[str]:
        """
        Retrieve categories directly linked to a merchant node.
        Merchant --BELONGS_TO--> Category
        """
        neighbors = await self.provider.get_neighbors(merchant, EdgeType.BELONGS_TO)
        categories = []
        for _, node in neighbors:
            if node.type == NodeType.CATEGORY:
                categories.append(node.id)
        return categories

    async def get_all_nodes(self, node_type: Optional[NodeType] = None) -> List[Node]:
        return await self.provider.get_all_nodes(node_type)

    async def get_all_edges(self, edge_type: Optional[EdgeType] = None) -> List[Edge]:
        return await self.provider.get_all_edges(edge_type)

    async def infer_category(self, merchant: str) -> Tuple[Optional[str], List[str]]:
        """
        Infer category using graph traversal.
        Returns: (Category, Path of Node IDs)
        """
        # 1. Direct lookup
        cats = await self.get_categories_for_merchant(merchant)
        if cats: 
             return cats[0], [merchant, cats[0]]
        
        # 2. Collaborative filtering (Nearest neighbor)
        # Get SIMILAR_TO neighbors
        similar_neighbors = await self.provider.get_neighbors(merchant, EdgeType.SIMILAR_TO)
        
        # Sort by weight descending
        similar_neighbors.sort(key=lambda x: x[0].weight, reverse=True)
        
        for _, sim_node in similar_neighbors:
            cats = await self.get_categories_for_merchant(sim_node.id)
            if cats: 
                logger.info("category_inferred_graph", source=merchant, similar=sim_node.id, inferred=cats[0])
                # Path: Merchant -> (Similar) -> Neighbor -> (Belongs) -> Category
                return cats[0], [merchant, sim_node.id, cats[0]]
            
        return None, []
        
    async def build_from_dict(self, merchant_category_map: Dict[str, str]):
        """
        Bulk load standard Merchant -> Category relationships.
        """
        count = 0
        for merchant, category in merchant_category_map.items():
            await self.add_node(merchant, NodeType.MERCHANT)
            await self.add_node(category, NodeType.CATEGORY)
            await self.add_edge(merchant, category, EdgeType.BELONGS_TO)
            count += 1
        logger.info("graph_built_from_dict", nodes=count*2, edges=count)

    async def find_hybrid_matches(self, vector_query: List[float], graph_constraints: Dict[str, Any], embedding_service: Any = None) -> List[Node]:
        """
        Hybrid Search: Vector Similarity + Graph Constraints.
        If nodes have 'embedding' property, we can rank them.
        """
        # 1. Expand constraints
        target_type = None
        if "type" in graph_constraints:
            try:
                target_type = NodeType(graph_constraints["type"])
            except: 
                pass
                
        # 2. Candidate Generation (Graph Filter)
        candidates = await self.provider.get_all_nodes(node_type=target_type)
        
        # 3. Apply other properties constraints (Metadata Filter)
        filtered = []
        for node in candidates:
            match = True
            for k, v in graph_constraints.items():
                if k == "type": continue
                if k == "must_be_category":
                    cats = await self.get_categories_for_merchant(node.id)
                    if v not in cats:
                        match = False
                        break
                elif node.properties.get(k) != v:
                     match = False
                     break
            if match:
                filtered.append(node)
                
        # 4. Vector Similarity (Re-ranking)
        # If vector_query provided, and we can compute similarity
        if vector_query and filtered:
            q_vec = np.array(vector_query)
            q_norm = np.linalg.norm(q_vec)
            
            scored_candidates = []
            for node in filtered:
                # Check for embedding in properties
                emb = node.properties.get("embedding")
                score = 0.0
                if emb and isinstance(emb, list):
                    # Compute Cosine Similarity
                    n_vec = np.array(emb)
                    n_norm = np.linalg.norm(n_vec)
                    if q_norm > 0 and n_norm > 0:
                        score = np.dot(q_vec, n_vec) / (q_norm * n_norm)
                
                # If no embedding, maybe use passed embedding_service to encode node.id?
                # That would be slow O(N) but accurate.
                # For this implementation, we rely on pre-computed embeddings or just return 0 score.
                # However, to satisfy "Hybrid Search", we should support it.
                elif embedding_service and hasattr(embedding_service, "encode"):
                     # On-the-fly encoding (expensive but correct for un-embedded nodes)
                     # In prod, we'd cache this.
                     n_vec = embedding_service.encode(node.id) # synchronous call?
                     n_vec = np.array(n_vec)
                     n_norm = np.linalg.norm(n_vec)
                     if q_norm > 0 and n_norm > 0:
                        score = np.dot(q_vec, n_vec) / (q_norm * n_norm)
                
                # Attach score to node temporarily? Or return tuple?
                # Pydantic models are frozen, so we must recreate node or return tuple.
                # Recreating node with new property:
                new_props = node.properties.copy()
                new_props['hybrid_score'] = float(score)
                new_node = Node(id=node.id, type=node.type, properties=new_props)
                scored_candidates.append(new_node)
            
            # Sort by score desc
            scored_candidates.sort(key=lambda x: x.properties.get('hybrid_score', 0), reverse=True)
            return scored_candidates
            
        return filtered
