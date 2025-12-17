from typing import List, Optional
from src.domain.repository import RuleRepository
from src.domain.rule import Rule
from src.application.audit_service import AuditService

class ManageRulesUseCase:
    """
    Use case for managing categorization rules.
    Allows creating, listing, and deleting rules.
    """
    def __init__(self, repo: RuleRepository, audit_service: Optional[AuditService] = None):
        self.repo = repo
        self.audit_service = audit_service

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
        created_rule = await self.repo.add(rule)
        
        if self.audit_service:
            await self.audit_service.log_action(
                action="CREATE",
                resource="RULE",
                resource_id=str(created_rule.id),
                details={"pattern": pattern, "category": category}
            )
            
        return created_rule

    async def delete_rule(self, rule_id: int):
        """
        Deletes a rule by its ID.

        Args:
            rule_id (int): The unique identifier of the rule to delete.
        """
        await self.repo.delete(rule_id)
        
        if self.audit_service:
            await self.audit_service.log_action(
                action="DELETE",
                resource="RULE",
                resource_id=str(rule_id)
            )

