import pytest
from unittest.mock import Mock, MagicMock
from src.application.ml_services.pattern_detector import PatternDetector, PatternMatch
from src.infrastructure.knowledge_graph.graph_service import GraphService, EdgeType, NodeType

@pytest.fixture
def mock_embedding_service():
    service = Mock()
    # Mock encode to return a dummy vector
    service.encode.return_value = [0.1, 0.2, 0.3]
    # Mock similarity to return high score for "Netflix" and "Netflix Premium"
    # usage: service.similarity(v1, v2)
    service.similarity.side_effect = lambda v1, v2: 0.9
    return service

@pytest.fixture
def mock_graph_service():
    service = Mock(spec=GraphService)
    service.has_edge.return_value = False
    return service

@pytest.fixture
def pattern_detector(mock_embedding_service, mock_graph_service):
    return PatternDetector(mock_embedding_service, mock_graph_service)

def test_detect_patterns_vector_only(pattern_detector, mock_embedding_service):
    """Test that it detects patterns using vector similarity (fallback)."""
    transactions = [
        MagicMock(description="Netflix", amount=15.00),
        MagicMock(description="Netflix Premium", amount=15.00),
        MagicMock(description="Uber Eats", amount=25.00)
    ]
    
    # Configure mock to return distinct high similarity
    mock_embedding_service.similarity.side_effect = [0.95, 0.96, 0.1] # Netflix=0.95, Premium=0.96
    
    matches = pattern_detector.detect_patterns("Netflix", transactions)
    
    # Should match "Netflix Premium"
    assert len(matches) >= 1
    assert matches[0].transaction.description == "Netflix Premium"
    assert matches[0].score > 0.8
    assert matches[0].source == "vector"

def test_detect_patterns_hybrid_boost(pattern_detector, mock_embedding_service, mock_graph_service):
    """Test that graph connections boost the score."""
    transactions = [
        MagicMock(description="Hulu", amount=15.00),
        MagicMock(description="Spotify", amount=15.00)
    ]
    
    # Vector similarity is moderate for both
    mock_embedding_service.similarity.return_value = 0.7
    
    # Graph has a SIMILAR_TO edge between Query (Netflix) and Hulu
    # We need to simulate the detector asking the graph
    # "Does Netflix have a relationship with Hulu?"
    def has_edge_side_effect(u, v, type):
        if (u == "Netflix" and v == "Hulu" and type == EdgeType.SIMILAR_TO):
            return True
        return False
    mock_graph_service.has_edge.side_effect = has_edge_side_effect
    
    matches = pattern_detector.detect_patterns("Netflix", transactions)
    
    # Hulu should have a higher score than Spotify because of the graph boost
    hulu_match = next(m for m in matches if m.transaction.description == "Hulu")
    spotify_match = next(m for m in matches if m.transaction.description == "Spotify")
    
    assert hulu_match.score > spotify_match.score
    assert hulu_match.source == "hybrid"

def test_clustering_grouping(pattern_detector, mock_embedding_service):
    """Test grouping similar transactions into a cluster."""
    # This might belong to a different method, e.g., analyze_batch
    # But let's check basic grouping logic if we put it in PatternDetector
    pass
