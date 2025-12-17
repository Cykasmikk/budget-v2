import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.infrastructure.models import TenantModel
from src.interface.dependencies import get_db
from sqlalchemy import select
from src.interface.auth_router import SSOCallbackRequest

@pytest.fixture
def mock_sso_service():
    with patch("src.application.sso_service.SSOService") as mock:
        instance = MagicMock()
        # Setup async mocks
        instance.generate_login_url = AsyncMock(side_effect=lambda t, c, state: f"https://idp.com/auth?state={state}")
        instance.exchange_code = AsyncMock(return_value={"id_token": "fake-token"})
        instance.verify_id_token = AsyncMock(return_value={"email": "test@example.com"})
        
        mock.return_value = instance
        yield instance

@pytest.mark.asyncio
async def test_sso_init_sets_state_cookie(client, db_session, mock_sso_service):
    # Setup Default Org
    tenant = TenantModel(name="Default Organization", domain="example.com", auth_config={"enabled": True})
    db_session.add(tenant)
    await db_session.commit()
    
    response = await client.post("/api/v1/auth/sso/init", json={"callback_url": "http://localhost:3000"})
    
    assert response.status_code == 200
    assert "sso_state" in response.cookies
    state = response.cookies["sso_state"]
    assert len(state) > 0
    
    # Check that redirect URL contains the state
    data = response.json()["data"]
    assert state in data["redirect_url"]

@pytest.mark.asyncio
async def test_sso_callback_success(client, db_session, mock_sso_service):
    # Setup Default Org
    tenant = TenantModel(name="Default Organization", domain="example.com", auth_config={"enabled": True})
    db_session.add(tenant)
    await db_session.commit()
    
    state = "valid-state-123"
    
    # Set cookie manually
    client.cookies = {"sso_state": state}
    
    payload = {
        "code": "auth-code",
        "callback_url": "http://localhost:3000",
        "state": state
    }
    
    response = await client.post("/api/v1/auth/sso/callback", json=payload)
    
    assert response.status_code == 200
    assert response.json()["data"]["user"] == "test@example.com"
    
    # Cookie should be cleared
    # Note: AsyncClient cookie handling of deletion can be tricky to assert directly via jar
    # but the response headers should contain Set-Cookie with max-age=0
    assert 'sso_state=""' in response.headers.get("set-cookie", "") or "Max-Age=0" in response.headers.get("set-cookie", "")

@pytest.mark.asyncio
async def test_sso_callback_csrf_fail_mismatch(client, db_session):
    # No need to setup DB as it fails before DB lookup
    
    client.cookies = {"sso_state": "valid-state"}
    
    payload = {
        "code": "auth-code",
        "callback_url": "http://localhost:3000",
        "state": "attacker-state" # Mismatch
    }
    
    response = await client.post("/api/v1/auth/sso/callback", json=payload)
    
    assert response.status_code == 400
    assert "Invalid state" in response.json()["detail"]

@pytest.mark.asyncio
async def test_sso_callback_csrf_fail_missing_cookie(client, db_session):
    # No cookie set
    
    payload = {
        "code": "auth-code",
        "callback_url": "http://localhost:3000",
        "state": "some-state"
    }
    
    response = await client.post("/api/v1/auth/sso/callback", json=payload)
    
    assert response.status_code == 400
    assert "Invalid state" in response.json()["detail"]
