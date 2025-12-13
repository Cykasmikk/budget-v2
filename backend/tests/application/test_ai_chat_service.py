import pytest
from unittest.mock import MagicMock, AsyncMock
from src.application.ai_chat_service import AIChatService
from src.domain.user import User, UserRole
from src.infrastructure.models import BudgetModel
from decimal import Decimal
from datetime import date, datetime
from uuid import uuid4

@pytest.mark.asyncio
async def test_ai_chat_service_generate_response(db_session):
    # Setup
    tenant_id = uuid4()
    user = User(
        id=uuid4(),
        tenant_id=tenant_id,
        email="test@example.com",
        role=UserRole.VIEWER,
        created_at=datetime.utcnow()
    )
    
    # Seed data
    entry = BudgetModel(
        tenant_id=tenant_id,
        date=date(2025, 1, 1),
        category="Food",
        amount=Decimal("100.00"),
        description="Groceries",
        project="Personal"
    )
    db_session.add(entry)
    await db_session.commit()
    
    service = AIChatService(db_session, user)
    
    # Test
    response = await service.generate_response("How much did I spend on Food?", [])
    
    # Assert
    assert "100.00" in response
    assert "Food" in response

@pytest.mark.asyncio
async def test_ai_chat_service_no_data(db_session):
    # Setup
    tenant_id = uuid4()
    user = User(
        id=uuid4(),
        tenant_id=tenant_id,
        email="test@example.com",
        role=UserRole.VIEWER,
        created_at=datetime.utcnow()
    )
    
    service = AIChatService(db_session, user)
    
    # Test
    response = await service.generate_response("Hello", [])
    
    # Assert
    assert "don't see any budget data" in response
