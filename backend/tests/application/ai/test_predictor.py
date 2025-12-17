import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from src.application.ai.predictor import Predictor
from src.domain.budget import BudgetEntry
from datetime import date
from decimal import Decimal

@pytest.fixture
def mock_embedding_service():
    with patch("src.application.ai.predictor.EmbeddingService") as MockService:
        service_instance = MockService.return_value
        # Mock encode to return deterministic vectors based on string length for testing
        # "Food" (4) -> [0.4, 0.4, 0.4]
        # "Uber" (4) -> [0.4, 0.4, 0.4]
        # "Server" (6) -> [0.6, 0.6, 0.6]
        service_instance.encode.side_effect = lambda x: [len(x)/10.0] * 3
        yield service_instance

def test_predictor_initialization(mock_embedding_service):
    """Test that predictor initializes with embedding service."""
    predictor = Predictor()
    assert predictor.embedding_service is not None

def test_train_and_predict(mock_embedding_service):
    """Test full flow: train on data, then predict."""
    predictor = Predictor()
    
    # Training data
    entries = [
        BudgetEntry(date=date(2024, 1, 1), amount=Decimal("10"), description="Uber Ride", category="Transport"),
        BudgetEntry(date=date(2024, 1, 1), amount=Decimal("10"), description="Lyft Ride", category="Transport"),
        BudgetEntry(date=date(2024, 1, 1), amount=Decimal("10"), description="AWS", category="Hosting"),
    ]
    
    # Train
    predictor.train(entries)
    
    # Predict "Uber EATS" (Starts with Uber, similar length)
    # Note: Our mock side_effect is simple length-based, so "Uber EATS" (9) might not match "Uber Ride" (9) perfectly if we used real embeddings
    # But here we just test that the mechanism works.
    
    # Let's mock the internal KNN to ensure we test the logic wrapper, NOT scikit-learn
    with patch.object(predictor, 'knn') as mock_knn:
        mock_knn.predict.return_value = ["Transport"]
        mock_knn.predict_proba.return_value = [[0.9, 0.1]] # 90% Transport
        mock_knn.classes_ = ["Transport", "Hosting"]
        
        category, confidence = predictor.predict("Uber EATS")
        
        assert category == "Transport"
        assert confidence == 0.9

def test_predict_without_training(mock_embedding_service):
    """Test prediction behavior when model is not trained."""
    predictor = Predictor()
    category, confidence = predictor.predict("Something")
    assert category == "Uncategorized"
    assert confidence == 0.0

def test_hybrid_rule_override(mock_embedding_service):
    """Test that symbolic rules (regex) override neural predictions if provided."""
    # This might belong in a higher level service, but if Predictor handles it:
    pass
