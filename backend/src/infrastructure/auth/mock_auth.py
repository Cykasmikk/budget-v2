from typing import Optional
from src.domain.auth import AuthProvider

class MockAuthProvider(AuthProvider):
    """
    Mock implementation for local development.
    Accepts any token and returns a dummy user.
    """
    
    async def verify_token(self, token: str) -> Optional[dict]:
        return {"sub": "test-user", "name": "Test User", "role": "admin"}

    async def get_user(self, token: str) -> Optional[str]:
        return "test-user"
