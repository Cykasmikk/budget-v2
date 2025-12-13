from typing import Dict, Any
from src.domain.repository import BudgetRepository
from src.application.ports import ExcelParser
from src.application.analyze_budget import AnalyzeBudgetUseCase

class UploadBudgetUseCase:
    """
    Use case for uploading and processing a budget Excel file.
    """
    
    def __init__(self, repo: BudgetRepository, parser: ExcelParser, analyzer: AnalyzeBudgetUseCase):
        self.repo = repo
        self.parser = parser
        self.analyzer = analyzer
        
    async def execute(self, file_content: bytes) -> Dict[str, Any]:
        """
        Executes the use case: parse file -> save to repo -> return analysis of THIS file.
        """
        entries, warnings = self.parser.parse(file_content)
        await self.repo.save_bulk(entries)
        
        # Analyze ONLY the new entries
        analysis = await self.analyzer.execute(entries)
        
        # Attach Warnings
        if isinstance(analysis, dict):
            analysis['warnings'] = warnings
            analysis['skipped_count'] = len(warnings)
            
        return analysis
