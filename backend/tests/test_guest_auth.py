
import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_guest_login_flow():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 1. Login as Guest
        response = await ac.post("/api/v1/auth/guest")
        assert response.status_code == 200
        assert "session_id" in response.cookies
        session_id = response.cookies["session_id"]
        
        # 2. Verify Session (Auth Me)
        # The cookie should be automatically handled by the client if we reuse it, 
        # but let's be explicit or reuse the client state.
        
        response_me = await ac.get("/api/v1/auth/me")
        assert response_me.status_code == 200
        data = response_me.json()
        assert "guest-" in data["user"]
        assert data["role"] == "admin"

@pytest.mark.asyncio
async def test_guest_login_data_seeding():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 1. Login
        response = await ac.post("/api/v1/auth/guest")
        assert response.status_code == 200, f"Login failed: {response.text}"
        assert "session_id" in response.cookies, "No session cookie returned"
        print(f"Cookie: {response.cookies['session_id']}")
        
        # 2. Check Analysis/Data
        response = await ac.get("/api/v1/analysis")
        assert response.status_code == 200, f"Analysis failed: {response.status_code} {response.text}"
        data = response.json()
        # Should have data seeded
        assert len(data) > 0, "No analysis data returned"
