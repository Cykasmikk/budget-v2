from fastapi import APIRouter, Depends
from typing import List
from src.application.simulate_budget import SimulateBudgetUseCase, SimulationAdjustment
from src.infrastructure.repository import SQLBudgetRepository
from src.infrastructure.db import get_session
from sqlalchemy.ext.asyncio import AsyncSession

from src.interface.dependencies import get_current_user

router = APIRouter()

async def get_simulate_use_case(session: AsyncSession = Depends(get_session)):
    repo = SQLBudgetRepository(session)
    return SimulateBudgetUseCase(repo)

@router.post("/simulate")
async def simulate_budget(
    adjustments: List[SimulationAdjustment],
    use_case: SimulateBudgetUseCase = Depends(get_simulate_use_case),
    user: dict = Depends(get_current_user)
):
    return await use_case.execute(adjustments)
