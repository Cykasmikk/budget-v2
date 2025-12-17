from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.budget import BudgetEntry
from src.domain.rule import Rule
from src.domain.repository import BudgetRepository, RuleRepository
from src.infrastructure.models import BudgetModel, RuleModel
from src.infrastructure.base_repository import BaseRepository

class SQLBudgetRepository(BaseRepository[BudgetModel], BudgetRepository):
    """
    SQLAlchemy implementation of the BudgetRepository.
    Handles persistence of budget entries using BaseRepository for common operations.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(session, BudgetModel)

    async def save_bulk(self, entries: List[BudgetEntry]) -> None:
        """
        Bulk inserts budget entries with tenant-scoped de-duplication.
        
        Args:
            entries (List[BudgetEntry]): The list of entries to save.
        """
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
        """
        Retrieves all budget entries for the current tenant.

        Returns:
            List[BudgetEntry]: List of budget domain entities.
        """
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

    async def get_distinct_entities(self) -> List[str]:
        """
        Retrieves distinct categories, projects, and NORMALIZED merchant names for entity resolution.
        """
        from src.domain.services.merchant_normalization import MerchantNormalizationService
        
        tenant_id = self._get_tenant_id()
        entities = set()
        
        # 1. Categories
        stmt_cat = select(BudgetModel.category).where(BudgetModel.tenant_id == tenant_id).distinct()
        res_cat = await self.session.execute(stmt_cat)
        entities.update(filter(None, res_cat.scalars().all()))
        
        # 2. Projects
        stmt_proj = select(BudgetModel.project).where(BudgetModel.tenant_id == tenant_id).distinct()
        res_proj = await self.session.execute(stmt_proj)
        entities.update(filter(None, res_proj.scalars().all()))
        
        # 3. Merchants (Normalized)
        # Fetch distinct raw descriptions first
        stmt_desc = select(BudgetModel.description).where(BudgetModel.tenant_id == tenant_id).distinct()
        res_desc = await self.session.execute(stmt_desc)
        raw_descs = filter(None, res_desc.scalars().all())
        
        # Normalize them to match what the Analysis/Simualtor sees
        normalized_merchants = {MerchantNormalizationService.normalize(d) for d in raw_descs}
        entities.update(normalized_merchants)
        
        return list(entities)

class SQLRuleRepository(BaseRepository[RuleModel], RuleRepository):
    """
    SQLAlchemy implementation of the RuleRepository.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(session, RuleModel)

    async def add(self, rule: Rule) -> Rule:
        """
        Adds a new categorization rule.

        Args:
            rule (Rule): The rule to add.

        Returns:
            Rule: The added rule with ID populated.
        """
        model = RuleModel(pattern=rule.pattern, category=rule.category)
        # tenant_id handled by BaseRepository.add
        await super().add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return Rule(id=model.id, pattern=model.pattern, category=model.category)

    async def get_all(self) -> List[Rule]:
        """
        Retrieves all rules for the current tenant.

        Returns:
            List[Rule]: List of rule entities.
        """
        models = await super().get_all()
        return [Rule(id=m.id, pattern=m.pattern, category=m.category) for m in models]

    async def delete(self, rule_id: int) -> None:
        """
        Deletes a rule by ID.

        Args:
            rule_id (int): The ID of the rule to delete.
        """
        await super().delete_by_id(rule_id)
        await self.session.commit()
