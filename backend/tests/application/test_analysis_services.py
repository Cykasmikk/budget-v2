import pytest
from unittest.mock import MagicMock
from src.application.analysis_services import CategoryClassifier
from src.application.ai.predictor import Predictor

def test_infer_legacy_keyword_match():
    """Test that existing keyword matching still works."""
    # "aws" -> Hosting/Cloud
    # "aws" -> Hosting/Cloud
    cat, _ = CategoryClassifier.infer("AWS Invoice")
    assert cat == "Hosting/Cloud"

def test_infer_preserves_existing():
    """Test that it doesn't override existing valid categories."""
    """Test that it doesn't override existing valid categories."""
    cat, _ = CategoryClassifier.infer("Unknown logic", current_category="Groceries")
    assert cat == "Groceries"

def test_infer_uses_predictor_fallback():
    """Test that it uses Predictor when legacy fails."""
    mock_predictor = MagicMock(spec=Predictor)
    mock_predictor.predict.return_value = ("Transport", 0.95)
    
    # "Taxi" might not be in legacy keywords (actually waiting to see), 
    # but let's assume "Mysterious Ride" is not.
    cat, conf = CategoryClassifier.infer("Mysterious Ride", predictor=mock_predictor)
    
    # Should call predictor
    mock_predictor.predict.assert_called_once_with("Mysterious Ride")
    assert cat == "Transport"
    assert conf == 0.95

def test_infer_ignores_low_confidence_predictor():
    """Test that it ignores low confidence predictions."""
    mock_predictor = MagicMock(spec=Predictor)
    # Confidence 0.4 < threshold (assuming 0.5 or similar)
    mock_predictor.predict.return_value = ("Transport", 0.4)
    
    cat, conf = CategoryClassifier.infer("Mysterious Ride", predictor=mock_predictor)
    
    assert cat == "Uncategorized"
    assert conf == 0.0

def test_infer_uses_reasoner():
    """Test that it uses Reasoner if provided."""
    mock_reasoner = MagicMock()
    # Mock result object with .category and .confidence attributes
    mock_result = MagicMock()
    mock_result.category = "Groceries"
    mock_result.confidence = 0.9
    mock_reasoner.refine_prediction.return_value = mock_result
    
    cat, conf = CategoryClassifier.infer("Woolworths", reasoner=mock_reasoner)
    
    assert cat == "Groceries"
    assert conf == 0.9
