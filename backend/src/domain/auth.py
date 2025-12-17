from abc import ABC, abstractmethod
from typing import Optional

class AuthProvider(ABC):
    """
    Abstract interface for authentication provider.
    Enforces the security gate requirement for abstracted auth.
    """
    
    @abstractmethod
    async def verify_token(self, token: str) -> Optional[dict]:
        """
        Verifies the given token and returns the user payload if valid.
        """
        pass

    @abstractmethod
    async def get_user(self, token: str) -> Optional[str]:
        """
        Returns the user ID from the token.
        """
        pass
