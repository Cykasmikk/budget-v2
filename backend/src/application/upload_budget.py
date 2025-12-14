from typing import Optional
from src.domain.repository import BudgetRepository
from src.infrastructure.excel_parser import ExcelParser
from src.application.analyze_budget import AnalyzeBudgetUseCase
from src.domain.analysis_models import BudgetAnalysisResult
from src.application.audit_service import AuditService

class UploadBudgetUseCase:
    def __init__(
        self, 
        repo: BudgetRepository, 
        parser: ExcelParser, 
        analyzer: AnalyzeBudgetUseCase,
        audit_service: Optional[AuditService] = None
    ):
        self.repo = repo
        self.parser = parser
        self.analyzer = analyzer
        self.audit_service = audit_service

    async def execute(self, file_content: bytes) -> BudgetAnalysisResult:
        entries, warnings = self.parser.parse(file_content)
        await self.repo.save_bulk(entries)
        
        # Log Audit
        if self.audit_service and entries:
            await self.audit_service.log_action(
                action="UPLOAD",
                resource="BUDGET_FILE",
                details={
                    "entries_count": len(entries),
                    "warnings_count": len(warnings),
                    "first_date": str(entries[0].date) if entries else None,
                    "last_date": str(entries[-1].date) if entries else None
                }
            )
        
        # Return analysis of the newly updated state
        result = await self.analyzer.execute()
        
        # Attach upload warnings
        result.warnings = warnings
        result.skipped_count = len(warnings)
        
        return result
