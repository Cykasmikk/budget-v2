from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from src.application.upload_budget import UploadBudgetUseCase
from src.application.analyze_budget import AnalyzeBudgetUseCase
from src.infrastructure.repository import SQLBudgetRepository
from src.infrastructure.excel_parser import PandasExcelParser
from src.infrastructure.db import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from src.interface.dependencies import get_current_user

router = APIRouter()

async def get_upload_use_case(session: AsyncSession = Depends(get_session)):
    repo = SQLBudgetRepository(session)
    parser = PandasExcelParser()
    analyzer = AnalyzeBudgetUseCase(repo)
    return UploadBudgetUseCase(repo, parser, analyzer)

async def get_analyze_use_case(session: AsyncSession = Depends(get_session)):
    repo = SQLBudgetRepository(session)
    return AnalyzeBudgetUseCase(repo)

@router.post("/upload")
async def upload_budget(
    files: List[UploadFile] = File(...),
    use_case: UploadBudgetUseCase = Depends(get_upload_use_case),
    user: dict = Depends(get_current_user)
):
    results = []
    try:
        for file in files:
            content = await file.read()
            # We process each file sequentially. 
            # Ideally, we should update the use case to accept a list of contents to do it in one transaction,
            # but calling execute multiple times works because our repository handles de-duplication.
            result = await use_case.execute(content)
            results.append(result)
            
        # Return the last result (which contains the full analysis) or merge them.
        # Since execute() returns the full analysis of the DB state, the last one is the most up-to-date.
        return results[-1] if results else {}
    except Exception as e:
        import traceback
        traceback.print_exc() # Print to stdout/stderr for docker logs
        
        # Also use structlog if available (which it should be)
        import structlog
        logger = structlog.get_logger()
        logger.exception("upload_failed_exception", error=str(e))
        
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/analysis", response_model=Dict[str, Any])
async def analyze_budget(
    use_case: AnalyzeBudgetUseCase = Depends(get_analyze_use_case),
    user: dict = Depends(get_current_user)
):
    return await use_case.execute()
