from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
import os
import structlog
import networkx as nx
from neo4j import GraphDatabase, AsyncGraphDatabase

from src.infrastructure.knowledge_graph.schema import Node, Edge, NodeType, EdgeType

logger = structlog.get_logger()

class GraphProvider(ABC):
    """
    Abstract interface for Graph Database operations.
    Supports pluggable backends (NetworkX, Neo4j, etc.).
    """
    
    @abstractmethod
    async def get_all_nodes(self, node_type: Optional[NodeType] = None) -> List[Node]:
        pass

    @abstractmethod
    async def get_all_edges(self, edge_type: Optional[EdgeType] = None) -> List[Edge]:
        pass

    @abstractmethod
    async def save_graph(self) -> None:
        pass
    
    @abstractmethod
    async def add_node(self, node: Node) -> None:
        pass
    
    @abstractmethod
    async def add_edge(self, edge: Edge) -> None:
        pass
    
    @abstractmethod
    async def get_node(self, node_id: str) -> Optional[Node]:
        pass
        
    @abstractmethod
    async def get_neighbors(self, node_id: str, edge_type: Optional[EdgeType] = None) -> List[Tuple[Edge, Node]]:
        """Returns list of (Edge, TargetNode) tuples."""
        pass

    @abstractmethod
    async def close(self):
        pass

class NetworkXProvider(GraphProvider):
    """
    In-memory / Local File Graph Provider using NetworkX.
    Good for local dev without Docker overhead.
    """
    def __init__(self, persistence_path: Optional[str] = "budget_graph.gml"):
        self.graph = nx.MultiDiGraph()
        self.persistence_path = persistence_path
        self._load_graph()
        
    def _load_graph(self):
        if self.persistence_path and os.path.exists(self.persistence_path):
            try:
                self.graph = nx.read_gml(self.persistence_path)
                logger.info("loaded_graph_from_disk", path=self.persistence_path, nodes=self.graph.number_of_nodes())
            except Exception as e:
                logger.error("failed_to_load_graph", error=str(e))
                
    def _save_graph(self):
        if self.persistence_path:
            try:
                # GML has trouble with some python types, so we might need string conversion
                # For MVP we just try raw
                nx.write_gml(self.graph, self.persistence_path)
            except Exception:
                # Fallback or silent failure for speed? logging is safer
                pass

    async def save_graph(self) -> None:
        self._save_graph()

    async def add_node(self, node: Node) -> None:
        self.graph.add_node(node.id, type=node.type.value, **node.properties)
        self._save_graph()

    async def add_edge(self, edge: Edge) -> None:
        self.graph.add_edge(edge.source_id, edge.target_id, type=edge.type.value, weight=edge.weight, **edge.properties)
        self._save_graph()

    async def get_node(self, node_id: str) -> Optional[Node]:
        if self.graph.has_node(node_id):
            data = self.graph.nodes[node_id]
            # reconstruct Node
            return Node(
                id=node_id, 
                type=NodeType(data.get('type', 'Transaction')), # Default fallback
                properties={k:v for k,v in data.items() if k != 'type'}
            )
        return None

    async def get_neighbors(self, node_id: str, edge_type: Optional[EdgeType] = None) -> List[Tuple[Edge, Node]]:
        results = []
        if not self.graph.has_node(node_id):
            return []
            
        for neighbor in self.graph.neighbors(node_id):
            # Get edges data
            edges_data = self.graph.get_edge_data(node_id, neighbor)
            for key, attr in edges_data.items():
                e_type_str = attr.get('type')
                if edge_type and e_type_str != edge_type.value:
                    continue
                
                # Build edge object
                edge = Edge(
                    source_id=node_id,
                    target_id=neighbor,
                    type=EdgeType(e_type_str) if e_type_str else EdgeType.BELONGS_TO,
                    weight=attr.get('weight', 1.0),
                    properties={k:v for k,v in attr.items() if k not in ['type', 'weight']}
                )
                
                # Fetch neighbor Node
                neighbor_data = self.graph.nodes[neighbor]
                neighbor_node = Node(
                    id=neighbor,
                    type=NodeType(neighbor_data.get('type', 'Transaction')),
                    properties={k:v for k,v in neighbor_data.items() if k != 'type'}
                )
                
                results.append((edge, neighbor_node))
        return results

    async def get_all_nodes(self, node_type: Optional[NodeType] = None) -> List[Node]:
        nodes = []
        for n_id, data in self.graph.nodes(data=True):
            # Filter by type if requested
            n_t_str = data.get("type", "Transaction")
            
            if node_type and n_t_str != node_type.value:
                continue
                
            n_type = NodeType(n_t_str) if n_t_str in [t.value for t in NodeType] else NodeType.TRANSACTION
            
            nodes.append(Node(
                id=n_id,
                type=n_type,
                properties={k:v for k,v in data.items() if k != "type"}
            ))
        return nodes

    async def get_all_edges(self, edge_type: Optional[EdgeType] = None) -> List[Edge]:
        edges = []
        for u, v, data in self.graph.edges(data=True):
            e_t_str = data.get("type", "related_to")
            
            if edge_type and e_t_str != edge_type.value:
                 continue

            edges.append(Edge(
                source_id=u,
                target_id=v,
                type=EdgeType(e_t_str) if e_t_str in [t.value for t in EdgeType] else EdgeType.RELATED_TO,
                weight=data.get("weight", 1.0),
                properties={k:v for k,v in data.items() if k not in ["type", "weight"]}
            ))
        return edges

    async def close(self):
        self._save_graph()

class Neo4jProvider(GraphProvider):
    """
    Neo4j Graph Provider Implementation.
    """
    def __init__(self, uri: str, user: str, password: str):
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        
    async def close(self):
        await self.driver.close()

    async def save_graph(self) -> None:
        # Neo4j is persistent, no-op
        pass
        
    async def add_node(self, node: Node) -> None:
        query = (
            f"MERGE (n:{node.type.value} {{id: $id}}) "
            "SET n += $props"
        )
        async with self.driver.session() as session:
            await session.run(query, id=node.id, props=node.properties)

    async def add_edge(self, edge: Edge) -> None:
        # Assumes nodes allow merging by ID independent of label for simplicity,
        # or we assume they exist. To be safe, we MATCH start/end nodes.
        # But we don't know their types here easily without querying.
        # So we trust IDs are unique or we blindly Match (n {id: $src})
        query = (
            "MATCH (a {id: $src}), (b {id: $tgt}) "
            f"MERGE (a)-[r:{edge.type.value}]->(b) "
            "SET r.weight = $weight, r += $props"
        )
        async with self.driver.session() as session:
            await session.run(query, 
                              src=edge.source_id, 
                              tgt=edge.target_id, 
                              weight=edge.weight, 
                              props=edge.properties)

    async def get_node(self, node_id: str) -> Optional[Node]:
        query = "MATCH (n {id: $id}) RETURN n, labels(n) as labels"
        async with self.driver.session() as session:
            result = await session.run(query, id=node_id)
            record = await result.single()
            if record:
                node_data = dict(record['n'])
                labels = record['labels']
                # Determine primary label (heuristic: pick first recognized one)
                primary_type = NodeType.TRANSACTION
                for l in labels:
                    try:
                        primary_type = NodeType(l)
                        break
                    except ValueError:
                        pass
                
                # remove id from props if it duplicates
                if 'id' in node_data:
                    del node_data['id']
                    
                return Node(id=node_id, type=primary_type, properties=node_data)
        return None

    async def get_neighbors(self, node_id: str, edge_type: Optional[EdgeType] = None) -> List[Tuple[Edge, Node]]:
        rel_type_clause = f":{edge_type.value}" if edge_type else ""
        query = (
            f"MATCH (a {{id: $id}})-[r{rel_type_clause}]->(b) "
            "RETURN r, type(r) as r_type, b, labels(b) as b_labels"
        )
        results = []
        async with self.driver.session() as session:
            result = await session.run(query, id=node_id)
            async for record in result:
                # Edge
                rel_props = dict(record['r'])
                rel_type = record['r_type']
                edge = Edge(
                    source_id=node_id, 
                    target_id=dict(record['b']).get('id', 'unknown'),
                    type=EdgeType(rel_type),
                    weight=rel_props.get('weight', 1.0),
                    properties={k:v for k,v in rel_props.items() if k != 'weight'}
                )
                
                # Node
                node_props = dict(record['b'])
                n_id = node_props.get('id', 'unknown')
                if 'id' in node_props: del node_props['id']
                
                labels = record['b_labels']
                n_type = NodeType.TRANSACTION
                for l in labels:
                    try: 
                        n_type = NodeType(l)
                        break
                    except ValueError: pass
                
                node = Node(id=n_id, type=n_type, properties=node_props)
                results.append((edge, node))
        return results

    async def get_all_nodes(self, node_type: Optional[NodeType] = None) -> List[Node]:
        # Limit to prevent OOM on large graphs, or rely on generator
        # For V1, we fetch all (assuming reasonable size < 10k)
        label_filter = f":{node_type.value}" if node_type else ""
        query = f"MATCH (n{label_filter}) RETURN n, labels(n)"
        
        nodes = []
        async with self.driver.session() as session:
            result = await session.run(query)
            async for record in result:
                node_props = dict(record['n'])
                n_id = node_props.get('id', 'unknown')
                labels = record['labels']
                
                # Determine type
                n_type = NodeType.TRANSACTION
                for l in labels:
                    try: 
                        n_type = NodeType(l)
                        break
                    except ValueError: pass
                
                if 'id' in node_props: del node_props['id']
                nodes.append(Node(id=n_id, type=n_type, properties=node_props))
        return nodes

    async def get_all_edges(self, edge_type: Optional[EdgeType] = None) -> List[Edge]:
        type_filter = f":{edge_type.value}" if edge_type else ""
        # Use elementId() for system ID fallback if 'id' property is missing
        query = (
            f"MATCH (a)-[r{type_filter}]->(b) "
            "RETURN a.id as prop_src, elementId(a) as sys_src, "
            "b.id as prop_tgt, elementId(b) as sys_tgt, "
            "r, type(r)"
        )
        
        edges = []
        async with self.driver.session() as session:
            result = await session.run(query)
            async for record in result:
                src_id = record['prop_src'] or record['sys_src']
                tgt_id = record['prop_tgt'] or record['sys_tgt']
                
                if not src_id or not tgt_id: continue
                
                rel_props = dict(record['r'])
                rel_type = record['type(r)']
                
                edges.append(Edge(
                    source_id=src_id,
                    target_id=tgt_id,
                    type=EdgeType(rel_type),
                    weight=rel_props.get('weight', 1.0),
                    properties={k:v for k,v in rel_props.items() if k != 'weight'}
                ))
        return edges

def get_graph_provider() -> GraphProvider:
    """Factory to get the appropriate provider."""
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    
    if neo4j_uri and neo4j_password:
        return Neo4jProvider(neo4j_uri, neo4j_user, neo4j_password)
    
    return NetworkXProvider()
