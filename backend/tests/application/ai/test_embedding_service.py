import pytest
from unittest.mock import MagicMock, patch
from src.application.ai.embedding_service import EmbeddingService

@pytest.fixture
def mock_transformers():
    with patch("src.application.ai.embedding_service.SentenceTransformer") as MockClass:
        mock_instance = MockClass.return_value
        import numpy as np
        # Mock encode to return a dummy vector as numpy array
        mock_instance.encode.return_value = np.array([0.1, 0.2, 0.3])
        yield MockClass

def test_embedding_service_initialization(mock_transformers):
    """Test that the service initializes the model correctly."""
    service = EmbeddingService()
    mock_transformers.assert_called_once_with('all-MiniLM-L6-v2')
    assert service.model is not None

def test_encode_returns_vector(mock_transformers):
    """Test that encode returns a list of floats."""
    service = EmbeddingService()
    vector = service.encode("test text")
    assert isinstance(vector, list)
    assert len(vector) == 3
    assert vector == [0.1, 0.2, 0.3]
    mock_transformers.return_value.encode.assert_called_once_with("test text")

def test_similarity_calculation():
    """Test cosine similarity calculation."""
    service = EmbeddingService()
    # Mocking internal helper if needed or just testing the static method logic
    # Assuming similarity is pure math, we can test it directly if implemented manually
    # or via scikit-learn. Let's assume we use scikit-learn's cosine_similarity or spatial.distance
    
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    v3 = [0.0, 1.0, 0.0]
    
    # Identical vectors = 1.0
    assert service.similarity(v1, v2) == pytest.approx(1.0)
    
    # Orthogonal vectors = 0.0
    assert service.similarity(v1, v3) == pytest.approx(0.0)

def test_caching_behavior(mock_transformers):
    """Test that repeated calls use the cache."""
    service = EmbeddingService()
    
    # First call
    service.encode("repeat")
    
    # Second call
    service.encode("repeat")
    
    # Should only call the model once
    mock_transformers.return_value.encode.assert_called_once()
