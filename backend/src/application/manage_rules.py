from typing import List
from src.domain.rule import Rule
from src.domain.repository import RuleRepository

class ManageRulesUseCase:
    def __init__(self, repo: RuleRepository):
        self.repo = repo

    async def add_rule(self, pattern: str, category: str) -> Rule:
        rule = Rule(pattern=pattern, category=category)
        return await self.repo.add(rule)

    async def get_rules(self) -> List[Rule]:
        return await self.repo.get_all()

    async def delete_rule(self, rule_id: int) -> None:
        await self.repo.delete(rule_id)
