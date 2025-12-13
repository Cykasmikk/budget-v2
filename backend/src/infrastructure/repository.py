from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.budget import BudgetEntry
from src.domain.rule import Rule
from src.domain.repository import BudgetRepository, RuleRepository
from src.infrastructure.models import BudgetModel, RuleModel
from src.infrastructure.base_repository import BaseRepository

class SQLBudgetRepository(BaseRepository[BudgetModel], BudgetRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, BudgetModel)

    async def save_bulk(self, entries: List[BudgetEntry]) -> None:
        tenant_id = self._get_tenant_id()
        
        # Optimized Bulk Insert using Hash-based deduplication per Tenant
        # 1. Fetch existing hashes for this Tenant
        stmt = select(BudgetModel).where(BudgetModel.tenant_id == tenant_id)
        existing_result = await self.session.execute(stmt)
        existing_models = existing_result.scalars().all()
        
        existing_hashes = {
            f"{m.date}_{float(m.amount)}_{m.description}" for m in existing_models
        }
        
        new_models = []
        for e in entries:
            entry_hash = f"{e.date}_{float(e.amount)}_{e.description}"
            if entry_hash not in existing_hashes:
                new_models.append(BudgetModel(
                    tenant_id=tenant_id,
                    date=e.date,
                    category=e.category,
                    amount=e.amount,
                    description=e.description,
                    project=e.project
                ))
                existing_hashes.add(entry_hash)
        
        if new_models:
            self.session.add_all(new_models)
            await self.session.commit()

    async def get_all(self) -> List[BudgetEntry]:
        # Using BaseRepository's get_all which already filters by tenant
        models = await super().get_all()
        return [
            BudgetEntry(
                date=m.date,
                category=m.category,
                amount=m.amount,
                description=m.description,
                project=m.project or "General"
            )
            for m in models
        ]

class SQLRuleRepository(BaseRepository[RuleModel], RuleRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, RuleModel)

    async def add(self, rule: Rule) -> Rule:
        model = RuleModel(pattern=rule.pattern, category=rule.category)
        # tenant_id handled by BaseRepository.add
        await super().add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return Rule(id=model.id, pattern=model.pattern, category=model.category)

    async def get_all(self) -> List[Rule]:
        models = await super().get_all()
        return [Rule(id=m.id, pattern=m.pattern, category=m.category) for m in models]

    async def delete(self, rule_id: int) -> None:
        await super().delete_by_id(rule_id)
        await self.session.commit()
