from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse
from src.infrastructure.repository import SQLBudgetRepository
from src.infrastructure.db import get_session
from sqlalchemy.ext.asyncio import AsyncSession
import io
import csv

from src.interface.dependencies import get_current_user

router = APIRouter()

async def get_repo(session: AsyncSession = Depends(get_session)):
    return SQLBudgetRepository(session)

@router.get("/export")
async def export_budget(
    repo: SQLBudgetRepository = Depends(get_repo),
    user: dict = Depends(get_current_user)
):
    entries = await repo.get_all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Category', 'Amount', 'Description', 'Project'])
    
    for entry in entries:
        writer.writerow([entry.date, entry.category, entry.amount, entry.description, entry.project or ''])
        
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=budget_export.csv"}
    )
