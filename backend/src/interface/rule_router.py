from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from src.application.manage_rules import ManageRulesUseCase
from src.infrastructure.repository import SQLRuleRepository
from src.infrastructure.db import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.rule import Rule
from src.interface.dependencies import get_current_user

router = APIRouter()

class RuleCreate(BaseModel):
    pattern: str
    category: str

async def get_manage_rules_use_case(session: AsyncSession = Depends(get_session)):
    repo = SQLRuleRepository(session)
    return ManageRulesUseCase(repo)

@router.get("/rules", response_model=List[Rule])
async def get_rules(
    use_case: ManageRulesUseCase = Depends(get_manage_rules_use_case),
    user: dict = Depends(get_current_user)
):
    return await use_case.get_rules()

@router.post("/rules", response_model=Rule)
async def add_rule(
    rule: RuleCreate,
    use_case: ManageRulesUseCase = Depends(get_manage_rules_use_case),
    user: dict = Depends(get_current_user)
):
    return await use_case.add_rule(rule.pattern, rule.category)

@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: int,
    use_case: ManageRulesUseCase = Depends(get_manage_rules_use_case),
    user: dict = Depends(get_current_user)
):
    await use_case.delete_rule(rule_id)
    return {"status": "ok"}
