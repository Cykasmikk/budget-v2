from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, UUID4, ConfigDict

class Tenant(BaseModel):
    """
    Represents a tenant (organization/account) in the system.
    All data is scoped to a tenant.
    """
    id: UUID4
    name: str
    domain: str
    auth_config: dict[str, Any] = {}
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
