import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.infrastructure.repository import SQLBudgetRepository, Base
from src.domain.budget import BudgetEntry
from datetime import date
from decimal import Decimal

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
    
    await engine.dispose()

@pytest.mark.asyncio
async def test_repository_save_and_get(db_session):
    repo = SQLBudgetRepository(db_session)
    
    entries = [
        BudgetEntry(date=date(2025, 1, 1), category="Food", amount=Decimal("10.0"), description="Lunch"),
        BudgetEntry(date=date(2025, 1, 2), category="Transport", amount=Decimal("5.0"), description="Bus")
    ]
    
    await repo.save_bulk(entries)
    
    saved_entries = await repo.get_all()
    assert len(saved_entries) == 2
    assert saved_entries[0].category == "Food"
    assert saved_entries[1].category == "Transport"
