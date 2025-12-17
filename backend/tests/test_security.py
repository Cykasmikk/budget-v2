import pytest
import os
from unittest.mock import MagicMock, patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.main import app
from src.infrastructure.models import TenantModel, UserModel
from src.application.auth_service import AuthService
from src.interface.dependencies import get_db

# Mock the CleanupService to prevent background task from hitting DB
@pytest.fixture(autouse=True)
def mock_cleanup():
    with patch("src.main.CleanupService") as mock:
        mock_instance = MagicMock()
        mock_instance.cleanup_expired_guests.return_value = 0
        mock.return_value = mock_instance
        yield mock

# Mock the AsyncSessionLocal in main.py to prevent Real DB connection in background loop
@pytest.fixture(autouse=True)
def mock_db_in_main():
    with patch("src.main.AsyncSessionLocal") as mock:
        # We don't need it to do anything real, just accept context manager
        mock.return_value.__aenter__.return_value = MagicMock()
        yield mock

@pytest.mark.asyncio
async def test_rate_limiting(db_session: AsyncSession):
    """
    Verify that the guest login endpoint is rate-limited.
    limit is 5/hour. We will hit it 6 times.
    """
    # Override dependency to use SQLite fixture
    app.dependency_overrides[get_db] = lambda: db_session
    
    transport = ASGITransport(app=app)
    # Use distinct client IP simulation if needed, but slowapi uses remote_address.
    # In tests, Starlette TestClient/httpx usually defaults to 127.0.0.1 or testclient.
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1-5 passes
        for i in range(5):
            response = await client.post("/api/v1/auth/guest")
            if response.status_code != 200:
                print(f"Request {i+1} failed: {response.status_code} {response.text}")
            assert response.status_code == 200, f"Request {i+1} failed: {response.text}"

        # 6th fail
        response = await client.post("/api/v1/auth/guest")
        assert response.status_code == 429, "Rate limit failed to trigger"
    
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_secure_cookies_flag(db_session: AsyncSession):
    """
    Verify that SECURE_COOKIES env var controls the secure flag.
    We need to patch os.getenv or set it before importing? 
    It is read at request time in the new code, so patching os.environ works.
    """
    app.dependency_overrides[get_db] = lambda: db_session
    transport = ASGITransport(app=app)
    
    # Enable Secure Cookies
    os.environ["SECURE_COOKIES"] = "True"
    
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Use simple endpoint logic or login (login is rate limited now? No, only guest)
        # Auth Service requires DB.
        
        # Create Admin
        service = AuthService(db_session)
        # Ensure default setup creates admin
        await service.ensure_default_setup()
        
        login_payload = {"email": "admin@example.com", "password": "admin"}
        response = await client.post("/api/v1/auth/login", json=login_payload)
        
        if response.status_code != 200:
             print(f"Login failed: {response.text}")
        assert response.status_code == 200
        
        # Check Cookies
        cookie = None
        for c in response.cookies.jar:
            if c.name == "session_id":
                cookie = c
                break
        
        assert cookie is not None
        assert cookie.secure == True # Should be True

    # Cleanup
    del os.environ["SECURE_COOKIES"]
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_tenant_isolation(db_session: AsyncSession):
    """
    Verify that User A cannot access User B's settings.
    We will simulate this by creating two sessions and trying to cross-access?
    The Settings API uses `user.tenant_id`.
    So if I am logged in as A, the API code:
      `select(TenantModel).where(TenantModel.id == user.tenant_id)`
    
    Hard to 'exploit' via API unless I can forge the session or if API took tenant_id as param.
    The API does NOT take tenant_id as param. It derives from session.
    
    Verification goal: Confirm that the Session object strictly maps to ONE user/tenant.
    
    Instead, let's test specific vulnerability: Can I use Guest Session ID to access Admin Data?
    """
    app.dependency_overrides[get_db] = lambda: db_session
    
    service = AuthService(db_session)
    
    # 1. Create Admin (Must be first so ensure_default_setup sees empty DB or checks correctly)
    await service.ensure_default_setup()
    admin_user = await service.authenticate_user("admin@example.com", "admin")
    admin_session = await service.create_session(admin_user)
    
    # 2. Create Guest
    guest_session = await service.create_guest_access()
    
    # Verify Tenant IDs
    print(f"Admin Tenant: {admin_user.tenant_id}")
    # We need guest user to check tenant id
    guest_user = await service.get_user_by_session(guest_session.id)
    print(f"Guest Tenant: {guest_user.tenant_id}")
    
    assert admin_user.tenant_id != guest_user.tenant_id, "Tenants are identical!"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # A. Guest Accesses Own Settings -> 200
        client.cookies = {"session_id": guest_session.id}
        response = await client.get("/api/v1/settings")
        assert response.status_code == 200
        guest_settings = response.json()
        print(f"Guest Initial: {response.json()}")
        
        # B. Admin Accesses Own Settings -> 200
        client.cookies = {"session_id": admin_session.id}
        response = await client.get("/api/v1/settings")
        assert response.status_code == 200
        admin_settings = response.json()
        
        # C. Verify Tenant Isolation (Guest changes should not affect Admin)
        # Switch back to Guest to perform update
        client.cookies = {"session_id": guest_session.id}
        response = await client.patch("/api/v1/settings", json={"theme": "purple"})
        assert response.status_code == 200

        # Switch to Admin
        client.cookies = {"session_id": admin_session.id}
        response = await client.get("/api/v1/settings")
        # Admin should see default "dark" or whatever is in DB, NOT "purple"
        assert response.json().get("theme") != "purple"
    
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_cors_headers():
    """
    Verify CORS headers are set.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
        
        # Invalid Origin
        response = await client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "http://evil.com",
                "Access-Control-Request-Method": "POST"
            }
        )
        # Default CORSMiddleware regex/list behavior: 
        # If not allowed, it normally doesn't return the header, or 400?
        # Starlette CORS middleware usually returns 200 but WITHOUT the AC-Allow-Origin header if the origin is not allowed.
        assert "access-control-allow-origin" not in response.headers
