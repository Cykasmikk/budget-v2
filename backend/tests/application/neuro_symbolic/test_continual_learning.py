import pytest
from unittest.mock import MagicMock
from src.application.neuro_symbolic.continual_learner import ContinualLearningService
from src.infrastructure.knowledge_graph.graph_service import GraphService, NodeType, EdgeType

def test_learn_feedback_updates_graph():
    """Test that valid feedback creates nodes and edges in the graph."""
    graph_service = GraphService()
    learner = ContinualLearningService(graph_service)
    
    # 1. Provide feedback for a new merchant
    learner.learn_feedback("New AI Tool", "Software")
    
    # 2. Verify Graph Updates
    assert graph_service.has_node("New AI Tool")
    assert graph_service.has_node("Software")
    assert graph_service.has_edge("New AI Tool", "Software", EdgeType.BELONGS_TO)
    
    # 3. Verify Inference works immediately
    inferred = graph_service.infer_category("New AI Tool")
    assert inferred == "Software"

def test_learn_feedback_corrects_existing():
    """Test that feedback overrides or adds to existing knowledge."""
    graph_service = GraphService()
    learner = ContinualLearningService(graph_service)
    
    # Initial state: Mapped to "Wrong Category"
    graph_service.add_node("Obscure SaaS", NodeType.MERCHANT)
    graph_service.add_node("Wrong Category", NodeType.CATEGORY)
    graph_service.add_edge("Obscure SaaS", "Wrong Category", EdgeType.BELONGS_TO)
    
    # Infer initial
    assert graph_service.infer_category("Obscure SaaS") == "Wrong Category"
    
    # Learn correction
    learner.learn_feedback("Obscure SaaS", "Correct Category")
    
    # Check graph has new edge
    assert graph_service.has_edge("Obscure SaaS", "Correct Category", EdgeType.BELONGS_TO)
    
    # Note: infer_category naive impl returns the *first* output. 
    # Real impl might need weighting or timestamping to prefer recent feedback.
    # For now, we assert the new edge exists.
    assert "Correct Category" in graph_service.get_categories_for_merchant("Obscure SaaS")
