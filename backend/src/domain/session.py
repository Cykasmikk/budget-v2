from datetime import datetime
from typing import Optional
from pydantic import BaseModel, UUID4, ConfigDict

class Session(BaseModel):
    """
    Represents a secure user session.
    """
    id: str  # High entropy token
    user_id: UUID4
    tenant_id: UUID4
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
