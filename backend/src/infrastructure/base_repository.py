from typing import TypeVar, Generic, Type, List, Optional
from uuid import UUID
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.context import get_tenant_id

T = TypeVar("T")

class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model

    def _get_tenant_id(self) -> UUID:
        tenant_id = get_tenant_id()
        if not tenant_id:
            # Fallback or Error? In stricter systems, raise Error.
            # For now, we assume middleware sets it.
            raise ValueError("Tenant ID is missing from context")
        return tenant_id

    async def get_all(self) -> List[T]:
        tenant_id = self._get_tenant_id()
        # Enforce Tenant Isolation
        stmt = select(self.model).where(self.model.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def add(self, entity: T):
        tenant_id = self._get_tenant_id()
        # Ensure entity has tenant_id set
        if not getattr(entity, "tenant_id", None):
             setattr(entity, "tenant_id", tenant_id)
        self.session.add(entity)
        await self.session.flush()

    async def delete_by_id(self, entity_id: int):
        tenant_id = self._get_tenant_id()
        stmt = delete(self.model).where(
            self.model.id == entity_id,
            self.model.tenant_id == tenant_id
        )
        await self.session.execute(stmt)
