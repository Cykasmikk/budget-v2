from abc import ABC, abstractmethod
from typing import List
from src.domain.budget import BudgetEntry

class ExcelParser(ABC):
    """
    Abstract interface for parsing Excel files.
    """
    
    @abstractmethod
    def parse(self, file_content: bytes) -> tuple[List[BudgetEntry], List[str]]:
        """
        Parses the binary content of an Excel file into BudgetEntry objects.
        Returns a tuple of (valid_entries, warnings).
        """
        pass
