from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any

class Tenant(BaseModel):
    model_config = ConfigDict(strict=True)
    id: UUID
    name: str
    domain: str
    auth_config: Dict[str, Any] = {}
    settings: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
