from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from src.application.upload_budget import UploadBudgetUseCase
from src.application.analyze_budget import AnalyzeBudgetUseCase
from src.infrastructure.repository import SQLBudgetRepository
from src.infrastructure.excel_parser import PandasExcelParser
from src.infrastructure.db import get_session
from src.infrastructure.models import TenantModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
from src.interface.dependencies import get_current_user, get_db
from src.interface.envelope import ResponseEnvelope
from src.domain.analysis_models import BudgetAnalysisResult
from src.application.audit_service import AuditService
from src.domain.user import User
import structlog

router = APIRouter()
logger = structlog.get_logger()

async def get_upload_use_case(session: AsyncSession = Depends(get_session)):
    repo = SQLBudgetRepository(session)
    parser = PandasExcelParser()
    analyzer = AnalyzeBudgetUseCase(repo)
    audit_service = AuditService(session)
    return UploadBudgetUseCase(repo, parser, analyzer, audit_service)

async def get_analyze_use_case(session: AsyncSession = Depends(get_session)):
    repo = SQLBudgetRepository(session)
    return AnalyzeBudgetUseCase(repo)

async def get_tenant_settings(db: AsyncSession, tenant_id: str) -> Dict[str, Any]:
    stmt = select(TenantModel).where(TenantModel.id == tenant_id)
    result = await db.execute(stmt)
    tenant = result.scalar_one_or_none()
    return tenant.settings if tenant else {}

@router.post("/upload", response_model=ResponseEnvelope[BudgetAnalysisResult])
async def upload_budget(
    files: List[UploadFile] = File(...),
    use_case: UploadBudgetUseCase = Depends(get_upload_use_case),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
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
        data = results[-1] if results else BudgetAnalysisResult()
        return ResponseEnvelope.success(data=data)
    except Exception as e:
        logger.exception("upload_failed_exception", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/analysis", response_model=ResponseEnvelope[BudgetAnalysisResult])
async def analyze_budget(
    use_case: AnalyzeBudgetUseCase = Depends(get_analyze_use_case),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    settings = await get_tenant_settings(db, user.tenant_id)
    result = await use_case.execute(settings=settings)
    return ResponseEnvelope.success(data=result)
