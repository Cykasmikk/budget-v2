from fastapi import APIRouter, Depends
from typing import List, Dict
from pydantic import BaseModel
from src.application.simulate_budget import SimulateBudgetUseCase, SimulationAdjustment
from src.infrastructure.repository import SQLBudgetRepository
from src.infrastructure.db import get_session
from sqlalchemy.ext.asyncio import AsyncSession

from src.interface.dependencies import get_current_user
from src.interface.envelope import ResponseEnvelope

router = APIRouter()

class SimulationResponse(BaseModel):
    current_total: float
    simulated_total: float
    savings: float
    breakdown: Dict[str, float]

async def get_simulate_use_case(session: AsyncSession = Depends(get_session)):
    repo = SQLBudgetRepository(session)
    return SimulateBudgetUseCase(repo)

@router.post("/simulate", response_model=ResponseEnvelope[SimulationResponse])
async def simulate_budget(
    adjustments: List[SimulationAdjustment],
    use_case: SimulateBudgetUseCase = Depends(get_simulate_use_case),
    user: dict = Depends(get_current_user)
):
    result = await use_case.execute(adjustments)
    return ResponseEnvelope.success(data=SimulationResponse(**result))
