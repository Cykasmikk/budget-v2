from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from src.infrastructure.db import get_session
from src.infrastructure.repository import SQLBudgetRepository
from src.domain.repository import BudgetRepository
from sqlalchemy.ext.asyncio import AsyncSession
import pandas as pd
import io

from src.interface.dependencies import get_current_user

router = APIRouter()

async def get_repo(session: AsyncSession = Depends(get_session)) -> BudgetRepository:
    return SQLBudgetRepository(session)

@router.get("/export")
async def export_budget(
    repo: BudgetRepository = Depends(get_repo),
    user: dict = Depends(get_current_user)
):
    """
    Exports budget data as CSV.
    """
    entries = await repo.get_all()
    
    # Create generator
    def iter_csv(rows):
        yield "Date,Category,Amount,Description,Project\n"
        for r in rows:
            yield f'{r.date},{r.category},{float(r.amount)},"{r.description}",{r.project}\n'

    return StreamingResponse(
        iter_csv(entries),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=budget_export.csv"}
    )
    
    return StreamingResponse(
        response,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=budget_export.csv"}
    )
