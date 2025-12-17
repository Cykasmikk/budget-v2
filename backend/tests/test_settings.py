import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.infrastructure.models import TenantModel
import uuid

from src.interface.dependencies import get_db
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_settings_api(db_session):
    # Override Dependency
    app.dependency_overrides[get_db] = lambda: db_session
    
    # Mock CleanupService so background task doesn't crash on invalid DB
    with patch("src.main.CleanupService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.cleanup_expired_guests.return_value = 0
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # Create guest session first
            response = await ac.post("/api/v1/auth/guest")
            assert response.status_code == 200
            cookies = response.cookies
            
            # 2. Get Default Settings
            response = await ac.get("/api/v1/settings", cookies=cookies)
            assert response.status_code == 200
            settings = response.json()
            assert settings["currency"] == "USD"
            assert settings["forecast_horizon"] == 6

            # 3. Patch Settings
            update_payload = {
                "currency": "EUR",
                "forecast_horizon": 12,
                "budget_threshold": 8000
            }
            response = await ac.patch("/api/v1/settings", json=update_payload, cookies=cookies)
            assert response.status_code == 200
            updated = response.json()
            assert updated["currency"] == "EUR"
            assert updated["forecast_horizon"] == 12
            assert updated["budget_threshold"] == 8000
            
            # 4. Verify Persistence (Get again)
            response = await ac.get("/api/v1/settings", cookies=cookies)
            assert response.status_code == 200
            final = response.json()
            assert final["currency"] == "EUR"
