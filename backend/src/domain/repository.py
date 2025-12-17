from abc import ABC, abstractmethod
from typing import List, Protocol
from src.domain.budget import BudgetEntry
from src.domain.rule import Rule

class BudgetRepository(ABC):
    """
    Abstract interface for budget data persistence.
    """
    
    @abstractmethod
    async def save_bulk(self, entries: List[BudgetEntry]) -> None:
        """
        Saves a list of budget entries to the repository.
        """
        pass
    
    @abstractmethod
    async def get_all(self) -> List[BudgetEntry]:
        """
        Retrieves all budget entries.
        """
        pass

class RuleRepository(Protocol):
    async def add(self, rule: Rule) -> Rule:
        """Adds a new rule."""
        pass
        
    async def get_all(self) -> List[Rule]:
        """Retrieves all rules."""
        pass
        
    async def delete(self, rule_id: int) -> None:
        """Deletes a rule by ID."""
        pass
