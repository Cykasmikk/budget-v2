from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class Session(BaseModel):
    model_config = ConfigDict(strict=True)
    id: str
    user_id: UUID
    tenant_id: UUID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
