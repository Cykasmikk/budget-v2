from abc import ABC, abstractmethod
from typing import List, AsyncIterator, Dict
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

class LLMProvider(ABC):
    """
    Abstract interface for Large Language Model providers.
    """

    @abstractmethod
    async def generate_response(self, prompt: str, context: str, conversation_history: List[Dict[str, str]] = []) -> str:
        """
        Generates a response from the LLM based on the prompt and context.
        """
        pass

    @abstractmethod
    async def generate_response_stream(self, prompt: str, context: str, conversation_history: List[Dict[str, str]] = []) -> AsyncIterator[str]:
        """
        Generates a streaming response from the LLM, yielding tokens as they are generated.
        """
        pass
