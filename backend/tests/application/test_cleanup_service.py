import pytest
from src.application.cleanup_service import CleanupService
from src.infrastructure.models import TenantModel, UserModel, SessionModel
from src.domain.user import UserRole
from datetime import datetime, timedelta
from uuid import uuid4

@pytest.mark.asyncio
async def test_cleanup_expired_guests(db_session):
    # Setup
    service = CleanupService(db_session)
    
    # 1. Create an active guest (should NOT be deleted)
    active_tenant_id = uuid4()
    active_tenant = TenantModel(
        id=active_tenant_id,
        name="Active Guest",
        domain="guest-active.local",
        created_at=datetime.utcnow()
    )
    db_session.add(active_tenant)
    
    active_user = UserModel(
        id=uuid4(),
        tenant_id=active_tenant_id,
        email="active@guest.local",
        role=UserRole.VIEWER
    )
    db_session.add(active_user)
    
    # 2. Create an expired guest (should be deleted)
    expired_tenant_id = uuid4()
    expired_tenant = TenantModel(
        id=expired_tenant_id,
        name="Guest Organization Expired",
        domain="guest-expired.local",
        created_at=datetime.utcnow() - timedelta(hours=25) # > 24 hours
    )
    db_session.add(expired_tenant)
    
    expired_user = UserModel(
        id=uuid4(),
        tenant_id=expired_tenant_id,
        email="expired@guest.local",
        role=UserRole.VIEWER
    )
    db_session.add(expired_user)
    
    # 3. Create a non-guest tenant (should NOT be deleted even if old)
    permanent_tenant = TenantModel(
        id=uuid4(),
        name="Permanent Org",
        domain="perm.local",
        created_at=datetime.utcnow() - timedelta(days=365)
    )
    db_session.add(permanent_tenant)
    
    await db_session.commit()
    
    # Execute
    deleted_count = await service.cleanup_expired_guests()
    
    # Assert
    assert deleted_count == 1
    
    # Verify deletions
    active = await db_session.get(TenantModel, active_tenant_id)
    assert active is not None
    
    expired = await db_session.get(TenantModel, expired_tenant_id)
    assert expired is None
    
    permanent = await db_session.get(TenantModel, permanent_tenant.id)
    assert permanent is not None
