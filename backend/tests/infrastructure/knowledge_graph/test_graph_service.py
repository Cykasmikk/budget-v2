import pytest
from src.infrastructure.knowledge_graph.graph_service import GraphService, GraphNode, GraphEdge, NodeType, EdgeType

@pytest.fixture
def graph_service():
    return GraphService()

def test_add_nodes_and_edges(graph_service):
    """Test adding nodes and edges to the graph."""
    graph_service.add_node("Netflix", NodeType.MERCHANT)
    graph_service.add_node("Entertainment", NodeType.CATEGORY)
    graph_service.add_edge("Netflix", "Entertainment", EdgeType.BELONGS_TO)
    
    assert graph_service.has_node("Netflix")
    assert graph_service.has_node("Entertainment")
    assert graph_service.has_edge("Netflix", "Entertainment", EdgeType.BELONGS_TO)

def test_find_related_categories(graph_service):
    """Test finding categories related to a merchant via graph traversal."""
    # Setup: Netflix -> Entertainment, Hulu -> Entertainment
    # Netflix is similar to Hulu
    graph_service.add_node("Netflix", NodeType.MERCHANT)
    graph_service.add_node("Hulu", NodeType.MERCHANT)
    graph_service.add_node("Entertainment", NodeType.CATEGORY)
    
    graph_service.add_edge("Netflix", "Entertainment", EdgeType.BELONGS_TO)
    graph_service.add_edge("Hulu", "Entertainment", EdgeType.BELONGS_TO)
    graph_service.add_edge("Netflix", "Hulu", EdgeType.SIMILAR_TO)
    
    # Direct lookup
    cats = graph_service.get_categories_for_merchant("Netflix")
    assert "Entertainment" in cats
    
    # Indirect lookup (if we implemented a 'related' search, but for now simple structure check)
    neighbors = graph_service.get_neighbors("Netflix", EdgeType.SIMILAR_TO)
    assert "Hulu" in neighbors

def test_inference_traversal(graph_service):
    """Test inferring category if direct link missing but similar merchant has one."""
    # UnknownMerchant --SIMILAR--> KnownMerchant --BELONGS--> Category
    graph_service.add_node("MysteryStream", NodeType.MERCHANT)
    graph_service.add_node("Netflix", NodeType.MERCHANT)
    graph_service.add_node("Entertainment", NodeType.CATEGORY)
    
    graph_service.add_edge("MysteryStream", "Netflix", EdgeType.SIMILAR_TO)
    graph_service.add_edge("Netflix", "Entertainment", EdgeType.BELONGS_TO)
    
    # Should be able to infer category for MysteryStream
    inferred = graph_service.infer_category("MysteryStream")
    assert inferred == "Entertainment"

def test_add_bulk_entities(graph_service):
    """Test standardizing bulk addition from analysis results."""
    # This simulates loading data from existing SQL records
    merchants = {"Uber": "Transport", "Woolworths": "Groceries"}
    graph_service.build_from_dict(merchants)
    
    assert graph_service.has_node("Uber")
    assert graph_service.get_categories_for_merchant("Uber") == ["Transport"]
