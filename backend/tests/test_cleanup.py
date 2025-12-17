import pytest
from datetime import datetime, timedelta
import uuid
from sqlalchemy import select
from src.infrastructure.models import TenantModel, UserModel, GuestUsageStats, BudgetModel
from src.application.cleanup_service import CleanupService

@pytest.mark.asyncio
async def test_cleanup_logic(db_session):
    # 1. Setup - Create 1 Old Guest, 1 New Guest, 1 Regular Tenant
    
    # Old Guest (Should be deleted)
    old_guest_id = uuid.uuid4()
    old_guest = TenantModel(
        id=old_guest_id,
        name="Guest Organization Old",
        domain="guest-old.example.com",
        created_at=datetime.utcnow() - timedelta(hours=25)
    )
    db_session.add(old_guest)
    
    # Data for old guest (to verify archive stats)
    db_session.add(BudgetModel(
        tenant_id=old_guest_id,
        date=datetime.utcnow(),
        category="Test",
        amount=100.50,
        description="Test Expense"
    ))
    
    # New Guest (Should remain)
    new_guest = TenantModel(
        id=uuid.uuid4(),
        name="Guest Organization New",
        domain="guest-new.example.com",
        created_at=datetime.utcnow() - timedelta(hours=1)
    )
    db_session.add(new_guest)
    
    # Regular Tenant (Should remain even if old)
    regular_tenant = TenantModel(
        id=uuid.uuid4(),
        name="Real Organization",
        domain="real.example.com",
        created_at=datetime.utcnow() - timedelta(hours=48) # Older than 24h, but not 'Guest'
    )
    db_session.add(regular_tenant)
    
    await db_session.commit()
    
    # 2. Run Cleanup
    service = CleanupService(db_session)
    deleted_count = await service.cleanup_expired_guests()
    
    # 3. Assertions
    assert deleted_count == 1
    
    # Old guest should be gone
    assert (await db_session.get(TenantModel, old_guest_id)) is None
    
    # New guest should exist
    assert (await db_session.get(TenantModel, new_guest.id)) is not None
    
    # Regular tenant should exist
    assert (await db_session.get(TenantModel, regular_tenant.id)) is not None
    
    # Stats should be archived for old guest
    result = await db_session.execute(select(GuestUsageStats).where(GuestUsageStats.original_tenant_id == str(old_guest_id)))
    stats = result.scalar_one_or_none()
    
    assert stats is not None
    assert float(stats.total_budget_value) == 100.50
    assert stats.session_duration_seconds > 0
