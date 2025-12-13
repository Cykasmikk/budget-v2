import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://budget_user:budget_password@postgres/budget_db")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# init_db is deprecated in favor of Alembic migrations

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
