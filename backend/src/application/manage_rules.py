from typing import List
from src.domain.repository import RuleRepository
from src.domain.rule import Rule

class ManageRulesUseCase:
    """
    Use case for managing categorization rules.
    Allows creating, listing, and deleting rules.
    """
    def __init__(self, repo: RuleRepository):
        self.repo = repo

    async def get_rules(self) -> List[Rule]:
        """
        Retrieves all rules for the current tenant.

        Returns:
            List[Rule]: A list of rule entities.
        """
        return await self.repo.get_all()

    async def add_rule(self, pattern: str, category: str) -> Rule:
        """
        Creates a new categorization rule.

        Args:
            pattern (str): The regex pattern to match against transaction descriptions.
            category (str): The category to assign if the pattern matches.

        Returns:
            Rule: The created rule entity.
        """
        rule = Rule(pattern=pattern, category=category)
        return await self.repo.add(rule)

    async def delete_rule(self, rule_id: int):
        """
        Deletes a rule by its ID.

        Args:
            rule_id (int): The unique identifier of the rule to delete.
        """
        await self.repo.delete(rule_id)
