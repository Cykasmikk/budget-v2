from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.application.query_budget import QueryBudgetUseCase
from src.infrastructure.repository import SQLBudgetRepository
from src.infrastructure.db import get_session
from sqlalchemy.ext.asyncio import AsyncSession

from src.interface.dependencies import get_current_user

router = APIRouter()

class QueryRequest(BaseModel):
    query: str

async def get_query_use_case(session: AsyncSession = Depends(get_session)):
    repo = SQLBudgetRepository(session)
    return QueryBudgetUseCase(repo)

@router.post("/query")
async def query_budget(
    request: QueryRequest,
    use_case: QueryBudgetUseCase = Depends(get_query_use_case),
    user: dict = Depends(get_current_user)
):
    return await use_case.execute(request.query)
