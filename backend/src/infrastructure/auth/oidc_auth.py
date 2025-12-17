from typing import Optional
from jose import jwt, JWTError
from src.domain.auth import AuthProvider
import os

class OIDCAuthProvider(AuthProvider):
    """
    OIDC implementation using JWT validation.
    """
    
    def __init__(self):

        self.secret_key = os.getenv("AUTH_SECRET_KEY")
        if not self.secret_key:
            raise ValueError("AUTH_SECRET_KEY environment variable is not set")
        self.algorithm = os.getenv("AUTH_ALGORITHM", "HS256")
        
    async def verify_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None

    async def get_user(self, token: str) -> Optional[str]:
        payload = await self.verify_token(token)
        if payload:
            return payload.get("sub")
        return None
