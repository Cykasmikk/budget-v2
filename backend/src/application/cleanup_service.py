from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from src.infrastructure.models import (
    TenantModel, UserModel, SessionModel, 
    BudgetModel, AuditLogModel, GuestUsageStats,
    RuleModel
)
import structlog
import uuid

logger = structlog.get_logger()

class CleanupService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def cleanup_expired_guests(self):
        """
        Finds guest tenants created > 24 hours ago.
        Archives their usage stats.
        Hard deletes all related data (Cascading delete manually if needed, or relying on FKs).
        Returns count of deleted tenants.
        """
        # 1. Find Expired Guest Tenants
        # We identify guests by name convention "Guest Organization..." or explicit metadata if we had it.
        # For now, relying on name convention + domain convention from auth_service.
        
        cutoff = datetime.utcnow() - timedelta(hours=24)
        
        stmt = select(TenantModel).where(
            TenantModel.name.like("Guest Organization%"),
            TenantModel.created_at < cutoff
        )
        result = await self.session.execute(stmt)
        expired_tenants = result.scalars().all()
        
        if not expired_tenants:
            return 0
            
        logger.info("cleanup_started", count=len(expired_tenants))
        
        for tenant in expired_tenants:
            await self._archive_and_delete(tenant)
            
        await self.session.commit()
        return len(expired_tenants)

    async def _archive_and_delete(self, tenant: TenantModel):
        try:
            # 1. Gather Stats
            # Count transactions
            txn_count_stmt = select(func.count()).where(BudgetModel.tenant_id == tenant.id)
            txn_count = (await self.session.execute(txn_count_stmt)).scalar() or 0
            
            # Sum budget
            budget_sum_stmt = select(func.sum(BudgetModel.amount)).where(BudgetModel.tenant_id == tenant.id)
            budget_sum = (await self.session.execute(budget_sum_stmt)).scalar() or 0
            
            # Duration (Now - CreatedAt)
            duration = (datetime.utcnow() - tenant.created_at).total_seconds()
            
            # Create Archive Record
            stats = GuestUsageStats(
                original_tenant_id=str(tenant.id),
                original_created_at=tenant.created_at,
                session_duration_seconds=int(duration),
                total_transactions_logged=txn_count,
                total_budget_value=budget_sum,
                feature_usage_summary={} # Placeholder for future detailed tracking
            )
            self.session.add(stats)
            
            # 2. Delete Data
            # Note: SQLAlchemy cascade 'delete' on relationships is preferred, 
            # but if not configured in models, we delete manually to be safe and clean.
            
            # Delete Sessions
            await self.session.execute(delete(SessionModel).where(SessionModel.tenant_id == tenant.id))
            
            # Delete Transactions
            await self.session.execute(delete(BudgetModel).where(BudgetModel.tenant_id == tenant.id))
            
            # Delete Rules
            await self.session.execute(delete(RuleModel).where(RuleModel.tenant_id == tenant.id))
            
            # Delete Audit Logs
            await self.session.execute(delete(AuditLogModel).where(AuditLogModel.tenant_id == tenant.id))
            
            # Delete Users
            await self.session.execute(delete(UserModel).where(UserModel.tenant_id == tenant.id))
            
            # Delete Tenant
            await self.session.delete(tenant)
            
        except Exception as e:
            logger.error("tenant_cleanup_failed", tenant_id=str(tenant.id), error=str(e))
            # We don't raise here to allow other tenants to be cleaned up
