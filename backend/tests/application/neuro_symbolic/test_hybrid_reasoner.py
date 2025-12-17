import pytest
from unittest.mock import Mock, MagicMock
from src.application.neuro_symbolic.hybrid_reasoner import HybridReasoner, ReasoningResult
from src.application.ai.predictor import Predictor
from src.infrastructure.knowledge_graph.graph_service import GraphService

@pytest.fixture
def mock_predictor():
    p = Mock(spec=Predictor)
    p.predict.return_value = ("Uncategorized", 0.0)
    return p

@pytest.fixture
def mock_graph_service():
    g = Mock(spec=GraphService)
    g.infer_category.return_value = None
    return g

@pytest.fixture
def hybrid_reasoner(mock_predictor, mock_graph_service):
    # We might pass a budget_solver mock too if we strictly use it for verification
    # For now, let's assume reasoner handles the orchestration logic
    return HybridReasoner(mock_predictor, mock_graph_service)

def test_neural_high_confidence_accepted(hybrid_reasoner, mock_predictor):
    """Test that high confidence neural prediction is accepted if no conflicts."""
    mock_predictor.predict.return_value = ("Groceries", 0.95)
    
    # Empty rules -> No conflict
    result = hybrid_reasoner.refine_prediction("Woolworths", [], threshold=0.8)
    
    assert result.category == "Groceries"
    assert result.source == "neural"
    assert result.confidence == 0.95
    assert result.is_verified is False # Not verified by rule/graph, just accepted high confidence

def test_symbolic_override(hybrid_reasoner, mock_predictor):
    """Test that a symbolic rule overrides neural prediction."""
    mock_predictor.predict.return_value = ("Software", 0.9)
    
    # Rule says Netflix -> Entertainment
    rules = [{"pattern": "Netflix", "category": "Entertainment"}]
    
    # Neural predicts Software for "Netflix", but rule says Entertainment
    # Note: Logic should check strict rule match
    result = hybrid_reasoner.refine_prediction("Netflix", rules)
    
    assert result.category == "Entertainment"
    assert result.source == "symbolic_override"
    assert result.confidence == 1.0

def test_graph_fallback_low_confidence(hybrid_reasoner, mock_predictor, mock_graph_service):
    """Test fallback to graph when neural confidence is low."""
    mock_predictor.predict.return_value = ("Unknown", 0.3)
    mock_graph_service.infer_category.return_value = "Transport"
    
    result = hybrid_reasoner.refine_prediction("Uber", [], threshold=0.8)
    
    assert result.category == "Transport"
    assert result.source == "graph_inference"
    assert result.confidence > 0.3 # Should be boosted or set high

def test_iterative_refinement_loop(hybrid_reasoner, mock_predictor):
    """
    Test the iterative loop: Neural -> Check -> Feedback?
    For this MVP, it's Linear: Rule > Neural (> Threshold) > Graph > Neural (Best Effort)
    But the roadmap mentions 'Iterative Refinement'.
    Let's stick to the robust fallback chain for now as valid 'Hybrid Reasoning'.
    """
    pass
