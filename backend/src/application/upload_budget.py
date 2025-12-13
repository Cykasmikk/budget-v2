from src.domain.repository import BudgetRepository
from src.infrastructure.excel_parser import ExcelParser
from src.application.analyze_budget import AnalyzeBudgetUseCase
from src.domain.analysis_models import BudgetAnalysisResult

class UploadBudgetUseCase:
    def __init__(self, repo: BudgetRepository, parser: ExcelParser, analyzer: AnalyzeBudgetUseCase):
        self.repo = repo
        self.parser = parser
        self.analyzer = analyzer

    async def execute(self, file_content: bytes) -> BudgetAnalysisResult:
        entries, warnings = self.parser.parse(file_content)
        await self.repo.add_all(entries)
        
        # Return analysis of the newly updated state
        result = await self.analyzer.execute()
        
        # Attach upload warnings
        result.warnings = warnings
        result.skipped_count = len(warnings)
        
        return result
