from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, UUID4, ConfigDict

class AuditLog(BaseModel):
    """
    Immutable record of system actions.
    """
    id: UUID4
    tenant_id: UUID4
    actor_id: Optional[UUID4] = None # System actions might be null
    action: str
    resource: str
    resource_id: Optional[str] = None
    details: dict[str, Any] = {}
    timestamp: datetime
    ip_address: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
