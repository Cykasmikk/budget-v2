from typing import List, Optional
import structlog
import os
import json
from pydantic import BaseModel
from src.application.ai.simulator_ai import SimulatorAction, SimulatorAI

logger = structlog.get_logger()

class ScenarioPlan(BaseModel):
    actions: List[SimulatorAction]
    explanation: str

class ScenarioPlanner:
    """
    Agentic Planner that decomposes high-level goals into a sequence of SimulatorActions.
    Example: "Save $500 for vacation" -> [Reduce Dining Out by $200, Reduce Shopping by $300]
    """
    def __init__(self, simulator_ai: SimulatorAI):
        self.simulator = simulator_ai
        # We might reuse the simulator's model or a more powerful one
        self.model = simulator_ai.model 
        
    async def generate_plan(self, user_goal: str) -> Optional[ScenarioPlan]:
        """
        Decomposes the user goal into a list of actions.
        """
        if not self.model:
             return None
             
        prompt = f"""
        You are a financial planning agent.
        Break down the user's goal into a sequence of specific budget adjustments (actions).
        
        User Goal: "{user_goal}"
        
        Output a JSON object with this schema:
        {{
            "actions": [
                {{
                    "action": "reduce" | "increase" | "set",
                    "target": "Category Name",
                    "amount": float,
                    "unit": "percent" | "absolute",
                    "explanation": "Reason for this specific step"
                }}
            ],
            "explanation": "Overall strategy explanation"
        }}
        """
        
        try:
            import google.generativeai as genai
            
            response = await self.model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            
            text = response.text
            if text.startswith("```json"):
                text = text.split("```json")[1].split("```")[0]
                
            data = json.loads(text.strip())
            return ScenarioPlan(**data)
            
        except Exception as e:
            logger.error("plan_generation_failed", error=str(e))
            # Fallback: try using SimulatorAI for single action parsing if decomposition fails
            single_action = await self.simulator.parse_scenario(user_goal)
            if single_action:
                return ScenarioPlan(actions=[single_action], explanation="Single step action parsed.")
            return None
