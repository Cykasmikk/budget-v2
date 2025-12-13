from datetime import datetime
from typing import Optional
from pydantic import BaseModel, UUID4, EmailStr, ConfigDict
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"

class User(BaseModel):
    """
    Represents a user in the system.
    """
    id: UUID4
    tenant_id: UUID4
    email: EmailStr
    role: UserRole
    hashed_password: Optional[str] = None # Null for SSO users
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
