from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List
from pydantic import BaseModel
from src.domain.rule import Rule
from src.application.manage_rules import ManageRulesUseCase
from src.infrastructure.repository import SQLRuleRepository
from src.infrastructure.db import get_session
from sqlalchemy.ext.asyncio import AsyncSession

from src.interface.dependencies import get_current_user
from src.interface.envelope import ResponseEnvelope
from src.application.audit_service import AuditService

router = APIRouter()

class RuleCreate(BaseModel):
    pattern: str
    category: str

async def get_manage_rules_use_case(session: AsyncSession = Depends(get_session)):
    repo = SQLRuleRepository(session)
    audit_service = AuditService(session)
    return ManageRulesUseCase(repo, audit_service)

@router.get("/rules", response_model=ResponseEnvelope[List[Rule]])
async def get_rules(
    use_case: ManageRulesUseCase = Depends(get_manage_rules_use_case),
    user: dict = Depends(get_current_user)
):
    rules = await use_case.get_rules()
    return ResponseEnvelope.success(data=rules)

@router.post("/rules", response_model=ResponseEnvelope[dict])
async def add_rule(
    rule: Rule = Body(...),
    use_case: ManageRulesUseCase = Depends(get_manage_rules_use_case),
    user: dict = Depends(get_current_user)
):
    await use_case.add_rule(rule.pattern, rule.category)
    return ResponseEnvelope.success(data={"status": "ok"})

@router.delete("/rules/{rule_id}", response_model=ResponseEnvelope[dict])
async def delete_rule(
    rule_id: int,
    use_case: ManageRulesUseCase = Depends(get_manage_rules_use_case),
    user: dict = Depends(get_current_user)
):
    await use_case.delete_rule(rule_id)
    return ResponseEnvelope.success(data={"status": "ok"})
