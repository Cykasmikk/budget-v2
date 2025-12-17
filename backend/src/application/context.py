from contextvars import ContextVar
from typing import Optional
from uuid import UUID

_tenant_id_ctx: ContextVar[Optional[UUID]] = ContextVar("tenant_id", default=None)
_user_id_ctx: ContextVar[Optional[UUID]] = ContextVar("user_id", default=None)

def get_tenant_id() -> Optional[UUID]:
    """
    Retrieves the current tenant ID from the context variable.

    Returns:
        Optional[UUID]: The tenant ID if set, otherwise None.
    """
    return _tenant_id_ctx.get()

def set_tenant_id(tenant_id: UUID):
    """
    Sets the current tenant ID in the context variable.

    Args:
        tenant_id (UUID): The tenant ID to set.
    """
    _tenant_id_ctx.set(tenant_id)

def get_user_id() -> Optional[UUID]:
    """
    Retrieves the current user ID from the context variable.

    Returns:
        Optional[UUID]: The user ID if set, otherwise None.
    """
    return _user_id_ctx.get()

def set_user_id(user_id: UUID):
    """
    Sets the current user ID in the context variable.

    Args:
        user_id (UUID): The user ID to set.
    """
    _user_id_ctx.set(user_id)
