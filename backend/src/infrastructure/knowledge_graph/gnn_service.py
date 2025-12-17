from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import scipy.sparse as sp
import structlog
from src.infrastructure.knowledge_graph.graph_service import GraphService, NodeType, EdgeType

logger = structlog.get_logger()

class GNNService:
    """
    Service for Graph Neural Network operations.
    Implements a simplified Graph Convolutional Network (GCN) layer 
    for semi-supervised node classification.
    """
    def __init__(self, graph_service: GraphService):
        self.graph_service = graph_service
        self.node_to_idx: Dict[str, int] = {}
        self.idx_to_node: Dict[int, str] = {}
        self.prediction_map: Dict[str, str] = {}
        self.is_trained = False
        
    async def train(self):
        """
        Train the GNN on the current graph state.
        Algorithm: Simplified GCN / Label Propagation by Diffusion.
        Y_{t+1} = D^{-1} * A * Y_t
        """
        nodes = await self.graph_service.get_all_nodes()
        edges = await self.graph_service.get_all_edges()
        
        if not nodes:
            logger.warning("gnn_train_empty_graph")
            return

        # 1. Build Index Map
        self.node_to_idx = {n.id: i for i, n in enumerate(nodes)}
        self.idx_to_node = {i: n.id for i, n in enumerate(nodes)}
        n_nodes = len(nodes)
        
        # 2. Extract Labels (Categories)
        # We treat Category nodes as one-hot labels for themselves
        # And labeled Merchant nodes as labels.
        # Collect all unique categories
        categories = sorted([n.id for n in nodes if n.type == NodeType.CATEGORY])
        cat_to_idx = {c: i for i, c in enumerate(categories)}
        n_classes = len(categories)
        
        if n_classes == 0:
            return

        # 3. Build Label Matrix Y (N x C)
        Y = np.zeros((n_nodes, n_classes))
        
        for i, node in enumerate(nodes):
            if node.type == NodeType.CATEGORY:
                if node.id in cat_to_idx:
                    Y[i, cat_to_idx[node.id]] = 1.0
                    
            elif node.type == NodeType.MERCHANT:
                # If merchant has implicit category via strict edges?
                # We let the graph propagate instead of hardcoding, 
                # unless we have ground truth (e.g. from SQL).
                # For GNN, we usually assume some labeled nodes.
                # Here we treat Categories as the sources of truth.
                pass
                
        # 4. Build Adjacency Matrix A (N x N)
        # We use lil_matrix for efficient construction
        A = sp.lil_matrix((n_nodes, n_nodes))
        
        for edge in edges:
            if edge.source_id in self.node_to_idx and edge.target_id in self.node_to_idx:
                u, v = self.node_to_idx[edge.source_id], self.node_to_idx[edge.target_id]
                weight = edge.weight
                A[u, v] = weight
                # Add self-loops? Usually yes for GCN
                
        # Add self-loops
        A.setdiag(1.0)
        
        # 5. Normalize A: D^{-1} * A
        # Row sum
        row_sums = np.array(A.sum(axis=1)).flatten()
        # Avoid division by zero
        row_sums[row_sums == 0] = 1.0
        D_inv = sp.diags(1.0 / row_sums)
        
        P = D_inv.dot(A)
        
        # 6. Propagate (Train)
        # Run K iterations (Diffusion)
        # This is equivalent to a K-layer simplified GCN
        K = 3
        Z = Y.copy()
        
        for k in range(K):
            Z = P.dot(Z)
            # Re-clamp known labels? (Label Spreading)
            # Z[known_mask] = Y[known_mask] 
        
        # 7. Store Predictions using argmax
        predicted_indices = np.argmax(Z, axis=1)
        max_probs = np.max(Z, axis=1)
        
        for i in range(n_nodes):
            node_id = self.idx_to_node[i]
            # specific threshold?
            if max_probs[i] > 0.0:
                cat_idx = predicted_indices[i]
                pred_cat = categories[cat_idx]
                self.prediction_map[node_id] = pred_cat
                
        self.is_trained = True
        logger.info("gnn_trained", nodes=n_nodes, classes=n_classes)

    async def predict_category(self, merchant: str) -> Optional[str]:
        if not self.is_trained:
            return None
        return self.prediction_map.get(merchant)
