import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from src.application.ai.simulator_ai import SimulatorAI, SimulatorAction
from decimal import Decimal

@pytest.fixture
def mock_genai():
    with patch("src.application.ai.simulator_ai.genai") as mock:
        # Mock the GenerativeModel class and its generate_content_async method
        mock_model = MagicMock()
        mock.GenerativeModel.return_value = mock_model
        
        # Mock response
        mock_response = MagicMock()
        mock_response.text = '{"action": "reduce", "target": "Entertainment", "amount": 15.0, "unit": "percent", "explanation": "Cutting entertainment budget by 15% as requested."}'
        
        # Make generate_content_async return the mock response (async)
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        
        yield mock

@pytest.mark.asyncio
async def test_parse_scenario_valid(mock_genai):
    """Test parsing a valid natural language scenario."""
    simulator = SimulatorAI(api_key="fake-key")
    
    action = await simulator.parse_scenario("Cut entertainment by 15%")
    
    assert isinstance(action, SimulatorAction)
    assert action.action == "reduce"
    assert action.target == "Entertainment"
    assert action.amount == 15.0
    assert action.unit == "percent"

@pytest.mark.asyncio
async def test_parse_scenario_json_error(mock_genai):
    """Test handling of invalid JSON response from LLM."""
    # Setup mock to return bad JSON
    mock_model = mock_genai.GenerativeModel.return_value
    mock_response = MagicMock()
    mock_response.text = "I am sorry I cannot do that."
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)
    
    simulator = SimulatorAI(api_key="fake-key")
    
    # Should probably return None or raise specific error
    # Let's assume it returns None for now or a fallback
    result = await simulator.parse_scenario("Invalid request")
    assert result is None

@pytest.mark.asyncio
async def test_simulated_output_schema():
    """Test that the Pydantic model enforces structure."""
    with pytest.raises(ValueError):
        SimulatorAction(action="unknown_action", target="Foo", amount=10, unit="percent")
