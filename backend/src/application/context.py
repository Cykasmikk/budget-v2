from contextvars import ContextVar
from typing import Optional
from uuid import UUID

_tenant_id_ctx: ContextVar[Optional[UUID]] = ContextVar("tenant_id", default=None)
_user_id_ctx: ContextVar[Optional[UUID]] = ContextVar("user_id", default=None)

def get_tenant_id() -> Optional[UUID]:
    return _tenant_id_ctx.get()

def set_tenant_id(tenant_id: UUID):
    _tenant_id_ctx.set(tenant_id)

def get_user_id() -> Optional[UUID]:
    return _user_id_ctx.get()

def set_user_id(user_id: UUID):
    _user_id_ctx.set(user_id)
