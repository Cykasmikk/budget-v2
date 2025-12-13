from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, Optional

class AuditLog(BaseModel):
    model_config = ConfigDict(strict=True)
    id: UUID
    tenant_id: UUID
    user_id: Optional[UUID]
    action: str
    resource_type: str
    resource_id: Optional[str]
    details: Dict[str, Any] = {}
    ip_address: Optional[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)
