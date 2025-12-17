import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from src.application.ai.simulator_ai import SimulatorAction
from src.main import app
from src.interface.dependencies import get_current_user
from src.domain.user import User, UserRole
from datetime import datetime
import uuid

@pytest.fixture
def mock_auth_user():
    tenant_id = uuid.uuid4()
    async def mock_get_current_user():
        return User(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            email="test@example.com",
            role=UserRole.ADMIN,
            created_at=datetime.now()
        )
    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield
    app.dependency_overrides.pop(get_current_user, None)

@pytest.mark.asyncio
async def test_parse_simulation_endpoint(client, mock_auth_user, monkeypatch):
    """Test that the endpoint correctly parses a scenario."""
    monkeypatch.setenv("GEMINI_API_KEY", "test_key")
    
    # Mock SimulatorAI to avoid live calls
    mock_action = SimulatorAction(
        action="reduce",
        target="Dining",
        amount=50.0,
        unit="percent",
        explanation="Test explanation"
    )
    
    with patch("src.interface.ai_chat_router.SimulatorAI") as MockSimulatorAI:
        instance = MockSimulatorAI.return_value
        instance.parse_scenario = AsyncMock(return_value=mock_action)
        
        response = await client.post(
            "/api/v1/ai/simulator/parse",
            json={"scenario": "Cut dining by 50%"}
        )
        
        assert response.status_code == 200
        data = response.json()
        payload = data["data"]
        assert payload["action"] == "reduce"
        assert payload["target"] == "Dining"
        assert payload["amount"] == 50.0

@pytest.mark.asyncio
async def test_parse_simulation_failure(client, mock_auth_user, monkeypatch):
    """Test handling of parsing failures."""
    monkeypatch.setenv("GEMINI_API_KEY", "test_key")
    
    with patch("src.interface.ai_chat_router.SimulatorAI") as MockSimulatorAI:
        instance = MockSimulatorAI.return_value
        instance.parse_scenario = AsyncMock(return_value=None)
        
        response = await client.post(
            "/api/v1/ai/simulator/parse",
            json={"scenario": "Garbage input"}
        )
        
        assert response.status_code == 422
